import queue
import time

class GestorColas:
    def __init__(self):
        self.cola = queue.PriorityQueue()
        self.contador = 0  

    def agregar_turno(self, prioridad, tramite, cliente_id, nombre, conn, addr):
        self.contador += 1
        timestamp = time.time()
        self.cola.put((prioridad, self.contador, tramite, cliente_id, nombre, conn, addr, timestamp))

    def obtener_turno(self):
        if self.cola.empty():
            return None
        turnos = []
        while not self.cola.empty():
            turnos.append(self.cola.get())
        now = time.time()
        turnos_actualizados = []
        for t in turnos:
            prioridad, contador, tramite, cliente_id, nombre, conn, addr, timestamp = t
            espera = now - timestamp
            if espera >= 30 and prioridad > 1:
                prioridad -= 1
                
                timestamp = now
            turnos_actualizados.append((prioridad, contador, tramite, cliente_id, nombre, conn, addr, timestamp))
       
        for t in turnos_actualizados:
            self.cola.put(t)
        
        if not self.cola.empty():
            return self.cola.get()
        return None
