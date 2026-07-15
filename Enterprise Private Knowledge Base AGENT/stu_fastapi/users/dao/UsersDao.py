# 操作数据库的文件
from common import MySQLUtil


# 根据用户名查询用户信息
def find_users_by_username(username):
    # 获取连接对象
    conn = MySQLUtil.mysql_conn()
    # 获取游标对象
    cur = conn.cursor()
    # SQL
    sql = "select * from `users` where `username`=%s"
    # 执行
    cur.execute(sql, [username])
    # 获取结果
    result = cur.fetchall()
    # 关闭连接
    MySQLUtil.mysql_close(cur, conn)
    # 返回结果
    return result


# 插入新用户
def insert_user(username, password):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        sql = "insert into `users` (`username`, `password`) values (%s, %s)"
        cur.execute(sql, [username, password])
        conn.commit()
        user_id = cur.lastrowid
        return user_id
    except Exception as e:
        conn.rollback()
        print("注册用户失败：", e)
        return None
    finally:
        MySQLUtil.mysql_close(cur, conn)


if __name__ == '__main__':
    print(find_users_by_username("cc"))


