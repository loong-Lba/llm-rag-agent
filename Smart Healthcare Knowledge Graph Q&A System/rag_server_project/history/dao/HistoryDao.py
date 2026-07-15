import pymysql


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "rag_server_project",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def ensure_tables():
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_session (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(64) NOT NULL,
                title VARCHAR(255) NOT NULL DEFAULT '新对话',
                last_question TEXT NULL,
                last_answer_preview TEXT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_message (
                id INT PRIMARY KEY AUTO_INCREMENT,
                session_id INT NOT NULL,
                role VARCHAR(32) NOT NULL,
                content TEXT NOT NULL,
                route_type VARCHAR(64) NULL,
                retrieval_used TINYINT(1) NOT NULL DEFAULT 0,
                tool_name VARCHAR(64) NULL,
                tool_input TEXT NULL,
                tool_output TEXT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chat_message_session_id (session_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def create_session(user_id, title="新对话"):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO chat_session (user_id, title) VALUES (%s, %s)",
            [user_id, title],
        )
        conn.commit()
        session_id = cur.lastrowid
        return find_session_by_id(session_id)
    finally:
        cur.close()
        conn.close()


def find_sessions_by_user_id(user_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, user_id, title, last_question, last_answer_preview, created_at, updated_at
            FROM chat_session
            WHERE user_id=%s
            ORDER BY updated_at DESC, id DESC
            """,
            [user_id],
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def find_session_by_id(session_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, user_id, title, last_question, last_answer_preview, created_at, updated_at
            FROM chat_session
            WHERE id=%s
            """,
            [session_id],
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def update_session_summary(session_id, title, last_question, last_answer_preview):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE chat_session
            SET title=%s,
                last_question=%s,
                last_answer_preview=%s,
                updated_at=NOW()
            WHERE id=%s
            """,
            [title, last_question, last_answer_preview, session_id],
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def save_message(session_id, role, content, route_type=None, retrieval_used=False, tool_name=None, tool_input=None, tool_output=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO chat_message (session_id, role, content, route_type, retrieval_used, tool_name, tool_input, tool_output)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [session_id, role, content, route_type, int(bool(retrieval_used)), tool_name, tool_input, tool_output],
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def find_messages_by_session_id(session_id, limit=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        if limit:
            cur.execute(
                """
                SELECT * FROM (
                    SELECT id, session_id, role, content, route_type, retrieval_used, tool_name, tool_input, tool_output, created_at
                    FROM chat_message
                    WHERE session_id=%s
                    ORDER BY id DESC
                    LIMIT %s
                ) t ORDER BY id ASC
                """,
                [session_id, limit],
            )
        else:
            cur.execute(
                """
                SELECT id, session_id, role, content, route_type, retrieval_used, tool_name, tool_input, tool_output, created_at
                FROM chat_message
                WHERE session_id=%s
                ORDER BY id ASC
                """,
                [session_id],
            )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def delete_session(session_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM chat_message WHERE session_id=%s", [session_id])
        cur.execute("DELETE FROM chat_session WHERE id=%s", [session_id])
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()
