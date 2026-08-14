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
    MySQLUtil.mysql_close(cur, conn)
    return result

# 获取完整的对话记录
def find_history_by_id(history_id):
    # 获取连接对象
    conn = MySQLUtil.mysql_conn()
    # 获取游标对象
    cur = conn.cursor()
    # SQL
    sql = """
        SELECT `history_id`, `question`, `answer`, `rag_metadata`
        FROM `history`
        WHERE `history_id`=%s OR `parent_id`=%s
        ORDER BY `create_time` ASC, `history_id` ASC
    """
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
        sql = """
            INSERT INTO `history`
                (`question`, `answer`, `create_time`, `parent_id`, `history_fk_users`, `rag_metadata`)
            VALUES (%s, %s, NOW(), %s, %s, %s)
        """
        cur.execute(sql, [history.question, history.answer, history.parentId, history.userId, None])
        conn.commit()  # 提交事务--------向数据库中写入这条数据
        return True
    except Exception as e:
        print(e)
        conn.rollback()     # 回滚事务 ---撤销数据库
        return False
    finally:
        MySQLUtil.mysql_close(cur, conn)


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
    finally:
        MySQLUtil.mysql_close(cur, conn)

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
    finally:
        MySQLUtil.mysql_close(cur, conn)

def root_history_exists(history_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT 1 FROM `history` WHERE `history_id` = %s AND `parent_id` = 0",
            [history_id],
        )
        return cur.fetchone() is not None
    finally:
        MySQLUtil.mysql_close(cur, conn)


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
        return cur.fetchall()
    except Exception as e:
        print(e)
        return []
    finally:
        MySQLUtil.mysql_close(cur, conn)


def find_exchange_by_request_id(history_id, request_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT `history_id`, `answer`, `rag_metadata`
            FROM `history`
            WHERE (`history_id` = %s OR `parent_id` = %s)
              AND JSON_UNQUOTE(JSON_EXTRACT(IF(JSON_VALID(`rag_metadata`), `rag_metadata`, NULL), '$.requestId')) = %s
            LIMIT 1
            """,
            [history_id, history_id, request_id],
        )
        return cur.fetchone()
    finally:
        MySQLUtil.mysql_close(cur, conn)


def save_chat_exchange(history_id, question, answer, rag_metadata, request_id):
    conn = MySQLUtil.mysql_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT `history_id`, `question`, `answer`, `history_fk_users`
            FROM `history`
            WHERE `history_id` = %s AND `parent_id` = 0
            FOR UPDATE
            """,
            [history_id],
        )
        root = cur.fetchone()
        if not root:
            raise ValueError("会话不存在")

        cur.execute(
            """
            SELECT `history_id`
            FROM `history`
            WHERE (`history_id` = %s OR `parent_id` = %s)
              AND JSON_UNQUOTE(JSON_EXTRACT(IF(JSON_VALID(`rag_metadata`), `rag_metadata`, NULL), '$.requestId')) = %s
            LIMIT 1
            """,
            [history_id, history_id, request_id],
        )
        existing = cur.fetchone()
        if existing:
            conn.commit()
            return existing["history_id"]

        if not (root.get("question") or "").strip() and not (root.get("answer") or "").strip():
            cur.execute(
                """
                UPDATE `history`
                SET `question` = %s, `answer` = %s, `rag_metadata` = %s
                WHERE `history_id` = %s
                """,
                [question, answer, rag_metadata, history_id],
            )
            record_id = int(history_id)
        else:
            cur.execute(
                """
                INSERT INTO `history`
                    (`question`, `answer`, `create_time`, `parent_id`, `history_fk_users`, `rag_metadata`)
                VALUES (%s, %s, NOW(), %s, %s, %s)
                """,
                [question, answer, history_id, root["history_fk_users"], rag_metadata],
            )
            record_id = cur.lastrowid

        conn.commit()
        return record_id
    except Exception:
        conn.rollback()
        raise
    finally:
        MySQLUtil.mysql_close(cur, conn)

