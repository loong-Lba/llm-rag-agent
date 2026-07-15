# 封装数据库连接、关闭的工具
import pymysql


# 获取连接
def mysql_conn():
    return pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="root",
        database="feifan_ai",
        charset="utf8mb4",
        # 获取字典数据类型
        cursorclass=pymysql.cursors.DictCursor
    )


# 关闭连接
def mysql_close(cur, conn):
    cur.close()
    conn.close()
