import json
import re

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from ai.models import LoadALYModel
from chat.dao import ChatDao, HistoryDao
from chat.service import KnowledgeBaseService
from common import ResponseUtil

NO_ANSWER_TEXT = "资料中未提及相关内容"

RAG_SYSTEM_TEMPLATE = """
你是一个严格依据检索资料回答问题的知识库助手。

【强制规则】
1. 只能使用下面【本次检索来源】中的事实，不得使用模型自身知识补充。
2. 每个事实结论都必须标注对应来源编号，例如 [1] 或 [1][2]。
3. 引用编号只能使用本次给出的编号，且必须与支持该结论的来源对应。
4. 历史问题只用于理解代词和上下文，不能作为事实依据。
5. 如果来源不足以回答，必须只回复“资料中未提及相关内容”。

【本次检索来源】
{context}
"""


def chat_no_stream(question):
    llm = LoadALYModel.load_model()
    response = llm.invoke(question)
    if response.content:
        return ResponseUtil.response_json(200, "success", response.content)
    return ResponseUtil.response_json(500, "fail", "没有回答")


def load_history_messages(session_id):
    history_data = HistoryDao.find_history_for_context(int(session_id))
    messages = []
    for item in history_data:
        question = (item.get("question") or "").strip()
        answer = (item.get("answer") or "").strip()
        if question:
            messages.append(HumanMessage(content=question))
        if answer:
            messages.append(AIMessage(content=answer))
    return messages


def _database_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value or ""


def _event(request_id, event_type, data):
    return {
        "event": event_type,
        "payload": {
            "requestId": request_id,
            "type": event_type,
            "data": data,
        },
    }


def _format_context(sources):
    return "\n\n".join(
        "[{index}] {content}".format(index=source["index"], content=source["content"])
        for source in sources
    )


def _has_valid_citation(answer, source_count):
    citations = re.findall(r"\[(\d+)\]", answer)
    return bool(citations) and all(1 <= int(item) <= source_count for item in citations)


def _sanitize_citations(text, source_count):
    return re.sub(
        r"\[(\d+)\]",
        lambda match: match.group(0) if 1 <= int(match.group(1)) <= source_count else "",
        text,
    )


def _save_exchange(history_id, question, answer, request_id, knowledge_base, sources, summary):
    rag_metadata = json.dumps(
        {
            "schemaVersion": 1,
            "requestId": request_id,
            "knowledgeBase": {
                "id": knowledge_base["id"],
                "name": knowledge_base["name"],
            },
            "route": "selected_knowledge_base",
            "sources": sources,
            "retrievalSummary": summary,
        },
        ensure_ascii=False,
    )
    return HistoryDao.save_chat_exchange(
        int(history_id),
        question,
        answer,
        rag_metadata,
        request_id,
    )


