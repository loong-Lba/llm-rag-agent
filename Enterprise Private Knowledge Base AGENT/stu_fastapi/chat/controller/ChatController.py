import json
import time

from starlette.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from chat.service import ChatService
from fastapi import APIRouter, Request

chat_router = APIRouter()
templates = Jinja2Templates(directory="templates")


# 非流式聊天
@chat_router.get("/chatNoStream")
def chat_no_stream(question):
    return ChatService.chat_no_stream(question)


# 流式聊天
@chat_router.get("/chatStream")
def chat_stream(question, history_id):
    """
        StreamingResponse：流式输出对象，参数：
        1、生成器对象
        2、媒体类型 --- 不同的返回类型数据值不一样
    """
    def generator():
        for chunk in ChatService.chat_stream(question, history_id):
            if chunk:
                # 返回生成器对象
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        # 响应结束
        yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
    return StreamingResponse(
        content=generator(),
        media_type="text/event-stream"
    )


# 访问chat_no_stream.html
@chat_router.get("/goChatNoStream", response_class=HTMLResponse)
def go_chat_no_stream(request: Request):
    # request：请求对象
    # name：访问页面的名字，从templates开始算路径
    return templates.TemplateResponse(request, "chat_no_stream.html")

# 访问chat_stream.html
@chat_router.get("/goChatStream", response_class=HTMLResponse)
def go_chat_stream(request: Request):
    # request：请求对象
    # name：访问页面的名字，从templates开始算路径
    return templates.TemplateResponse(request, "chat_stream.html")

# 创建新对话
@chat_router.post("/createNewChat")
def create_new_chat(user_id):
    return ChatService.create_new_chat(user_id)

