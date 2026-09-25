import sqlite3
from pathlib import Path

DB_PATH = Path("bot.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            free_used INTEGER DEFAULT 0,
            blocked INTEGER DEFAULT 0,
            vip INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        db.commit()

def save_user(user):
    with connect() as db:
        db.execute("""INSERT INTO users(user_id, username)
        VALUES(?, ?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username""",
        (user.id, user.username or ""))
        db.commit()

def get_user(user_id):
    with connect() as db:
        return db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

def is_allowed(user_id):
    row = get_user(user_id)
    return bool(row and not row["blocked"])

def can_download(user_id):
    row = get_user(user_id)
    if not row or row["blocked"]:
        return False
    return bool(row["vip"] or row["free_used"] < 3)

def increase_free_used(user_id):
    with connect() as db:
        db.execute("UPDATE users SET free_used=free_used+1 WHERE user_id=?", (user_id,))
        db.commit()

def set_vip(user_id, value=1):
    with connect() as db:
        db.execute("UPDATE users SET vip=? WHERE user_id=?", (value, user_id))
        db.commit()

def set_blocked(user_id, value=1):
    with connect() as db:
        db.execute("UPDATE users SET blocked=? WHERE user_id=?", (value, user_id))
        db.commit()

def stats():
    with connect() as db:
        return db.execute("""SELECT COUNT(*) total,
        COALESCE(SUM(vip),0) vip,
        COALESCE(SUM(blocked),0) blocked FROM users""").fetchone()
