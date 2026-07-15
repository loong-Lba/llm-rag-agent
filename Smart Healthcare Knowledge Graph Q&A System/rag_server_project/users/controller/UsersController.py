# 配置子路由引入APIRouter
from fastapi import APIRouter, Request
from ..service import UsersService

# 创建子路由实例
users_router = APIRouter()

# 邮件登录
@users_router.get("/sendEmail")
def send_email(username: str, request: Request):
    # 获取agent对象
    agent = request.app.state.agent
    # 直接调用方法返回 --- send_email方法的返回值必须是json格式【在python中就是一个字典】
    return UsersService.send_email(username, agent)



# 验证码验证
@users_router.get("/verifyCode")
def verify_code(receiver: str, code: str, request: Request):
    agent = request.app.state.agent
    return UsersService.verify_code(receiver, code, agent)