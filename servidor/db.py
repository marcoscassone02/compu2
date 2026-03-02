import os
import sqlite3
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))          
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))    
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


DB_PATH = os.path.join(DATA_DIR, "turnos.db")


def inicializar_db():
    # Asegura que exista /data
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS turnos_atendidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tramite TEXT NOT NULL,
            prioridad INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            conversacion TEXT
        )
    """)
    conn.commit()
    conn.close()


def guardar_turno(cliente_id, nombre, tramite, prioridad, admin_id, conversacion=None):
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO turnos_atendidos (cliente_id, nombre, tramite, prioridad, admin_id, timestamp, conversacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (cliente_id, nombre, tramite, prioridad, admin_id, timestamp, conversacion))
    conn.commit()
    conn.close()