import csv
import os
import re
import threading
from hashlib import sha256

import jieba
from chromadb import PersistentClient
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

PATH_BASE = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATASET_PATH = os.path.join(PATH_BASE, "datasets")
VECTOR_DB_PATH = os.path.join(PATH_BASE, "vectors")
EMBEDDING_MODEL_PATH = os.path.join(PATH_BASE, "models", "embedding_model")
RERANKER_MODEL_PATH = os.path.join(PATH_BASE, "models", "bge-reranker-large_v1")
EMBEDDING_MODEL_NAME = os.path.join(
    EMBEDDING_MODEL_PATH,
    "models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2",
    "snapshots",
    "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
)
RERANKER_MODEL_NAME = os.path.join(
    RERANKER_MODEL_PATH,
    "models--BAAI--bge-reranker-large",
    "snapshots",
    "55611d7bca2a7133960a6d3b71e083071bbfc312",
)

KNOWLEDGE_BASES = {
    "motogp_675sr": {
        "id": "motogp_675sr",
        "name": "MotoGP/675SR 知识库",
        "collection_name": "motogp_675sr_house",
        "source_file": "motogpand675sr.csv",
        "vector_top_k": 10,
        "bm25_top_k": 10,
        "top_k": 3,
    },
    "law": {
        "id": "law",
        "name": "法律知识库",
        "collection_name": "law_house",
        "source_file": "法律数据集.csv",
        "vector_top_k": 10,
        "bm25_top_k": 10,
        "top_k": 3,
    },
}

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "这个",
    "那个", "什么", "哪", "怎么", "吗", "呢", "吧", "啊", "与", "及", "或", "关于",
}

_embedding_model = None
_reranker_model = None
_embedding_lock = threading.Lock()
_reranker_lock = threading.Lock()
_retrieval_lock = threading.Lock()


def get_knowledge_base(knowledge_base_id):
    config = KNOWLEDGE_BASES.get(knowledge_base_id)
    if not config:
        raise ValueError("不支持的知识库")
    return config.copy()


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                from langchain_huggingface import HuggingFaceEmbeddings

                _embedding_model = HuggingFaceEmbeddings(
                    model_name=EMBEDDING_MODEL_NAME,
                    model_kwargs={"device": "cpu", "local_files_only": True},
                )
    return _embedding_model


def get_reranker_model():
    global _reranker_model
    if _reranker_model is None:
        with _reranker_lock:
            if _reranker_model is None:
                from FlagEmbedding import FlagReranker

                _reranker_model = FlagReranker(
                    model_name_or_path=RERANKER_MODEL_NAME,
                    use_fp16=False,
                )
    return _reranker_model


def _source_version(config):
    rows = _read_source_rows(config)
    digest = sha256("\n".join(rows).encode("utf-8")).hexdigest()[:12]
    return digest


def versioned_collection_name(config):
    return "{0}_v_{1}".format(config["collection_name"], _source_version(config))


def _collection_names():
    client = PersistentClient(path=VECTOR_DB_PATH)
    names = []
    for collection in client.list_collections():
        names.append(collection if isinstance(collection, str) else collection.name)
    return names


def _active_collection_name(config):
    versioned_name = versioned_collection_name(config)
    if versioned_name not in _collection_names():
        return config["collection_name"]

    collection = PersistentClient(path=VECTOR_DB_PATH).get_collection(versioned_name)
    source_count = len(_read_source_rows(config))
    sample = collection.get(limit=1, include=["metadatas"])
    metadatas = sample.get("metadatas") or []
    is_ready = (
        collection.count() == source_count
        and (collection.metadata or {}).get("hnsw:space") == "cosine"
        and metadatas
        and metadatas[0].get("knowledge_base_id") == config["id"]
    )
    return versioned_name if is_ready else config["collection_name"]


def _open_db(config):
    return Chroma(
        persist_directory=VECTOR_DB_PATH,
        collection_name=_active_collection_name(config),
        embedding_function=get_embedding_model(),
    )


def _read_source_rows(config):
    csv_path = os.path.join(DATASET_PATH, config["source_file"])
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames or "text" not in reader.fieldnames:
            raise ValueError("知识库 CSV 缺少 text 列")
        return [
            row["text"].strip()
            for row in reader
            if row.get("text") and row["text"].strip()
        ]


def _article_number(text):
    match = re.search(r"《[^》]+》\s*(第[^条]{1,20}条)", text)
    return match.group(1) if match else None


