from __future__ import annotations

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from tavily import TavilyClient

# 加载 .env 文件中的环境变量
load_dotenv()


# 定义全局状态
# 图中的每一个节点函数都会接收它，并返回自己要更新的字段
# 是智能体在整个执行过程中的公共上下文对象
class SearchState(TypedDict):
    # messages用来保存对话历史
    # add_messages是LangGraph提供的聚合器，表示每个节点返回的新消息
    # 会自动追加到已有消息列表中，而不是直接覆盖
    messages: Annotated[list[BaseMessage], add_messages]

    # user_query：经过大模型理解、提炼后的用户真实需求
    # 它不一定等于用户原始输入，而是更适合后续回答节点使用的“问题摘要”
    user_query: str

    # search_query：为了调用Tavily搜索而优化后的关键词
    # 通常比用户原始问题更短、更精确、更接近搜索引擎偏好的表达方式
    search_query: str

    # search_results：Tavily返回并经过整理后的搜索结果文本
    # 后续的回答节点会基于这里的内容生成最终答案
    search_results: str

    # final_answer：最终给用户展示的答案
    final_answer: str

    # step：记录当前工作流执行到哪一步
    step: str


# 统一封装大模型初始化
def load_model() -> ChatOpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("未找到 DASHSCOPE_API_KEY 或 LLM_API_KEY 环境变量")

    return ChatOpenAI(
        api_key=api_key,
        # DashScope提供OpenAI兼容接口，因此可以直接用ChatOpenAI
        base_url=os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("LLM_MODEL_ID", "qwen3.7-plus"),
        temperature=0.7,
        streaming=True,
    )


# 统一封装Tavily搜索客户端初始化逻辑（没去注册，这个功能用不了，不能联网搜索实时数据）
def load_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("未找到 TAVILY_API_KEY 环境变量")

    os.environ["TAVILY_API_KEY"] = api_key
    return TavilyClient(api_key=api_key)


# 初始化模型和搜索客户端
llm = load_model()
tavily_client = load_tavily_client()    # 没注册，用不了


