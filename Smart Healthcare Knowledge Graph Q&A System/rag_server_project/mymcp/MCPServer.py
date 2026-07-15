import os
import random
import shutil
import smtplib
from email.mime.text import MIMEText

import jieba
import pymysql
import redis
from fastmcp import FastMCP
from FlagEmbedding import FlagReranker
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jGraph
from rank_bm25 import BM25Okapi

# 创建 FastMCP 实例，用来注册对外可调用的 MCP 工具
mcp = FastMCP()

# 连接 Neo4j 医疗知识图谱，供图谱查询与文本语料构建复用
neo4j_graph = Neo4jGraph(
    url="bolt://127.0.0.1:7687",
    username="neo4j",
    password="rootroot",
    database="neo4j"
)

# 项目根目录及检索相关资源路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
VECTOR_DB_PATH = os.path.join(PROJECT_ROOT, "vectors")
VECTOR_DB_NAME = "medical_graph_house"
EMBEDDING_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "embedding_model")
RERANKER_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "bge-reranker-large_v1")
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-large"

# BM25 中文分词时使用的停用词，尽量减少无意义高频词对排序的干扰
STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
    "着", "没有", "看", "好", "自己", "这", "那", "他", "她", "它", "们",
    "这个", "那个", "什么", "哪", "怎么", "吗", "呢", "吧", "啊", "哦",
    "还", "被", "把", "让", "从", "对", "与", "但", "而", "或", "所",
    "为", "以", "及", "可", "可以", "能", "能够", "应该", "需要", "已经",
    "虽然", "如果", "因为", "所以", "只是", "还是", "不过", "然后",
    "之", "其", "中", "等", "等等", "即", "使", "向", "将", "按", "当",
    "于", "由", "比", "除了", "关于", "以及", "并且", "此外", "另外",
    "过", "来", "去", "做", "作", "像", "如", "如同", "由于",
}

# 下面这些全局变量用于缓存检索组件，避免每次调用工具都重复加载模型和索引
_embedding_model = None
_reranker_model = None
_vector_db = None
_bm25_docs = None
_bm25_index = None


def _safe_text(value):
    # 将任意值转成干净字符串，避免 None 或空白值影响后续处理
    if value is None:
        return ""
    return str(value).strip()


def _join_values(values):
    # 去重并拼接多值字段，最终用顿号连接，便于生成可读文本语料
    items = []
    for value in values or []:
        text = _safe_text(value)
        if text and text not in items:
            items.append(text)
    return "、".join(items)


def _get_embedding_model():
    # 懒加载向量化模型，首次使用时才真正创建对象
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            cache_folder=EMBEDDING_MODEL_PATH,
            model_kwargs={"device": "cpu"},
        )
    return _embedding_model


def _get_reranker_model():
    # 懒加载重排序模型，避免服务启动时一次性占用过多资源
    global _reranker_model
    if _reranker_model is None:
        _reranker_model = FlagReranker(
            model_name_or_path=RERANKER_MODEL_NAME,
            cache_dir=RERANKER_MODEL_PATH,
            use_fp16=True,
        )
    return _reranker_model


def _clear_retrieval_cache():
    # 构建或刷新向量库后，清空缓存，保证后续检索读取的是新数据
    global _vector_db, _bm25_docs, _bm25_index
    _vector_db = None
    _bm25_docs = None
    _bm25_index = None


# 查询MySQL数据库数据的工具
@mcp.tool(
    name="find_email",
    description="根据用户信息查询出对应的邮箱号信息",
)
async def find_email(sql: str, params: str = None) -> dict:
    if not sql.strip().lower().startswith("select"):
        return {"result": "只可以执行查询语句，不可以执行增删改语句"}
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="root",
            database="rag_server_project",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        cur = conn.cursor()
        cur.execute(sql, params or ())
        result = cur.fetchall()
        cur.close()
        conn.close()
        return {"result": result}
    except Exception as e:
        return {"result": str(e)}


# 发送邮件工具
@mcp.tool(
    name="send_email",
    description="给指定的邮箱发送登录的验证码"
)
async def send_email(receiver: str) -> dict:
    code = ""
    for i in range(4):
        code += str(int(random.random() * 10))
    sender = "925183137@qq.com"
    password = "jfvdzmollykbbfgg"
    subject = "登录验证码"
    content = f"【LBA科技】您的登录验证码是：{code}，提供给他人会导致账号被盗和资产损失，若非本人操作，轻修改密码。"
    message = MIMEText(content, "plain", "utf-8")
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    smtp_server = "smtp.qq.com"
    smtp_port = 587
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()
        r = redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )
        r.set(receiver, code, ex=60)
        r.close()
        return {"result": "发送成功"}
    except Exception as e:
        return {"result": str(e)}


