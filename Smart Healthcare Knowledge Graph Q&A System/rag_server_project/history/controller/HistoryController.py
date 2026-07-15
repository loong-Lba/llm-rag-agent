from fastapi import APIRouter
from ..service import HistoryService

history_router = APIRouter()


@history_router.get("/list")
def history_list(userId: str):
    data = HistoryService.list_chat_sessions(userId)
    return {
        "code": 200,
        "msg": "success",
        "data": data,
    }


@history_router.get("/detail")
def history_detail(sessionId: int):
    data = HistoryService.get_session_messages(sessionId)
    return {
        "code": 200,
        "msg": "success",
        "data": data,
    }


@history_router.delete("/delete")
def history_delete(sessionId: int):
    ok = HistoryService.remove_chat_session(sessionId)
    return {
        "code": 200 if ok else 500,
        "msg": "success" if ok else "删除失败",
    }
