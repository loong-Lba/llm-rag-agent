import os
import pandas as pd
from chromadb import db
from langchain_chroma import Chroma
from langchain_core import documents
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from openai.types import embedding_model
from ai.models import LoadALYModel
from FlagEmbedding import FlagAutoModel, FlagReranker

# 项目根路径
path_base = os.path.dirname(os.path.dirname(__file__))
# 向量化模型路径
embedding_model_path = os.path.join(path_base, 'models', 'embedding_model')
#重排序模型路径
reranker_model_path = os.path.join(path_base, 'models', 'bge-reranker-large_v1')
# 数据集路径
dataset_path = os.path.join(path_base, 'datasets')
# 向量数据库存储路径
vector_db_path = os.path.join(path_base, 'vectors')
# 向量数据库集合的名字
vector_db_name = 'motogp_675sr_house'


# 加载向量化模型
embedding_model = HuggingFaceEmbeddings(
    model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
    cache_folder=embedding_model_path,
)

# 定义构造外部知识库的函数
def build_motogp_675sr_house():
    # pandas读取csv数据
    df = pd.read_csv(os.path.join(dataset_path, 'motogpand675sr.csv'))
    # df数据类型转为list
    data = df.values.tolist()
    # list转为document对象 --- document对象的page_content的值为list中的元素字符串
    documents = [Document(page_content=item[0])for item in data]

    # 存储数据集
    Chroma.from_documents(  # 基于documents创建向量数据库
        documents=documents,  # 文档
        persist_directory=vector_db_path,  # 数据库存储的路径
        collection_name=vector_db_name,  # 集合名字
        embedding=embedding_model,  # 向量化模型
        collection_metadata={"hnsw:space": "cosine"},  # 检索规则
    )
    print("构建知识库成功")

# 定义检索函数
def check_mod(question):
    # 加载大模型
    llm = LoadALYModel.load_model()
    # 获取检索对象
    db = Chroma(
        persist_directory=vector_db_path,  # 数据库存储的路径
        collection_name=vector_db_name,  # 集合名字
        embedding_function=embedding_model,  # 向量化模型
    )
    print('成功获取检索对象')

    #执行检索
    retriever = db.as_retriever(search_kwargs={"k": 3})

    template = """
        你是一个 MotoGP 与摩托车 675SR 领域的知识问答助手。
        请基于给定的【参考上下文】准确回答用户问题。

        回答要求：
        1. 优先依据参考上下文回答
        2. 不要捏造信息
        3. 如果参考上下文中没有相关内容，请明确说明“资料中未提及相关内容”

        - 参考上下文: {context}
        - 用户问题: {question}
    """

    # 创建一个提示词模板，用于将检索到的文档上下文和用户问题组合成完整的输入，发送给大语言模型（LLM）。
    prompt = PromptTemplate(input_variables=["context", "question"], template=template)

    # 加载重排序模型
    reranker_model = FlagReranker(
        # 模型名称
        model_name_or_path="BAAI/bge-reranker-large",
        # 模型缓存路径
        cache_dir=reranker_model_path,
        # 是否使用fp16
        use_fp16=True
    )
    # 重排序
    def reranker(inputs):
        # 这个函数会接收管道传来的 question 和 初始检索结果
        question = inputs["question"]
        docs = inputs["context"]  # 这是管道内检索得到的结果

        # 建立列表，存储检索器返回的文档
        docs = retriever.invoke(question)

        # 构建配对
        pairs = [(question, doc.page_content) for doc in docs]

        # 计算重排分数
        scores = reranker_model.compute_score(pairs)

        # 将分数和文档绑定
        scored_docs = list(zip(scores, docs))

        # 按分数从高到低排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # 取出前 3 个文档（只保留文档对象，丢弃分数）
        top_k = 3

        top_docs = [doc for score, doc in scored_docs[:top_k]]
        # 打印重排序结果
        print(f"重排序后最相关的 {top_k} 个文档：")
        for i, doc in enumerate(top_docs):
            print(f"第{i + 1}名: {doc.page_content[:50]}...")
        # 返回结果
        return {"context": top_docs, "question": inputs["question"]}

    # 封装QA链
    qa = (
        RunnableParallel({  # 并行执行器：同时运行多个任务，然后吧它们的结果打包成一个字典，供下一步使用
            "context": retriever,
            "question": RunnablePassthrough(),  # 透传执行器 --- 内容不做任何更改直接传递
        })
        | RunnableLambda(reranker)
        | prompt  # 格式化提示词
        | llm  # 调用模型
        | StrOutputParser()  # 输出解析器 --- 字符串的方式输出
)

    # 执行问答
    response = qa.invoke(question)  # invoke：一次性输入，一次性获取完整输出
    print(response)

if __name__ == '__main__':
    build_motogp_675sr_house()
    check_mod("675SR 的定位是什么？")