# 验证验证码工具
@mcp.tool(
    name="verify_code",
    description="验证用户输入的验证码是否正确"
)
async def verify_code(receiver: str, code: str) -> dict:
    r = redis.Redis(
        host="127.0.0.1",
        port=6379,
        db=0,
        decode_responses=True,
    )
    redis_code = r.get(receiver)
    if code == redis_code:
        return {"result": "验证成功"}
    return {"result": "验证失败"}


def fetch_medical_documents_from_graph():
    # 从 Neo4j 图谱中读取疾病节点及其关联信息，并整理成可检索的文本文档
    rows = neo4j_graph.query(
        """
        MATCH (d:Disease)
        OPTIONAL MATCH (d)-[:DISEASE_CATEGORY]->(category:Category)
        OPTIONAL MATCH (d)-[:DISEASE_SYMPTOM]->(symptom:Symptom)
        OPTIONAL MATCH (d)-[:DISEASE_ACOMPANY]->(acompany:Disease)
        OPTIONAL MATCH (d)-[:DISEASE_DEPARTMENT]->(department:Department)
        OPTIONAL MATCH (d)-[:DISEASE_CUREWAY]->(cureway:Cureway)
        OPTIONAL MATCH (d)-[:DISEASE_CHECK]->(check:Check)
        OPTIONAL MATCH (d)-[:DISEASE_DRUG]->(drug:Drug)
        OPTIONAL MATCH (d)-[:DISEASE_DO_EAT]->(do_eat:Food)
        OPTIONAL MATCH (d)-[:DISEASE_NOT_EAT]->(not_eat:Food)
        OPTIONAL MATCH (d)-[:DISEASE_DISHES]->(dish:Dishes)
        RETURN id(d) AS disease_id,
               d.name AS name,
               d.desc AS `desc`,
               d.prevent AS prevent,
               d.cause AS cause,
               d.yibao_status AS yibao_status,
               d.get_prob AS get_prob,
               d.get_way AS get_way,
               d.cure_lasttime AS cure_lasttime,
               d.cured_prob AS cured_prob,
               d.cost_money AS cost_money,
               collect(DISTINCT category.name) AS categories,
               collect(DISTINCT symptom.name) AS symptoms,
               collect(DISTINCT acompany.name) AS acompanies,
               collect(DISTINCT department.name) AS departments,
               collect(DISTINCT cureway.name) AS cureways,
               collect(DISTINCT check.name) AS checks,
               collect(DISTINCT drug.name) AS drugs,
               collect(DISTINCT do_eat.name) AS do_eats,
               collect(DISTINCT not_eat.name) AS not_eats,
               collect(DISTINCT dish.name) AS dishes
        """
    )

    documents = []
    ids = []
    for row in rows:
        # 为每个疾病节点生成一篇文本化文档，文档 id 与图谱节点绑定
        disease_id = row.get("disease_id")
        name = _safe_text(row.get("name"))
        title = name or f"疾病{disease_id}"
        doc_id = f"disease-{disease_id}"
        content_lines = [f"疾病：{title}"]

        scalar_fields = [
            ("疾病分类", _join_values(row.get("categories"))),
            ("疾病介绍", _safe_text(row.get("desc"))),
            ("病因", _safe_text(row.get("cause"))),
            ("预防措施", _safe_text(row.get("prevent"))),
            ("医保情况", _safe_text(row.get("yibao_status"))),
            ("患病概率", _safe_text(row.get("get_prob"))),
            ("传染方式", _safe_text(row.get("get_way"))),
            ("治疗周期", _safe_text(row.get("cure_lasttime"))),
            ("治愈概率", _safe_text(row.get("cured_prob"))),
            ("治疗费用", _safe_text(row.get("cost_money"))),
            ("相关症状", _join_values(row.get("symptoms"))),
            ("并发症", _join_values(row.get("acompanies"))),
            ("就诊科室", _join_values(row.get("departments"))),
            ("治疗方式", _join_values(row.get("cureways"))),
            ("检查项目", _join_values(row.get("checks"))),
            ("相关药物", _join_values(row.get("drugs"))),
            ("推荐食物", _join_values(row.get("do_eats"))),
            ("不推荐食物", _join_values(row.get("not_eats"))),
            ("推荐菜谱", _join_values(row.get("dishes"))),
        ]

        for label, value in scalar_fields:
            if value:
                content_lines.append(f"{label}：{value}")

        documents.append(
            Document(
                id=doc_id,
                page_content="\n".join(content_lines),
                metadata={
                    "doc_id": doc_id,
                    "entity_type": "Disease",
                    "source": "neo4j_medical_graph",
                    "title": title,
                    "disease_id": disease_id,
                },
            )
        )
        ids.append(doc_id)
    return documents, ids