# 从消息列表中提取“最后一条用户消息”
def _extract_latest_user_message(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content if isinstance(message.content, str) else str(message.content)
    raise ValueError("未找到用户消息，请至少传入一条 HumanMessage。")


# 解析理解节点的大模型输出
# 我们要求模型按“理解：...”和“搜索词：...”这种格式返回
# 这里负责把这两部分拆出来
# 如果模型没有严格按格式输出，就退回使用原始问题，保证流程不会中断
def _parse_understanding_response(text: str, fallback_query: str) -> tuple[str, str]:
    understood_query = fallback_query
    search_query = fallback_query

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("理解："):
            understood_query = stripped.split("理解：", 1)[1].strip() or fallback_query
        elif stripped.startswith("搜索词："):
            search_query = stripped.split("搜索词：", 1)[1].strip() or fallback_query

    return understood_query, search_query


# 把Tavily返回的原始JSON结构整理成更适合后续LLM阅读的纯文本
# 这样回答节点收到的上下文会更规整，也更容易生成稳定答案
def _format_search_results(response: dict) -> str:
    lines: list[str] = []

    # Tavily可能会直接返回一个answer字段
    # 这是Tavily自己给出的简要总结，适合作为搜索结果的开头
    answer = response.get("answer")
    if answer:
        lines.append(f"Tavily 摘要：{answer}")
        lines.append("")

    results = response.get("results", [])
    if not results:
        lines.append("没有检索到可用结果。")
        return "\n".join(lines)

    # 逐条整理搜索结果，保留标题、链接、摘要内容
    # 为了避免上下文过长，这里对content做了截断
    for index, item in enumerate(results, start=1):
        title = item.get("title", "无标题")
        url = item.get("url", "无链接")
        content = (item.get("content") or "").strip()
        if len(content) > 500:
            content = f"{content[:500]}..."

        lines.extend(
            [
                f"结果 {index}：{title}",
                f"链接：{url}",
                f"内容：{content or '无摘要'}",
                "",
            ]
        )

    return "\n".join(lines).strip()


# 节点1：理解用户问题，并生成更适合搜索引擎的搜索词（这是整个流程的第一步，负责把“自然语言问题”转成“可检索任务”）
def understand_query_node(state: SearchState) -> dict:
    """步骤1：理解用户查询并生成搜索关键词"""
    user_message = _extract_latest_user_message(state["messages"])

    understand_prompt = f"""分析用户的查询：\"{user_message}\"
请完成两个任务：
1. 简洁总结用户想要了解什么
2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

格式：
理解：[用户需求总结]
搜索词：[最佳搜索关键词]"""

    # 这里调用大模型，不是直接回答用户，而是先做“任务理解”和“查询改写”
    response = llm.invoke([SystemMessage(content=understand_prompt)])
    response_text = response.content if isinstance(response.content, str) else str(response.content)
    understood_query, search_query = _parse_understanding_response(response_text, user_message)

    return {
        "user_query": understood_query,
        "search_query": search_query,
        "step": "understood",
        # 往messages里追加一条AIMessage，表示当前节点的中间输出
        "messages": [AIMessage(content=f"我将为您搜索：{search_query}")],
    }


# 节点2：调用Tavily执行真实联网搜索
# 这是本项目能否获取实时数据的关键节点（没注册，用不了哈哈哈）
def tavily_search_node(state: SearchState) -> dict:
    """步骤2：使用Tavily API进行真实搜索"""
    search_query = state["search_query"]

    try:
        print(f"正在搜索: {search_query}")
        response = tavily_client.search(
            query=search_query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
        search_results = _format_search_results(response)

        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [AIMessage(content="搜索完成！正在整理答案...")],
        }
    except Exception as error:
        # 如果Tavily搜索失败，不让整个图崩掉
        # 而是把错误信息写进状态，并把step标记为search_failed
        # 这样后面的回答节点就可以走“降级兜底”分支
        return {
            "search_results": f"搜索失败：{error}",
            "step": "search_failed",
            "messages": [AIMessage(content="搜索遇到问题，正在尝试基于模型知识回答...")],
        }


# 节点3：根据前一步搜索是否成功，生成最终答案
# 如果搜索成功：基于实时搜索结果作答
# 如果搜索失败：退化为基于模型已有知识回答
def generate_answer_node(state: SearchState) -> dict:
    """步骤3：基于搜索结果生成最终答案"""
    if state["step"] == "search_failed":
        fallback_prompt = f"""搜索 API 暂时不可用，请基于你的已有知识回答用户问题。

用户问题：{state['user_query']}
要求：
1. 直接回答问题
2. 明确说明这是基于模型知识的回答，可能不是最新信息
3. 尽量结构清晰、内容准确"""
        response = llm.invoke([SystemMessage(content=fallback_prompt)])
    else:
        answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案。

用户问题：{state['user_query']}

搜索结果：
{state['search_results']}

要求：
1. 优先依据搜索结果回答
2. 用清晰的中文分点说明
3. 如果信息存在不确定性，要明确指出
4. 不要编造搜索结果中没有支持的事实"""
        response = llm.invoke([SystemMessage(content=answer_prompt)])

    answer = response.content if isinstance(response.content, str) else str(response.content)
    return {
        "final_answer": answer,
        "step": "completed",
        "messages": [AIMessage(content=answer)],
    }


# 创建并编译LangGraph图。
# 这里定义了完整的节点和边，也就是整个工作流执行顺序：
# START->understand->search->answer->END
def create_search_assistant():
    workflow = StateGraph(SearchState)

    # 注册节点，每个节点本质上都是一个函数
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    # 定义执行路径
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    # InMemorySaver用来保存图运行时的检查点状态
    # 当前项目里它主要用于演示和基础状态持久化，保存在内存中，程序结束后会消失
    memory = InMemorySaver()
    return workflow.compile(checkpointer=memory)


# 对外暴露的统一运行入口
# main.py只需要调用这个函数，并传入用户问题即可
def run_search_app(user_input: str, thread_id: str = "default") -> SearchState:
    app = create_search_assistant()

    # 初始化图的起始状态
    # 一开始只有用户消息，其余字段都为空，等待后续节点逐步填充
    initial_state: SearchState = {
        "messages": [HumanMessage(content=user_input)],
        "user_query": "",
        "search_query": "",
        "search_results": "",
        "final_answer": "",
        "step": "started",
    }

    # thread_id用于区分不同会话线程
    # 当前CLI项目默认固定为default，后续如果做多轮对话或Web应用，
    # 可以按用户或会话动态设置。
    return app.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
