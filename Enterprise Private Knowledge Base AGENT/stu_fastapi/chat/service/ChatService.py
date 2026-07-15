import os

import jieba
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from FlagEmbedding import FlagReranker
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from ai.models import LoadALYModel
from chat.dao import ChatDao
from common import ResponseUtil
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from chat.dao import ChatDao, HistoryDao
from operator import itemgetter
from langchain_core.messages import HumanMessage, AIMessage

# 提示词：如果问题与数据库有关则返回yes，不相关则返回no，目的是达到：如果问题与数据库相关则进行检索，如果不想管则直接由大模型回答
RELEVANCE_JUDGE_TEMPLATE = """
你是一个问题路由助手。

你的任务是判断：用户的问题是否需要依赖“MotoGP 与摩托车 675SR 知识库”来回答。

【如果满足以下情况，返回 YES】
1. 问题和 MotoGP、675SR、摩托车、赛车、车型参数、性能配置、品牌、赛事、车手、赛道、技术特点、驾驶体验等内容相关
2. 问题更适合依据 MotoGP 与 675SR 知识库中的资料来回答
3. 用户是在询问车辆信息、赛事信息、技术参数、配置差异、产品定位、性能表现、骑行体验等内容

【如果满足以下情况，返回 NO】
1. 问题是日常聊天、常识问答、写作、翻译、编程、数学、生活建议等，与 MotoGP 和 675SR 知识库无关
2. 问题不需要依赖 MotoGP 和 675SR 知识库即可直接回答
3. 问题明显不是 MotoGP、675SR 或摩托车相关问题

【用户问题】
{question}

你只能返回一个单词：
YES 或 NO
"""

# 提示词：不检索直接回答
DIRECT_ANSWER_TEMPLATE = """
你是一个智能问答助手。

用户当前的问题与 MotoGP 和摩托车 675SR 知识库无关，因此不需要参考知识库内容。
请你结合历史对话，直接根据你的自身知识自然回答用户问题。

如果历史对话中有上下文，请保持上下文连贯。

【用户问题】
{question}

请直接输出最终答案。
"""

# ==================== 路径配置 ====================
path_base = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# 向量化模型路径（保留旧版路径，但改用新版风格）
embedding_model_path = os.path.abspath(os.path.join(path_base, 'models', 'embedding_model'))
# 重排序模型路径
reranker_model_path = os.path.abspath(os.path.join(path_base, 'models', 'bge-reranker-large_v1'))
# 向量数据库路径
vector_db_path = os.path.abspath(os.path.join(path_base, 'vectors'))
# 向量数据库集合的名字
vector_db_name = 'motogp_675sr_house'

# ==================== 全局嵌入模型（单例，避免重复加载） ====================
embedding_model = HuggingFaceEmbeddings(
    model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    cache_folder=embedding_model_path,
    model_kwargs={'device': 'cpu'}
)

#===========判断：如果问题与数据库相关则检索后回答，无关则大模型直接回答=============
# 定义函数：判断是否需要检索
def need_retrieval(question):
    llm = LoadALYModel.load_model()
    # 让模型判断当前问题是否需要依赖MotoGP/675sr检索
    prompt = PromptTemplate.from_template(RELEVANCE_JUDGE_TEMPLATE)
    chain = prompt | llm | StrOutputParser()    # 提示词->大模型->字符串解析器，最终输出会被解析成普通字符串

    # 传入 question 后，模型理论上只会返回 YES 或 NO
    # strip()：去掉首尾空白字符
    # upper()：统一转成大写，避免 yes / Yes / YES 这种格式差异影响判断
    result = chain.invoke({"question": question}).strip().upper()
    print(f"\n问题是否需要检索知识库：{result}")

    return result == "YES"

