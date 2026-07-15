from ..dao.HistoryDao import (
    ensure_tables,
    create_session,
    find_sessions_by_user_id,
    find_session_by_id,
    update_session_summary,
    save_message,
    find_messages_by_session_id,
    delete_session,
)


ensure_tables()

# 安全文本
def _safe_text(value):
    if value is None:   # 如果传入的是None，返回空字符串，避免报错
        return ""
    return str(value).strip()   # 否则先转换成字符串，再去掉首尾空白字符后返回

# title长度限制
def _clip_text(value, size):
    text = _safe_text(value)    # 将值转为安全字符串，并按照指定长度截断
    if len(text) <= size:
        return text
    return text[:size]

# 新建title
def _build_title(question):
    title = _clip_text(question, 20)
    return title or "新对话"

# 创建新对话
def create_chat_session(user_id, title=None):
    user_id = _safe_text(user_id)
    if not user_id:
        return None
    return create_session(user_id, _clip_text(title, 255) or "新对话")

# 根据user_id查询聊天会话列表（查看用户有哪些对话）
def list_chat_sessions(user_id):
    user_id = _safe_text(user_id)
    if not user_id:
        return []
    return find_sessions_by_user_id(user_id)

# 根据session_id获取聊天会话记录（查看某个会话本身）
def get_chat_session(session_id):
    if not session_id:
        return None
    return find_session_by_id(session_id)

# 根据session_id查询聊天记录（查某一个会话里的消息）
def get_session_messages(session_id, limit=None):
    if not session_id:
        return []
    return find_messages_by_session_id(session_id, limit)


def append_chat_round(session_id, question, answer, route_type=None, retrieval_used=False, tool_name=None, tool_input=None, tool_output=None):
    # 如果没有会话id，说明无法归档这轮对话，直接返回失败
    if not session_id:
        return False

    # 对问题和回答做安全处理，None转为空字符串，并且去掉首尾空白
    question_text = _safe_text(question)
    answer_text = _safe_text(answer)

    # 如果用户问题有内容，就保存一条user消息
    if question_text:
        save_message(
            session_id=session_id,
            role="user",
            content=question_text,
            route_type=route_type,
            retrieval_used=retrieval_used,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=None,
        )
    # 如果助手回答有内容，就保存一条assistant消息
    if answer_text:
        save_message(
            session_id=session_id,
            role="assistant",
            content=answer_text,
            route_type=route_type,
            retrieval_used=retrieval_used,
            tool_name=tool_name,
            tool_input=None,
            tool_output=tool_output,
        )
    # 读取当前对话信息
    session = get_chat_session(session_id)
    # 取出当前标题，如果没有标题则用空字符串代替
    current_title = _safe_text(session.get("title") if session else "")
    # 如果已有标题且不是新对话，继续沿用，否则根据用户问题生成一个新标题
    title = current_title if current_title and current_title != "新对话" else _build_title(question_text)
    # 截取回答的前120个字符，作为摘要浏览
    last_answer_preview = _clip_text(answer_text, 120)
    # 更新会话摘要信息，包括标题、最后一个问题、最后一个回答预览
    update_session_summary(session_id, title, question_text, last_answer_preview)
    return True # 本轮对话追加成功

# 删除对话
def remove_chat_session(session_id):
    if not session_id:
        return False
    return delete_session(session_id)
