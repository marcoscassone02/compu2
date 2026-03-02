import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db import inicializar_db, guardar_turno


def run_db_worker(db_queue):
    """
    Proceso dedicado: lee tareas desde db_queue y escribe en SQLite.
    IPC real: multiprocessing.Queue
    """
    inicializar_db()
    while True:
        item = db_queue.get()
        if item is None:  
            break
        try:
            guardar_turno(**item)
        except Exception as e:
            print(f"[DB_WORKER] Error guardando turno: {e}")