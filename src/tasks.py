import os
import json
import sqlite3
from celery import Celery
from database import init_db, DB_PATH

# Host (tu PC): Redis está mapeado a 6380 (según tu docker ps)
# Docker (worker): Redis es redis:6379
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6380")

celery_app = Celery(
    "turnos_final",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

# Para este proyecto NO necesitamos guardar resultados en backend (evita errores y dependencias)
celery_app.conf.task_ignore_result = True


def _conn():
    init_db()
    return sqlite3.connect(DB_PATH)


@celery_app.task(name="persist_event")
def persist_event(event_type: str, payload: dict) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events(event_type, payload) VALUES (?, ?)",
        (event_type, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


@celery_app.task(name="persist_ticket")
def persist_ticket(ticket_id: int, tramite: str, client_name: str) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO tickets(ticket_id, tramite, client_name) VALUES (?, ?, ?)",
        (ticket_id, tramite, client_name),
    )
    conn.commit()
    conn.close()


@celery_app.task(name="persist_session_start")
def persist_session_start(session_id: str, ticket_id: int, operator_name: str, client_name: str, tramite: str) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO sessions(session_id, ticket_id, operator_name, client_name, tramite, ended_at, ended_reason)
        VALUES (?, ?, ?, ?, ?, NULL, NULL)
        """,
        (session_id, ticket_id, operator_name, client_name, tramite),
    )
    conn.commit()
    conn.close()


@celery_app.task(name="persist_message")
def persist_message(session_id: str, sender_role: str, sender_name: str, text: str) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages(session_id, sender_role, sender_name, text) VALUES (?, ?, ?, ?)",
        (session_id, sender_role, sender_name, text),
    )
    conn.commit()
    conn.close()


@celery_app.task(name="persist_session_end")
def persist_session_end(session_id: str, ended_reason: str) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE sessions SET ended_at=CURRENT_TIMESTAMP, ended_reason=? WHERE session_id=?",
        (ended_reason, session_id),
    )
    conn.commit()
    conn.close()
