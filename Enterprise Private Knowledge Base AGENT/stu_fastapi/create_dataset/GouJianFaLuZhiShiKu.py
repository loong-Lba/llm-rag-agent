import argparse
import os
import sys

PATH_BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PATH_BASE not in sys.path:
    sys.path.insert(0, PATH_BASE)

from langchain_chroma import Chroma
from langchain_core.documents import Document

from chat.service import KnowledgeBaseService


def _load_documents(knowledge_base_id):
    config = KnowledgeBaseService.get_knowledge_base(knowledge_base_id)
    documents = []
    ids = []
    for row_number, text in enumerate(KnowledgeBaseService._read_source_rows(config), 1):
        documents.append(
            Document(
                page_content=text,
                metadata=KnowledgeBaseService.build_metadata(config, text, row_number),
            )
        )
        ids.append(KnowledgeBaseService.stable_chunk_id(config, text, row_number))
    return config, documents, ids


def rebuild_knowledge_base(knowledge_base_id):
    config, documents, ids = _load_documents(knowledge_base_id)
    collection_name = KnowledgeBaseService.versioned_collection_name(config)
    db = Chroma(
        persist_directory=KnowledgeBaseService.VECTOR_DB_PATH,
        collection_name=collection_name,
        embedding_function=KnowledgeBaseService.get_embedding_model(),
        collection_metadata={"hnsw:space": "cosine"},
    )
    if documents:
        texts = [document.page_content for document in documents]
        metadatas = [document.metadata for document in documents]
        embeddings = KnowledgeBaseService.get_embedding_model().embed_documents(texts)
        db._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
    count = db._collection.count()
    if count != len(documents):
        raise RuntimeError("知识库片段数校验失败：期望 {0}，实际 {1}".format(len(documents), count))
    print("{0} 构建成功：{1}，共 {2} 个片段".format(config["name"], collection_name, count))


def rebuild_all():
    for knowledge_base_id in KnowledgeBaseService.KNOWLEDGE_BASES:
        rebuild_knowledge_base(knowledge_base_id)


def main():
    parser = argparse.ArgumentParser(description="重建指定 Chroma 知识库")
    parser.add_argument(
        "knowledge_base",
        choices=["all"] + list(KnowledgeBaseService.KNOWLEDGE_BASES.keys()),
        help="知识库 ID，或 all",
    )
    args = parser.parse_args()
    if args.knowledge_base == "all":
        rebuild_all()
    else:
        rebuild_knowledge_base(args.knowledge_base)


if __name__ == "__main__":
    main()
