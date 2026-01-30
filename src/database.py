import sqlite3
from pathlib import Path

DB_PATH = Path("../db/data.sqlite3")

def init_db():
    # ✅ asegura que exista la carpeta donde va la DB
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
      CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY,
        tramite TEXT NOT NULL,
        client_name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    """)

    cur.execute("""
      CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        ticket_id INTEGER NOT NULL,
        operator_name TEXT NOT NULL,
        client_name TEXT NOT NULL,
        tramite TEXT NOT NULL,
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ended_at DATETIME,
        ended_reason TEXT
      )
    """)

    cur.execute("""
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        sender_role TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        text TEXT NOT NULL,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    """)

    cur.execute("""
      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    """)

    conn.commit()
    conn.close()
