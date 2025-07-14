import queue

class GestorColas:
    def __init__(self):
        self.cola = queue.PriorityQueue()
        self.contador = 0  # Para desempatar turnos con misma prioridad

    def agregar_turno(self, prioridad, tramite, cliente_id, conn, addr):
        self.contador += 1
        # Guardar también la conexión y la dirección
        self.cola.put((prioridad, self.contador, tramite, cliente_id, conn, addr))

    def obtener_turno(self):
        if not self.cola.empty():
            return self.cola.get()
        return None