# 定义函数： 与数据库无关，直接回答
def direct_chat_stream(question, history_messages):
    llm = LoadALYModel.load_model()

    prompt = ChatPromptTemplate.from_messages([
        ("system", DIRECT_ANSWER_TEMPLATE),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    direct_chain = prompt | llm | StrOutputParser()

    for chunk in direct_chain.stream({
        "question": question,
        "history": history_messages,
    }):
        if chunk:
            yield chunk

# ==================== 非流式聊天 ====================
def chat_no_stream(question):
    llm = LoadALYModel.load_model()
    response = llm.invoke(question)
    if response.content:
        return ResponseUtil.response_json(200, "success", response.content)
    return ResponseUtil.response_json(500, "fail", "没有回答")

#===================历史记录加载=================
# 定义函数：加载历史
def load_history_messages(session_id):
    history_data = HistoryDao.find_history_for_context(int(session_id))

    messages = []
    for item in history_data:
        history_question = (item.get("question") or "").strip()
        history_answer = (item.get("answer") or "").strip()

        if history_question:
            messages.append(HumanMessage(content=history_question))
        if history_answer:
            messages.append(AIMessage(content=history_answer))

    return messages


# 中文停用词表（常见停用词，避免无意义词干扰BM25排序）
STOP_WORDS = set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
    "着", "没有", "看", "好", "自己", "这", "那", "他", "她", "它", "们",
    "这个", "那个", "什么", "哪", "怎么", "吗", "呢", "吧", "啊", "哦",
    "还", "被", "把", "让", "从", "对", "与", "但", "而", "或", "所",
    "为", "以", "及", "可", "可以", "能", "能够", "应该", "需要", "已经",
    "虽然", "如果", "因为", "所以", "只是", "还是", "不过", "然后",
    "之", "其", "中", "等", "等等", "即", "使", "向", "将", "按", "当",
    "于", "由", "比", "除了", "关于", "以及", "并且", "此外", "另外",
    "过", "着", "来", "去", "做", "作", "像", "如", "如同", "由于",
])


# 封装一个分词函数
def tokenize(text):
    return [word for word in jieba.cut(text) if word.strip() and word not in STOP_WORDS and len(word.strip()) > 1]

# 获取BM25检索的文档信息和对象
def get_bm25_retrieval(db):
    # 获取向量数据库中的所有数据
    docs = db.get()
    # 获取ids和documents
    ids = docs['ids']
    documents = docs['documents']

    tokenized_corpus = [tokenize(text) for text in documents]
    # 包装documents
    docs = [Document(page_content=item, id=ids[index]) for index,item in enumerate(documents)]
    # 创建BM25对象
    bm25 = BM25Okapi(tokenized_corpus)
    return docs, bm25

# BM25检索
def bm25_search(bm25, bm25_docs, question, tok_k=10):
    # 获取BM25分数
    bm25_scores = bm25.get_scores(tokenize(question))
    # 分数由高到低排序
    scores_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:tok_k]
    # 基于分数的索引值把对应的文档取出来
    return [bm25_docs[item] for item in scores_indices]

# rrf融合
def rrf_result(vector_result, bm25_result, tok_k=10):
    # 存文档
    docs_dict = {}
    # 存分数
    scores_dict = {}
    # 先计算向量检索结果，存入字典，key为id，value为rrf单面值
    for index, doc in enumerate(vector_result):
        # 获取文档的id作为字典的key，唯一性
        id = doc.id
        # 存入字典
        docs_dict[id] = doc
        scores_dict[id] = scores_dict.get(id, 0) + 1.0 / (60 + index + 1)
    # 再计算BM25结果，存入同一个字典，如果key相同就相加，否则单独存入
    for index, doc in enumerate(bm25_result):
        # 获取文档的id作为字典的key，唯一性
        id = doc.id
        # 存入字典
        docs_dict[id] = doc
        scores_dict[id] = scores_dict.get(id, 0) + 1.0 / (60 + index + 1)
    # 从高到低排序 --- 结果只有id
    scores_result = sorted(scores_dict, key=scores_dict.get, reverse=True)
    # 返回结果
    return [docs_dict[id] for id in scores_result]


#  打印检索到的文档内容
def retrieved_docs(docs, title="检索结果"):
    """打印检索到的文档内容，然后原样返回docs供下游使用"""
    print(f'标题：{title}')
    print(f"\n检索到 {len(docs)} 个文档：")
    for i, doc in enumerate(docs, 1):
        print(f"\n【文档 {i}】")
        print(f"  内容: {doc.page_content[:500]}{'...' if len(doc.page_content) > 500 else ''}")
        print("-" * 60)
    return docs
