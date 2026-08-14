import json

from fastapi import APIRouter, Query, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse, StreamingResponse

from chat.service import ChatService, KnowledgeBaseService
from common import ResponseUtil

chat_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@chat_router.get("/chatNoStream")
def chat_no_stream(question: str):
    return ChatService.chat_no_stream(question)


def _encode_sse(item):
    payload = json.dumps(item["payload"], ensure_ascii=False)
    return "event: {event}\ndata: {payload}\n\n".format(
        event=item["event"],
        payload=payload,
    )


@chat_router.get("/chatStream")
async def chat_stream(
    request: Request,
    question: str = Query(..., min_length=1),
    history_id: int = Query(..., gt=0),
    knowledge_base: str = Query(..., min_length=1),
    request_id: str = Query(..., min_length=1, max_length=64),
):
    async def generator():
        async for item in ChatService.chat_stream(
            question,
            history_id,
            knowledge_base,
            request_id,
            request.is_disconnected,
        ):
            yield _encode_sse(item)

    return StreamingResponse(
        content=generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@chat_router.get("/knowledgeBases")
def knowledge_bases():
    return ResponseUtil.response_json(
        200,
        "success",
        KnowledgeBaseService.list_knowledge_bases(),
    )


@chat_router.get("/goChatNoStream", response_class=HTMLResponse)
def go_chat_no_stream(request: Request):
    return templates.TemplateResponse(request, "chat_no_stream.html")


@chat_router.get("/goChatStream", response_class=HTMLResponse)
def go_chat_stream(request: Request):
    return templates.TemplateResponse(request, "chat_stream.html")


@chat_router.post("/createNewChat")
def create_new_chat(user_id: int):
    return ChatService.create_new_chat(user_id)
