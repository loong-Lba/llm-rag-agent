# 接口定义的文件
from users.entity.Users import Users
from users.service import UsersService
from fastapi import APIRouter

# 子路由对象
api_router = APIRouter()


# 登录
@api_router.post("/login")  # 子路由
def login(users: Users):
    return UsersService.login(users)


# 注册
@api_router.post("/register")
def register(users: Users):
    return UsersService.register(users)
