import ast
import json
from langchain_core.messages import HumanMessage, AIMessage
from ...ai.LoadAgent import load_medical_chat_agent, decide_chat_route, direct_chat
from ...history.service import HistoryService


medical_chat_agent = load_medical_chat_agent()


def _parse_route_result(raw_result, question):
    text = str(raw_result).strip()
    for parser in (json.loads, ast.literal_eval):
        try:
            data = parser(text)
            if isinstance(data, dict):
                return {
                    "route": data.get("route", "DIRECT"),
                    "resolved_question": data.get("resolved_question") or question,
                    "reason": data.get("reason", ""),
                }
        except Exception:
            continue
    return {
        "route": "DIRECT",
        "resolved_question": question,
        "reason": text,
    }


def load_history_messages(session_id, limit=10):
    rows = HistoryService.get_session_messages(session_id, limit=limit)
    messages = []
    for item in rows:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def direct_chat_answer(question, history_messages):
    return direct_chat(question, history_messages)


def medical_graph_chat(question, history_messages):
    response = medical_chat_agent.invoke({
        "messages": [
            *[
                {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
                for msg in history_messages
            ],
            {"role": "user", "content": question}
        ]
    })
    messages = response.get("messages", [])

    used_tools = []
    tool_inputs = []
    tool_outputs = []
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None) or []
        for call in tool_calls:
            name = str(call.get("name") or "").strip()
            if name:
                used_tools.append(name)
            args = call.get("args")
            if args is not None:
                tool_inputs.append(str(args))
        if getattr(msg, "type", "") == "tool":
            content = getattr(msg, "content", None)
            if content:
                tool_outputs.append(str(content))

    answer_text = "模型没有输出"
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            answer_text = msg.content
            break

    return {
        "answer": answer_text,
        "tool_name": ", ".join(dict.fromkeys(used_tools)) if used_tools else None,
        "tool_input": "\n".join(tool_inputs) if tool_inputs else None,
        "tool_output": "\n".join(tool_outputs) if tool_outputs else None,
    }


def _safe_preview(text, size=500):
    value = str(text or "").strip()
    if len(value) <= size:
        return value
    return value[:size]


def create_new_chat(user_id):
    session = HistoryService.create_chat_session(user_id)
    if not session:
        return {"code": 500, "msg": "创建会话失败"}
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "sessionId": session["id"],
            "title": session["title"],
        }
    }


def chat(message, session_id, user_id=None):
    if not session_id:
        session = HistoryService.create_chat_session(user_id or "guest")
        session_id = session["id"]

    history_messages = load_history_messages(session_id)
    route_result = _parse_route_result(decide_chat_route(message, history_messages), message)
    route = route_result["route"]
    resolved_question = route_result["resolved_question"] or message

    retrieval_used = route == "MEDICAL_GRAPH"
    tool_name = None
    tool_input = resolved_question
    tool_output = None

    if route == "MEDICAL_GRAPH":
        medical_result = medical_graph_chat(resolved_question, history_messages)
        answer = medical_result["answer"]
        tool_name = medical_result.get("tool_name") or "search_medical_hybrid"
        tool_input = medical_result.get("tool_input") or resolved_question
        tool_output = _safe_preview(medical_result.get("tool_output") or answer)
    else:
        answer = direct_chat_answer(resolved_question, history_messages)

    HistoryService.append_chat_round(
        session_id=session_id,
        question=message,
        answer=answer,
        route_type=route,
        retrieval_used=retrieval_used,
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
    )

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "sessionId": session_id,
            "answer": answer,
            "route": route,
            "retrievalUsed": retrieval_used,
            "resolvedQuestion": resolved_question,
        }
    }