def build_medical_vector_store():
    # 把图谱转出来的文本文档写入 Chroma，本地形成可重复加载的向量库
    documents, ids = fetch_medical_documents_from_graph()
    if not documents:
        raise ValueError("未从 Neo4j 图谱中读取到可构建的疾病文档")

    # 重建前先清空旧向量库目录，避免旧数据残留
    shutil.rmtree(VECTOR_DB_PATH, ignore_errors=True)
    Chroma.from_documents(
        documents=documents,
        ids=ids,
        persist_directory=VECTOR_DB_PATH,
        collection_name=VECTOR_DB_NAME,
        embedding=_get_embedding_model(),
        collection_metadata={"hnsw:space": "cosine"},
    )
    _clear_retrieval_cache()
    return {
        "count": len(documents),
        "collection_name": VECTOR_DB_NAME,
        "persist_directory": VECTOR_DB_PATH,
    }


def _get_vector_db():
    # 懒加载 Chroma 向量库实例，后续检索直接复用
    global _vector_db
    if _vector_db is None:
        _vector_db = Chroma(
            persist_directory=VECTOR_DB_PATH,
            collection_name=VECTOR_DB_NAME,
            embedding_function=_get_embedding_model(),
        )
    return _vector_db


def _ensure_vector_store():
    # 确保向量库中已经有数据；如果为空则自动触发一次构建
    db = _get_vector_db()
    snapshot = db.get()
    if not snapshot.get("ids"):
        build_medical_vector_store()
        db = _get_vector_db()
    return db


def tokenize(text):
    # 中文分词并过滤停用词，为 BM25 稀疏检索准备词项序列
    return [
        word for word in jieba.cut(_safe_text(text))
        if word.strip() and word not in STOP_WORDS and len(word.strip()) > 1
    ]


def _get_bm25_retrieval(db):
    # 从向量库中取出全量文档，临时构建 BM25 检索对象并缓存起来
    global _bm25_docs, _bm25_index
    if _bm25_docs is not None and _bm25_index is not None:
        return _bm25_docs, _bm25_index

    snapshot = db.get()
    ids = snapshot.get("ids", [])
    documents = snapshot.get("documents", [])
    metadatas = snapshot.get("metadatas", [])

    _bm25_docs = [
        Document(
            id=ids[index],
            page_content=documents[index],
            metadata=(metadatas[index] if index < len(metadatas) else {}) or {},
        )
        for index in range(len(ids))
    ]
    tokenized_corpus = [tokenize(doc.page_content) for doc in _bm25_docs]
    _bm25_index = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
    return _bm25_docs, _bm25_index


def _bm25_search(bm25, bm25_docs, question, top_k=10):
    # 根据问题分词后的 BM25 分数做关键词检索，返回 top_k 个候选文档
    if bm25 is None or not bm25_docs:
        return []
    scores = bm25.get_scores(tokenize(question))
    score_indexes = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:top_k]
    return [bm25_docs[index] for index in score_indexes]


def _doc_key(doc, index):
    # 统一计算文档唯一标识，便于不同检索结果之间做去重和分数融合
    if getattr(doc, "id", None):
        return doc.id
    metadata = getattr(doc, "metadata", {}) or {}
    return metadata.get("doc_id") or metadata.get("disease_id") or f"doc-{index}"


def _rrf_result(vector_result, bm25_result, top_k=10):
    # 使用 RRF 融合向量检索与 BM25 检索结果，按排名而不是原始分数做合并
    docs_dict = {}
    scores_dict = {}

    for index, doc in enumerate(vector_result):
        key = _doc_key(doc, index)
        docs_dict[key] = doc
        scores_dict[key] = scores_dict.get(key, 0.0) + 1.0 / (60 + index + 1)

    for index, doc in enumerate(bm25_result):
        key = _doc_key(doc, index)
        docs_dict[key] = doc
        scores_dict[key] = scores_dict.get(key, 0.0) + 1.0 / (60 + index + 1)

    ranked_keys = sorted(scores_dict, key=scores_dict.get, reverse=True)[:top_k]
    return [docs_dict[key] for key in ranked_keys]


