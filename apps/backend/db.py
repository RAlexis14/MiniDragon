import os, sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo   # ← zona horaria
from config import Settings

cfg = Settings()
EC_TZ = ZoneInfo("America/Guayaquil")

def now_iso():
    return datetime.now(EC_TZ).isoformat()  # ← hora de Ecuador

def get_conn():
    os.makedirs(os.path.dirname(cfg.DB_FILE), exist_ok=True)
    conn = sqlite3.connect(cfg.DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS search_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL,
          query TEXT NOT NULL,
          results_count INTEGER NOT NULL,
          sample_names TEXT,
          created_at TEXT NOT NULL
        );""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_search_user ON search_logs(username, id DESC);")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS view_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL,
          character_id TEXT,
          character_name TEXT NOT NULL,
          created_at TEXT NOT NULL
        );""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_view_user ON view_logs(username, id DESC);")

def insert_search(username: str, query: str, results_count: int, sample_names_json: str):
    with get_conn() as conn:
        conn.execute("""
          INSERT INTO search_logs(username, query, results_count, sample_names, created_at)
          VALUES(?,?,?,?,?);
        """, (username, query, results_count, sample_names_json, now_iso()))

def last_logs(username: str, limit: int = 20):
    with get_conn() as conn:
        cur = conn.execute("""
          SELECT id, query, results_count, sample_names, created_at
          FROM search_logs
          WHERE username = ?
          ORDER BY id DESC
          LIMIT ?;
        """, (username, limit))
        return [dict(r) for r in cur.fetchall()]

def insert_view(username: str, character_id: str | None, character_name: str):
    with get_conn() as conn:
        conn.execute("""
          INSERT INTO view_logs(username, character_id, character_name, created_at)
          VALUES(?,?,?,?);
        """, (username, character_id, character_name, now_iso()))

def last_views(username: str, limit: int = 20):
    with get_conn() as conn:
        cur = conn.execute("""
          SELECT id, character_id, character_name, created_at
          FROM view_logs
          WHERE username = ?
          ORDER BY id DESC
          LIMIT ?;""", (username, limit))
        return [dict(r) for r in cur.fetchall()]
