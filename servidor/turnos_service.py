# servidor/turnos_service.py
import time
import heapq
from collections import deque


PRIORIDADES = {
    "pago": 1,
    "reclamo": 2,
    "consulta": 3
}


class TurnoQueue:
    """
    Cola de prioridad con aging simple:
    - Guardamos (prioridad, orden, cliente_id, nombre, tramite, timestamp)
    - Cada vez que pedimos turno, aplicamos aging si esperó >= aging_seconds:
      baja prioridad numérica (ej: 3->2->1) hasta min 1.
    """
    def __init__(self, aging_seconds=30):
        self.heap = []
        self.counter = 0
        self.aging_seconds = aging_seconds

    def push(self, cliente_id, nombre, tramite):
        prioridad = PRIORIDADES.get(tramite, 3)
        self.counter += 1
        ts = time.time()
        heapq.heappush(self.heap, [prioridad, self.counter, cliente_id, nombre, tramite, ts])

    def pop(self):
        if not self.heap:
            return None

        now = time.time()
        for item in self.heap:
            prioridad, orden, cliente_id, nombre, tramite, ts = item
            espera = now - ts
            if espera >= self.aging_seconds and prioridad > 1:
                item[0] = prioridad - 1
                item[5] = now  

        heapq.heapify(self.heap)
        prioridad, orden, cliente_id, nombre, tramite, ts = heapq.heappop(self.heap)
        return {
            "cliente_id": cliente_id,
            "nombre": nombre,
            "tramite": tramite,
            "prioridad": prioridad
        }


def run_turnos_service(q_to_turnos, q_to_proxy):
    """
    Proceso de turnos:
      - recibe eventos del proxy (nuevo cliente / admin disponible)
      - mantiene cola de turnos + cola de admins disponibles
      - emite eventos de asignación hacia el proxy
    """
    turnos = TurnoQueue(aging_seconds=30)
    admins = deque()  

    while True:
        evt = q_to_turnos.get() 
        if evt is None:
            break

        t = evt.get("type")

        if t == "ADMIN_READY":
            admin_id = evt["admin_id"]
            admins.append(admin_id)

        elif t == "NEW_TURNO":
            turnos.push(evt["cliente_id"], evt["nombre"], evt["tramite"])

        elif t == "ADMIN_DISCONNECTED":

            admin_id = evt["admin_id"]
            try:
                admins.remove(admin_id)
            except ValueError:
                pass


        while admins:
            turno = turnos.pop()
            if not turno:
                break
            admin_id = admins.popleft()
            q_to_proxy.put({
                "type": "ASSIGN",
                "admin_id": admin_id,
                **turno
            })