def _rerank_docs(question, docs, top_k=3):
    # 对融合后的候选文档做二次精排，留下最相关的 top_k 个结果
    if not docs:
        return []
    pairs = [[question, doc.page_content] for doc in docs]
    scores = _get_reranker_model().compute_score(pairs)
    if not isinstance(scores, list):
        scores = [scores]

    for doc, score in zip(docs, scores):
        metadata = dict(doc.metadata or {})
        metadata["relevance_score"] = round(float(score), 4)
        doc.metadata = metadata

    ranked_docs = sorted(
        docs,
        key=lambda item: (item.metadata or {}).get("relevance_score", 0),
        reverse=True,
    )
    return ranked_docs[:top_k]


def _format_docs(docs):
    # 把内部 Document 对象转成普通字典，便于工具结果直接返回给调用方
    results = []
    for doc in docs:
        metadata = dict(doc.metadata or {})
        results.append({
            "id": _doc_key(doc, 0),
            "title": metadata.get("title") or metadata.get("doc_id") or "未命名资料",
            "content": doc.page_content,
            "metadata": metadata,
        })
    return results


def hybrid_retrieve_medical_documents(question, top_k=10, rerank_top_k=3):
    # 完整混合检索流程：向量检索 -> BM25 检索 -> RRF 融合 -> reranker 精排
    db = _ensure_vector_store()
    retriever = db.as_retriever(search_kwargs={"k": top_k})
    vector_result = retriever.invoke(question)
    bm25_docs, bm25 = _get_bm25_retrieval(db)
    bm25_result = _bm25_search(bm25, bm25_docs, question, top_k)
    rrf_docs = _rrf_result(vector_result, bm25_result, top_k)
    reranked_docs = _rerank_docs(question, rrf_docs, min(rerank_top_k, len(rrf_docs)))
    return {
        "vector_docs": vector_result,
        "bm25_docs": bm25_result,
        "rrf_docs": rrf_docs,
        "final_docs": reranked_docs or rrf_docs,
    }


@mcp.tool(
    name="search_medical_hybrid",
    description="基于 Neo4j 医疗图谱生成的文本知识库执行向量检索、BM25 检索和 RRF 混合检索，返回最相关的医疗资料片段"
)
def search_medical_hybrid(question: str, top_k: int = 10, rerank_top_k: int = 3) -> dict:
    # 对外暴露的医疗混合检索工具，返回最终候选资料与可直接拼进提示词的上下文
    question_text = _safe_text(question)
    if not question_text:
        return {"error": "问题不能为空"}

    try:
        retrieval_result = hybrid_retrieve_medical_documents(question_text, top_k=max(int(top_k), 1), rerank_top_k=max(int(rerank_top_k), 1))
        final_docs = retrieval_result["final_docs"]
        if not final_docs:
            return {
                "result": {
                    "strategy": "rrf_hybrid",
                    "documents": [],
                    "context": "",
                    "message": "未检索到相关资料",
                }
            }

        context = "\n\n".join(
            f"[来源{index}] {doc.page_content}"
            for index, doc in enumerate(final_docs, start=1)
        )
        return {
            "result": {
                "strategy": "rrf_hybrid",
                "question": question_text,
                "documents": _format_docs(final_docs),
                "context": context,
                "vector_count": len(retrieval_result["vector_docs"]),
                "bm25_count": len(retrieval_result["bm25_docs"]),
                "rrf_count": len(retrieval_result["rrf_docs"]),
            }
        }
    except Exception as e:
        return {"error": str(e)}


# Neo4j 图谱查询工具
@mcp.tool(
    name="find_data",
    description="在Neo4j医疗知识图谱中查询疾病相关数据"
)
def find_data(cypher: str, params: dict = None) -> dict:
    # 执行图谱只读查询，只允许 MATCH 开头，防止误执行写操作
    try:
        if not cypher.strip().lower().startswith("match"):
            return {"error": "只允许执行 MATCH 查询语句"}
        result = neo4j_graph.query(cypher, params or {})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


# 启动 MCP 服务，对外提供 HTTP 方式的工具调用入口
if __name__ == '__main__':
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=9000,
        path="/mcp",
        show_banner=False
    )