async def chat_stream(question, history_id, knowledge_base_id, request_id, is_disconnected):
    answer_parts = []

    try:
        question = (question or "").strip()
        if not question:
            raise ValueError("问题不能为空")
        if await is_disconnected():
            return

        knowledge_base = KnowledgeBaseService.get_knowledge_base(knowledge_base_id)
        if not await run_in_threadpool(HistoryDao.root_history_exists, int(history_id)):
            raise ValueError("会话不存在")

        existing = await run_in_threadpool(HistoryDao.find_exchange_by_request_id, history_id, request_id)
        if existing:
            rag_metadata = json.loads(existing.get("rag_metadata") or "{}")
            yield _event(request_id, "route", {"mode": "selected_knowledge_base", "knowledgeBase": rag_metadata.get("knowledgeBase", {})})
            yield _event(request_id, "sources", {"items": rag_metadata.get("sources", []), "summary": rag_metadata.get("retrievalSummary", {})})
            yield _event(request_id, "answer_start", {"citationRequired": bool(rag_metadata.get("sources"))})
            yield _event(request_id, "token", {"content": _database_text(existing.get("answer"))})
            yield _event(request_id, "done", {"historyId": int(history_id), "recordId": existing["history_id"], "saved": True, "replayed": True})
            return

        history_messages = await run_in_threadpool(load_history_messages, history_id)
        yield _event(
            request_id,
            "route",
            {"mode": "selected_knowledge_base", "knowledgeBase": {"id": knowledge_base["id"], "name": knowledge_base["name"]}},
        )
        yield _event(
            request_id,
            "searching",
            {"vectorTopK": knowledge_base["vector_top_k"], "bm25TopK": knowledge_base["bm25_top_k"]},
        )

        search_result = await run_in_threadpool(KnowledgeBaseService.search_candidates, knowledge_base_id, question)
        if await is_disconnected():
            return
        yield _event(
            request_id,
            "reranking",
            {"candidateCount": len(search_result["fused"]), "topK": knowledge_base["top_k"]},
        )

        retrieval = await run_in_threadpool(KnowledgeBaseService.rerank_candidates, search_result)
        summary = retrieval["summary"]
        sources = retrieval["sources"]
        if await is_disconnected():
            return
        yield _event(request_id, "sources", {"items": sources, "summary": summary})
        yield _event(request_id, "answer_start", {"citationRequired": summary["decision"] == "answer"})

        if summary["decision"] != "answer":
            answer_parts.append(NO_ANSWER_TEXT)
            yield _event(request_id, "token", {"content": NO_ANSWER_TEXT})
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", RAG_SYSTEM_TEMPLATE),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{question}"),
                ]
            )
            chain = prompt | LoadALYModel.load_model() | StrOutputParser()
            citation_buffer = ""
            chunk_stream = chain.stream({"context": _format_context(sources), "history": history_messages, "question": question})
            async for chunk in iterate_in_threadpool(iter(chunk_stream)):
                if await is_disconnected():
                    return
                if not chunk:
                    continue
                citation_buffer += chunk
                last_open = citation_buffer.rfind("[")
                last_close = citation_buffer.rfind("]")
                if last_open > last_close:
                    ready_text = citation_buffer[:last_open]
                    citation_buffer = citation_buffer[last_open:]
                else:
                    ready_text = citation_buffer
                    citation_buffer = ""
                safe_chunk = _sanitize_citations(ready_text, len(sources))
                if safe_chunk:
                    answer_parts.append(safe_chunk)
                    yield _event(request_id, "token", {"content": safe_chunk})

            safe_tail = "" if citation_buffer.startswith("[") else _sanitize_citations(citation_buffer, len(sources))
            if safe_tail:
                answer_parts.append(safe_tail)
                yield _event(request_id, "token", {"content": safe_tail})

            complete_answer = "".join(answer_parts).strip()
            if not _has_valid_citation(complete_answer, len(sources)):
                citation_suffix = "\n\n参考来源：" + "".join("[{0}]".format(source["index"]) for source in sources)
                answer_parts.append(citation_suffix)
                yield _event(request_id, "token", {"content": citation_suffix})

        if await is_disconnected():
            return
        answer = "".join(answer_parts).strip()
        try:
            record_id = await run_in_threadpool(
                _save_exchange,
                history_id,
                question,
                answer,
                request_id,
                knowledge_base,
                sources,
                summary,
            )
        except Exception as exc:
            print("RAG persistence failed:", exc)
            yield _event(request_id, "error", {"code": "PERSIST_FAILED", "message": "回答生成完成，但保存失败", "retryable": True})
            return

        yield _event(request_id, "done", {"historyId": int(history_id), "recordId": record_id, "saved": True})
    except ValueError as exc:
        message = str(exc)
        code = "SESSION_NOT_FOUND" if message == "会话不存在" else "INVALID_REQUEST"
        yield _event(request_id, "error", {"code": code, "message": message, "retryable": False})
    except Exception as exc:
        print("RAG stream failed:", exc)
        yield _event(request_id, "error", {"code": "RAG_FAILED", "message": "检索或回答生成失败", "retryable": True})


def create_new_chat(user_id):
    result = ChatDao.create_new_chat(user_id)
    return ResponseUtil.response_json(200, "success", result)
