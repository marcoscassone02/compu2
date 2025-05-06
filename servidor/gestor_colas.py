import threading
from queue import PriorityQueue

class GestorColas:
    def __init__(self):
        # Diccionario de colas por tipo de trámite
        self.colas = {
            'Pago': PriorityQueue(),
            'Reclamo': PriorityQueue(),
            'Consulta': PriorityQueue(),
            'Fraude': PriorityQueue(),
        }
        self.contador_turnos = 0
        self.lock = threading.Lock()

    def solicitar_turno(self, tipo_tramite):
        with self.lock:
            self.contador_turnos += 1
            turno_id = f"{tipo_tramite[:3].upper()}-{self.contador_turnos}"
            # Aquí usamos prioridad simple (puedes mejorar esto)
            prioridad = self.obtener_prioridad(tipo_tramite)
            self.colas[tipo_tramite].put((prioridad, turno_id))
            print(f"[GestorColas] Turno agregado: {turno_id} con prioridad {prioridad}")
            return turno_id

    def obtener_siguiente_turno(self):
        with self.lock:
            for tipo, cola in self.colas.items():
                if not cola.empty():
                    _, turno_id = cola.get()
                    print(f"[GestorColas] Turno asignado: {turno_id}")
                    return turno_id
            return None

    def obtener_prioridad(self, tipo_tramite):
        prioridades = {
            'Pago': 2,
            'Reclamo': 1,
            'Consulta': 3,
            'Fraude': 0,  # Máxima prioridad
        }
        return prioridades.get(tipo_tramite, 5)  # 5 = prioridad más baja por defecto
