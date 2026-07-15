# 逻辑处理文件 --- 核心实现功能代码的位置
from users.dao import UsersDao


# 登录
def login(users):
    username = users.username
    password = users.password
    # 判断账号和密码是否为空
    if not (username and password):
        return {"code": 500, "msg": "账号或密码不能为空", "data": None}
    # 根据用户名查询用户信息
    result = UsersDao.find_users_by_username(username)
    if not result:
        return {"code": 500, "msg": "账号不存在", "data": None}
    # 判断密码
    if password != result[0]["password"]:
        return {"code": 500, "msg": "密码错误", "data": None}
    # 登录成功
    return {"code": 200, "msg": "登录成功", "data": result[0]['id']}

# 注册
def register(users):
    username = users.username
    password = users.password

    if not (username and password):
        return {"code": 500, "msg": "用户名或密码不能为空", "data": None}

    result = UsersDao.find_users_by_username(username)
    if result:
        return {"code": 500, "msg": "用户名已存在", "data": None}

    user_id = UsersDao.insert_user(username, password)
    if not user_id:
        return {"code": 500, "msg": "注册失败", "data": None}

    return {"code": 200, "msg": "注册成功", "data": user_id}
