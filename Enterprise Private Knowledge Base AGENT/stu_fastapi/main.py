from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from chat.controller.ChatController import chat_router
from chat.controller.HistoryController import history_router
from users.controller.UsersController import api_router

# 创建FastAPI对象
app = FastAPI()

# 访问静态资源放行
app.mount("/static", app=StaticFiles(directory="static"), name="static")

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "欢迎使用FastAPI应用",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "users": "/users (用户管理)",
            "chat": "/chat (AI聊天)",
            "chat_ui": "/chat/goChatNoStream (聊天界面)"
        }
    }

# 引入users模块的子路由
"""
    include_router 方法参数：
        1、router：引入的子路由 --- 子路由的名字APIRouter对象的名字
        2、prefix：访问子路由的时候添加在前面的前缀
        3、tags：在swaggerUI中分组的名字
"""
app.include_router(router=api_router, prefix="/users", tags=["users"])
# 注册chat模块
app.include_router(router=chat_router, prefix="/chat", tags=["chat"])
# 注册history模块
app.include_router(router=history_router, prefix="/history", tags=["history"])



# 运行FastAPI
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        # host="192.168.2.81",
        port=8001,
        reload=False,
    )
