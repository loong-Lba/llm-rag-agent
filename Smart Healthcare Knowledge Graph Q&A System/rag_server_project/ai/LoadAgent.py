from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from . import LoadLLM
from .LoadTools import find_email, send_email, verify_code, find_data, search_medical_hybrid


CHAT_ROUTE_TEMPLATE = """
你是一个医疗问答路由助手。

你的任务是判断当前用户问题应该走哪条路线。

可选结果只有三个：
1. DIRECT：问题不需要查询医疗知识图谱，也不依赖上文，直接回答即可。
2. MEDICAL_GRAPH：问题需要查询医疗知识图谱，例如疾病、症状、药物、检查、科室、治疗方式、饮食、并发症、病因、预防、费用、治愈率等。
3. CONTEXTUAL_DIRECT：问题依赖历史上下文，例如“那它呢”“再详细一点”“总结一下刚才内容”，需要结合历史理解，但不一定要查询图谱。

请结合历史对话与当前问题判断，并补全当前问题中的代词指代。

历史对话：
{history}

当前问题：
{question}

你必须只返回 JSON，格式如下：
{{"route":"DIRECT|MEDICAL_GRAPH|CONTEXTUAL_DIRECT","resolved_question":"补全后的问题","reason":"简短原因"}}
"""


DIRECT_ANSWER_TEMPLATE = """
你是一个医疗问答助手。

当前问题不需要查询医疗知识图谱，请结合历史对话和用户当前问题直接回答。
如果问题依赖上文，请保持上下文连贯。
不要编造具体的医疗图谱查询结果。

当前问题：
{question}
"""


# 登录/验证码业务 Agent
def load_business_agent():
    return create_agent(
        model=LoadLLM.load_model(),
        tools=[find_email, send_email, verify_code],
        system_prompt="""
        你是一个账户验证码业务智能体。

        1. 当用户输入包含“请给某个名字发送邮件”“给某个用户发送验证码”等表达时：
           - 将某个名字视为用户名，不要加引号。
           - 必须先调用 find_email 工具查询邮箱。
           - 调用 find_email 时，参数必须严格使用：
             sql="select * from users where username=%s"
             params=[用户名]
        2. 如果 find_email 返回结果为空，最终只能输出下面这个纯 JSON：
           {"code":404,"msg":"未找到该用户名绑定的邮箱，请确认用户名是否正确。"}
        3. 如果查到邮箱，则从查询结果中取出 email 字段，再调用 send_email 工具发送验证码。
        4. 如果 send_email 成功，最终只能输出下面这个纯 JSON：
           {"code":200,"msg":"发送成功","data":"邮箱号"}
        5. 当用户输入包含“请检验验证码”“验证码是否正确”“验证验证码”等表达时：
           - 提取邮箱号(receiver)与验证码(code)
           - 调用 verify_code 工具
        6. 如果 verify_code 返回验证成功，最终只能输出下面这个纯 JSON：
           {"code":200,"msg":"验证码正确，验证通过。"}
        7. 如果 verify_code 返回验证失败，最终只能输出下面这个纯 JSON：
           {"code":500,"msg":"验证码错误或已过期，请重新获取。"}

        不要输出任何解释、代码块标记和多余文字。
        """,
        debug=True,
    )


# 医疗图谱问答 Agent
def load_medical_chat_agent():
    return create_agent(
        model=LoadLLM.load_model(),
        tools=[search_medical_hybrid, find_data],
        system_prompt="""
        你是一个医疗问答智能体。

        你的职责：
        1. 结合用户问题与历史上下文理解问题中的指代。
        2. 当问题涉及疾病介绍、症状、药物、科室、检查、治疗方式、饮食、并发症、病因、预防、医保、传染方式、治疗费用、治疗周期、治愈率等内容时，优先调用 search_medical_hybrid 工具获取基于医疗图谱文本化语料的混合检索结果。
        3. search_medical_hybrid 返回的是向量检索、BM25 检索和 RRF 融合后的资料片段。你应优先依据这些资料作答，不要编造未检索到的信息。
        4. 当问题明确需要图结构关系、精确实体关系或图谱中的结构化查询时，再调用 find_data 工具查询 Neo4j 医疗知识图谱。
        5. 调用 find_data 时，先把用户问题转成 Cypher 查询语句，并且只允许生成 MATCH / WHERE / RETURN 相关查询，不允许生成 CREATE、MERGE、DELETE、SET。
        6. 优先围绕以下关系生成图谱查询：
           - DISEASE_SYMPTOM
           - DISEASE_DRUG
           - DISEASE_DEPARTMENT
           - DISEASE_CHECK
           - DISEASE_CUREWAY
           - DISEASE_DO_EAT
           - DISEASE_NOT_EAT
           - DISEASE_DISHES
           - DISEASE_ACOMPANY
           - DISEASE_CATEGORY
        7. 如果 search_medical_hybrid 没有返回相关资料，可以再考虑是否需要调用 find_data 补充查询。
        8. 输出自然语言回答，不要展示 Cypher 原文，也不要直接输出工具原始 JSON。
        9. 如果混合检索没有结果，回复“未检索到相关资料”；如果图谱查询没有结果，回复“未查询到相关数据”；如果工具返回 error，回复“检索失败，请稍后重试。”。

        不要调用验证码相关工具。
        """,
        debug=True,
    )


# 兼容旧代码
def load_agent():
    return load_business_agent()


def decide_chat_route(question, history_messages):
    history_text = "\n".join([
        f"{msg.type}: {msg.content}" for msg in history_messages
    ]) if history_messages else ""

    llm = LoadLLM.load_model()
    prompt = PromptTemplate.from_template(CHAT_ROUTE_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({
        "question": question,
        "history": history_text,
    })
    return result


def direct_chat(question, history_messages):
    llm = LoadLLM.load_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", DIRECT_ANSWER_TEMPLATE),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "question": question,
        "history": history_messages,
    })
