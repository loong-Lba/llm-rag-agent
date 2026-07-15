from common import MySQLUtil


# 创建新对话（空）
def create_new_chat(user_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        sql = "INSERT INTO `history` VALUES(NULL, %s, %s, now(), %s, %s)"
        cur.execute(sql, ['', '', 0, user_id])      # 先占位，之后再用updateHistoryById填充数据库
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(e)
        conn.rollback()
        return None





# 查根记录、所有子记录，并按照时间顺序返回
def find_history_for_context(history_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    sql = "SELECT `question`, `answer`FROM `history`WHERE `history_id`=%s OR `parent_id`=%sORDER BY `create_time` ASC, `history_id` ASC"
    cur.execute(sql, [history_id, history_id])
    result = cur.fetchall()
    MySQLUtil.mysql_close(cur, conn)
    return result
