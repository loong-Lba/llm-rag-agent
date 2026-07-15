from fastapi import APIRouter
from pydantic import BaseModel
from ..service import ChatService

chat_router = APIRouter()


class CreateChatBody(BaseModel):
    userId: str


class SendChatBody(BaseModel):
    sessionId: int | None = None
    userId: str | None = None
    message: str


@chat_router.post("/createNewChat")
def create_new_chat(body: CreateChatBody):
    return ChatService.create_new_chat(body.userId)


@chat_router.post("/send")
def chat_send(body: SendChatBody):
    return ChatService.chat(
        message=body.message,
        session_id=body.sessionId,
        user_id=body.userId,
    )