def build_metadata(config, text, row_number):
    content_hash = sha256(text.encode("utf-8")).hexdigest()
    return {
        "knowledge_base_id": config["id"],
        "knowledge_base_name": config["name"],
        "source_file": config["source_file"],
        "row_number": row_number,
        "article_number": _article_number(text) or "",
        "chunk_index": row_number,
        "content_hash": content_hash,
    }


def stable_chunk_id(config, text, row_number):
    digest = sha256(text.encode("utf-8")).hexdigest()[:16]
    return "{0}:{1}:{2}:{3}".format(config["id"], config["source_file"], row_number, digest)


def _source_metadata_map(config):
    mapping = {}
    for row_number, text in enumerate(_read_source_rows(config), 1):
        mapping.setdefault(text, []).append(build_metadata(config, text, row_number))
    return mapping


def _complete_metadata(config, text, metadata, source_map):
    result = dict(metadata or {})
    if not result.get("knowledge_base_id"):
        candidates = source_map.get(text) or []
        if candidates:
            result.update(candidates.pop(0))
    result.setdefault("knowledge_base_id", config["id"])
    result.setdefault("knowledge_base_name", config["name"])
    result.setdefault("source_file", config["source_file"])
    result.setdefault("row_number", None)
    result.setdefault("article_number", _article_number(text) or "")
    return result


def list_knowledge_bases():
    result = []
    for config in KNOWLEDGE_BASES.values():
        csv_path = os.path.join(DATASET_PATH, config["source_file"])
        source_count = 0
        chunk_count = 0
        status = "ready"
        message = ""
        try:
            source_count = len(_read_source_rows(config))
            collection_name = _active_collection_name(config)
            collection = PersistentClient(path=VECTOR_DB_PATH).get_collection(collection_name)
            chunk_count = collection.count()
            sample = collection.get(limit=1, include=["metadatas"])
            metadatas = sample.get("metadatas") or []
            collection_metadata = collection.metadata or {}
            if chunk_count != source_count:
                status = "degraded"
                message = "CSV 行数与向量片段数不一致"
            elif collection_metadata.get("hnsw:space") != "cosine":
                status = "degraded"
                message = "当前为兼容旧库，建议构建带 metadata 的 cosine 版本库"
            elif metadatas and not metadatas[0].get("knowledge_base_id"):
                status = "degraded"
                message = "向量库可用，但建议重建以补齐来源 metadata"
        except Exception as exc:
            status = "unavailable"
            message = str(exc)

        result.append({
            "id": config["id"],
            "name": config["name"],
            "sourceFile": config["source_file"],
            "status": status,
            "statusMessage": message,
            "documentCount": 1 if os.path.exists(csv_path) else 0,
            "sourceRowCount": source_count,
            "chunkCount": chunk_count,
        })
    return result


def _tokenize(text):
    return [
        word for word in jieba.cut(text)
        if word.strip() and word not in STOP_WORDS and len(word.strip()) > 1
    ]


def _round(value):
    if value is None:
        return None
    return round(float(value), 6)


