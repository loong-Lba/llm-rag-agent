from common import MySQLUtil


def find_history_by_user_id(user_id):
    #获取连接对象
    conn = MySQLUtil.mysql_conn()
    #获取游标对象
    cur = conn.cursor()
    #SQL
    sql = "SELECT h.* FROM `history` h LEFT JOIN `users` u ON h.history_fk_users=u.id WHERE u.id=%s AND `parent_id`=0;"
    #执行
    cur.execute(sql, [user_id])
    # 获取结果
    result = cur.fetchall()
    return result

# 获取完整的对话记录
def find_history_by_id(history_id):
    # 获取连接对象
    conn = MySQLUtil.mysql_conn()
    # 获取游标对象
    cur = conn.cursor()
    # SQL
    sql = "SELECT `question`, `answer` FROM `history` WHERE `history_id`=%s OR `parent_id`=%s;"
    # 执行
    cur.execute(sql, [history_id, history_id])
    # 获取结果
    result = cur.fetchall()
    MySQLUtil.mysql_close(cur, conn)
    return result

if __name__ == '__main__':
    print(find_history_by_id(1))

# 保存继续对话的结果
def open_history_save_data(history):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        sql = "INSERT INTO `history` VALUES(NULL, %s,%s, now(),%s,%s)"
        cur.execute(sql, [history.question,history.answer,history.parentId,history.userId])
        conn.commit()  # 提交事务--------向数据库中写入这条数据
        return True
    except Exception as e:
        print(e)
        conn.rollback()     # 回滚事务 ---撤销数据库
        return False


# 删除历史对话记录（删除相同的history_id和他的儿子记录）
def delete_history_by_root_id(history_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        sql = "DELETE FROM `history` WHERE `history_id`=%s OR `parent_id`=%s;"
        cur.execute(sql, [history_id, history_id])
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False

# 第一次输入问题，ai回答后，更新这个空对话
def update_history_by_id(history_id, question, answer):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        sql = "UPDATE `history` SET `question`=%s, `answer`=%s WHERE `history_id`=%s"
        cur.execute(sql, [question, answer, history_id])
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False

# 查询当前整段对话历史
def find_history_for_context(history_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        sql = """
           SELECT `question`, `answer`
           FROM `history`
           WHERE `history_id` = %s OR `parent_id` = %s
           ORDER BY `create_time` ASC, `history_id` ASC
           """
        cur.execute(sql, [history_id, history_id])
        result = cur.fetchall()
        MySQLUtil.mysql_close(cur, conn)
        return result
    except Exception as e:
        print(e)
        MySQLUtil.mysql_close(cur, conn)
        return []

