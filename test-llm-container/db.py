import sqlite3
import datetime as dt

DB_PATH = "app.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        is_active INTEGER NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
    conn.commit()
    conn.close()

def create_session(session_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions(session_id, created_at, is_active) VALUES(?,?,1)",
        (session_id, dt.datetime.utcnow().isoformat() + "Z"),
    )
    conn.commit()
    conn.close()

def session_is_active(session_id: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT is_active FROM sessions WHERE session_id=?",
        (session_id,),
    ).fetchone()
    conn.close()
    return bool(row["is_active"]) if row else False

def end_session(session_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE sessions SET is_active=0 WHERE session_id=?", (session_id,))
    conn.commit()
    conn.close()

def add_message(session_id: str, role: str, content: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages(session_id, role, content, created_at) VALUES(?,?,?,?)",
        (session_id, role, content, dt.datetime.utcnow().isoformat() + "Z"),
    )
    conn.commit()
    conn.close()

def get_history(session_id: str, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()
    rows = list(reversed(rows))
    return [{"role": r["role"], "content": r["content"]} for r in rows]