def search_candidates(knowledge_base_id, question):
    config = get_knowledge_base(knowledge_base_id)
    db = _open_db(config)
    all_data = db.get(include=["documents", "metadatas"])
    ids = all_data.get("ids") or []
    documents = all_data.get("documents") or []
    metadatas = all_data.get("metadatas") or [{} for _ in documents]
    if not documents:
        return {
            "config": config,
            "question": question,
            "fused": [],
            "vector_hit_count": 0,
            "bm25_hit_count": 0,
        }

    source_map = _source_metadata_map(config)
    records = {}
    for doc_id, text, metadata in zip(ids, documents, metadatas):
        records[doc_id] = {
            "id": doc_id,
            "content": text,
            "metadata": _complete_metadata(config, text, metadata, source_map),
            "scores": {
                "vectorDistance": None,
                "vectorSimilarity": None,
                "vectorRank": None,
                "bm25Score": None,
                "bm25Rank": None,
                "rrfScore": 0.0,
                "rrfRank": None,
                "rerankScore": None,
                "rerankRank": None,
            },
        }

    query_embedding = get_embedding_model().embed_query(question)
    vector_data = db._collection.query(
        query_embeddings=[query_embedding],
        n_results=min(config["vector_top_k"], len(documents)),
        include=["distances"],
    )
    vector_ids = (vector_data.get("ids") or [[]])[0]
    vector_distances = (vector_data.get("distances") or [[]])[0]
    is_cosine = (db._collection.metadata or {}).get("hnsw:space") == "cosine"
    for rank, (doc_id, distance) in enumerate(zip(vector_ids, vector_distances), 1):
        if doc_id not in records:
            continue
        records[doc_id]["scores"].update({
            "vectorDistance": _round(distance),
            "vectorSimilarity": _round(1.0 - float(distance)) if is_cosine else None,
            "vectorRank": rank,
        })

    bm25 = BM25Okapi([_tokenize(text) for text in documents])
    raw_bm25_scores = bm25.get_scores(_tokenize(question))
    bm25_indices = [
        index for index in sorted(
            range(len(raw_bm25_scores)),
            key=lambda item: (-raw_bm25_scores[item], ids[item]),
        )
        if raw_bm25_scores[index] > 0
    ][:config["bm25_top_k"]]
    bm25_ids = []
    for rank, index in enumerate(bm25_indices, 1):
        doc_id = ids[index]
        bm25_ids.append(doc_id)
        records[doc_id]["scores"].update({
            "bm25Score": _round(raw_bm25_scores[index]),
            "bm25Rank": rank,
        })

    for rank, doc_id in enumerate(vector_ids, 1):
        if doc_id in records:
            records[doc_id]["scores"]["rrfScore"] += 1.0 / (60 + rank)
    for rank, doc_id in enumerate(bm25_ids, 1):
        records[doc_id]["scores"]["rrfScore"] += 1.0 / (60 + rank)

    candidate_ids = sorted(set(vector_ids) | set(bm25_ids))
    fused = sorted(
        [records[doc_id] for doc_id in candidate_ids if doc_id in records],
        key=lambda item: (-item["scores"]["rrfScore"], item["id"]),
    )
    for rank, item in enumerate(fused, 1):
        item["scores"]["rrfScore"] = _round(item["scores"]["rrfScore"])
        item["scores"]["rrfRank"] = rank

    return {
        "config": config,
        "question": question,
        "fused": fused,
        "vector_hit_count": len(vector_ids),
        "bm25_hit_count": len(bm25_ids),
    }


def rerank_candidates(search_result):
    config = search_result["config"]
    fused = search_result["fused"]
    if not fused:
        return _empty_result(config)

    pairs = [[search_result["question"], item["content"]] for item in fused]
    with _retrieval_lock:
        rerank_scores = get_reranker_model().compute_score(pairs, normalize=True)
    if hasattr(rerank_scores, "tolist"):
        rerank_scores = rerank_scores.tolist()
    if not isinstance(rerank_scores, (list, tuple)):
        rerank_scores = [rerank_scores]
    for item, score in zip(fused, rerank_scores):
        item["scores"]["rerankScore"] = _round(score)

    reranked = sorted(
        fused,
        key=lambda item: (-(item["scores"]["rerankScore"] or 0.0), item["id"]),
    )
    for rank, item in enumerate(reranked, 1):
        item["scores"]["rerankRank"] = rank

    selected = reranked[:config["top_k"]]
    sources = [_serialize_source(config, item, index) for index, item in enumerate(selected, 1)]
    threshold = float(os.getenv("RAG_MIN_RERANK_SCORE", "0.5"))
    best_score = sources[0]["scores"]["rerankScore"] if sources else None
    decision = "answer" if best_score is not None and best_score >= threshold else "insufficient_evidence"
    return {
        "sources": sources,
        "summary": {
            "vectorHitCount": search_result["vector_hit_count"],
            "bm25HitCount": search_result["bm25_hit_count"],
            "fusedCandidateCount": len(fused),
            "returnedSourceCount": len(sources),
            "bestRerankScore": best_score,
            "minimumRerankScore": threshold,
            "decision": decision,
        },
    }


def retrieve(knowledge_base_id, question):
    return rerank_candidates(search_candidates(knowledge_base_id, question))


def _serialize_source(config, item, index):
    metadata = item["metadata"]
    return {
        "index": index,
        "knowledgeBase": {"id": config["id"], "name": config["name"]},
        "sourceFile": metadata.get("source_file") or config["source_file"],
        "articleNumber": metadata.get("article_number") or None,
        "rowNumber": metadata.get("row_number"),
        "content": item["content"],
        "scores": item["scores"],
    }


def _empty_result(config):
    threshold = float(os.getenv("RAG_MIN_RERANK_SCORE", "0.5"))
    return {
        "sources": [],
        "summary": {
            "vectorHitCount": 0,
            "bm25HitCount": 0,
            "fusedCandidateCount": 0,
            "returnedSourceCount": 0,
            "bestRerankScore": None,
            "minimumRerankScore": threshold,
            "decision": "insufficient_evidence",
        },
    }