# ==================== 流式聊天（重构后） ====================
def chat_stream(question, history_id):
    history_messages = load_history_messages(history_id)
    #判断：是否需要检索
    if not need_retrieval(question):    # 不需要
        print("\n当前问题与MotoGP/675sr无关，跳过检索，直接调用大模型回答")
        for chunk in direct_chat_stream(question, history_messages):
            if chunk:
                yield chunk
        return
    #需要
    print("\n当前问题与MotoGP/675sr相关，进入 RAG 检索流程")

    #如果需要检索
    #  获取检索对象
    db = Chroma(
        persist_directory=vector_db_path,
        collection_name=vector_db_name,
        embedding_function=embedding_model,
    )
    print('成功获取检索对象')

    # 向量检索器
    retriever = db.as_retriever(search_kwargs={"k": 10})
    # BM25检索器
    bm25_docs, bm25 = get_bm25_retrieval(db)
    # 融合检索的函数
    def merge_retrieval(question):
        #向量检索
        vector_result = retriever.invoke(question)
        retrieved_docs(vector_result, '向量检索结果:')
        #BM25检索
        bm25_result = bm25_search(bm25, bm25_docs, question, 10)
        retrieved_docs(bm25_result, 'BM25检索结果：')
        #rrf融合
        rrf_docs = rrf_result(vector_result, bm25_result, 10)
        retrieved_docs(rrf_docs, "RRF融合结果：")
        #返回结果
        return rrf_docs


    # 大模型
    llm = LoadALYModel.load_model()

    # 提示词模板（分类处理，更智能）
    template = """
    你是一个 MotoGP 与摩托车 675SR 领域的问答助手。

    请优先结合提供的上下文内容回答用户问题。

    【回答规则】
    1. 回答必须基于提供的上下文内容
    2. 如果上下文中可以找到答案，请直接结合上下文作答
    3. 如果上下文中没有提及相关内容，请明确回复：
       “资料中未提及相关内容”

    【上下文】
    {context}

    【用户问题】
    {question}

    请直接输出最终答案。
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    # 重排序模型
    reranker_model = FlagReranker(
        model_name_or_path="BAAI/bge-reranker-large",
        cache_dir=reranker_model_path,
        use_fp16=True
    )

    # 重排序函数
    def reranker(inputs):
        """
        自定义重排序函数
        输入: {"context": List[Document], "question": str}
        输出: {"context": str, "question": str} (直接适配 PromptTemplate)
        """
        docs = inputs["context"]
        question = inputs["question"]
        history = inputs["history"]
        print(f"\n 开始进行重排序... (候选文档数: {len(docs)})")

        # 空值检查（关键修复）
        if not docs:
            print("未检索到任何文档，跳过重排序")
            return {"context": "", "question": question, "history": history}

        # 1. 构造 query-document 对并计算相关性分数
        pairs = [[question, doc.page_content] for doc in docs]
        scores = reranker_model.compute_score(pairs)

        # 2. 将分数注入 metadata 并按分数降序排序
        for doc, score in zip(docs, scores):
            doc.metadata["relevance_score"] = round(float(score), 4)
        sorted_docs = sorted(docs, key=lambda d: d.metadata["relevance_score"], reverse=True)

        # 3. 截取 Top-3 高相关文档
        top_n = 3
        final_docs = sorted_docs[:top_n]

        # 4. 打印重排序后的结果
        print(f" 重排序完成，保留 Top-{top_n} 文档：")
        for i, doc in enumerate(final_docs, 1):
            score = doc.metadata.get("relevance_score", "N/A")
            print(f"\n【文档 {i}】(相关度: {score})")
            print(f"  内容: {doc.page_content[:500]}{'...' if len(doc.page_content) > 500 else ''}")
            print("-" * 60)

        # 5. 将文档列表格式化为 context 字符串，供 Prompt 使用
        context_str = "\n\n".join(
            f"[来源{i + 1}] {doc.page_content}" for i, doc in enumerate(final_docs)
        )
        return {"context": context_str, "question": question, "history": history}

    # 构造问答链
    qa_chain = (
            RunnableParallel({
                 "context": itemgetter("question") | RunnableLambda(merge_retrieval),
                 "question": itemgetter("question"),
                 "history": itemgetter("history"),
            })
            | RunnableLambda(reranker)
            | prompt
            | llm
            | StrOutputParser()
    )

    # 流式输出
    for chunk in qa_chain.stream(
            {
                "question": question,
                "history": history_messages,
            }
    ):
        if chunk:
            yield chunk


# ==================== 测试入口 ====================
if __name__ == '__main__':
    # 当前问题
    current_question = '675sr怎么样'
    test_history_id = 1
    for chunk in chat_stream(current_question, test_history_id):
        print(chunk, end="")
    # for chunk in chat_stream("675sr"):
    #     print(chunk, end="")

# 创建新对话
def create_new_chat(user_id):
    result = ChatDao.create_new_chat(user_id)
    return ResponseUtil.response_json(200, 'success', result)


