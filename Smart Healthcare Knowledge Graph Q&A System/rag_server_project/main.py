# 导入FastAPI
from fastapi import FastAPI
import uvicorn
# 导入子路由
from .users.controller.UsersController import users_router
from .chat.controller.ChatController import chat_router
from .history.controller.HistoryController import history_router
# 导入异步上下文管理器
from contextlib import asynccontextmanager
from .ai import LoadAgent
from fastapi.middleware.cors import CORSMiddleware
"""
    fastapi启动和关闭执行，函数yield之前的代码在启动的时候执行、之后的代码在关闭的时候执行
"""
# fastapi启动和关闭执行
@asynccontextmanager
async def on_start(app:FastAPI):
    # 向fastapi对象中的state属性里面设置一个值---agent对象
    app.state.agent = LoadAgent.load_agent()
    print("FastAPI服务器启动了，创建了agent对象")
    print(app.state.agent)
    yield
    # 关闭agent对象
    app.state.agent = None
    print("FastAPI服务器启动了，关闭了agent对象")
    # 创建FastAPI实例 --- 对象
app = FastAPI(lifespan=on_start)
"""
    注册子路由 include_router 方法，参数：
        1、子路由名字
        2、prefix：前缀，即访问子路由的时候需要把这个前缀添加在请求地址里面
        比如子路由配置的是test，请求地址就是---http://localhost:8000/users/test
        3、tags：在swagger ui中用这个名字做分类
"""
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(history_router, prefix="/history", tags=["history"])

#配置跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],   # 允许的源
    allow_credentials=True,     # 允许携带cookie
    allow_methods=["*"],        # 允许的请求方法
    allow_headers=["*"],        # 允许的请求头
)


# 配置FastAPI项目启动 --- 这里的启动是运行整个服务器项目
if __name__ == '__main__':
    uvicorn.run(
        app="rag_server_project.main:app",  # 启动的FastAPI实例
        host="127.0.0.1",  # 启动的IP地址
        port=8000,  # 启动的端口号
        reload=False,  # 不允许重新加载
    )
