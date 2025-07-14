import sqlite3
from datetime import datetime

DB_PATH = 'turnos.db'

# Inicializa la base de datos y la tabla si no existen
def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
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
    ''')
    conn.commit()
    conn.close()

# Guarda un turno atendido en la base de datos
def guardar_turno(cliente_id, nombre, tramite, prioridad, admin_id, conversacion=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO turnos_atendidos (cliente_id, nombre, tramite, prioridad, admin_id, timestamp, conversacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (cliente_id, nombre, tramite, prioridad, admin_id, timestamp, conversacion))
    conn.commit()
    conn.close() 