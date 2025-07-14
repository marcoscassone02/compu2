import socket
import threading
import argparse
from gestor_colas import GestorColas

PRIORIDADES = {
    "pago": 1,
    "reclamo": 2,
    "consulta": 3
}

cliente_id_counter = 0
cliente_id_lock = threading.Lock()

def handle_client(conn, addr, gestor_colas):
    global cliente_id_counter
    try:
        data = conn.recv(1024).decode()
        if not data:
            return
        # Espera: "tramite:<tipo_tramite>"
        partes = dict(x.split(":") for x in data.strip().split(";") if ":" in x)
        tramite = partes.get("tramite")
        prioridad = PRIORIDADES.get(tramite, 3)
        # Asignar cliente_id incremental de forma segura
        with cliente_id_lock:
            cliente_id_counter += 1
            cliente_id = str(cliente_id_counter)
        # Enviar el cliente_id al cliente
        conn.sendall(f"CLIENTE_ID:{cliente_id}\n".encode())
        # Pasar conn y addr a la cola junto con el cliente_id
        gestor_colas.agregar_turno(prioridad, tramite, cliente_id, conn, addr)
        # No cerrar la conexión aquí, la usará el administrativo
    except Exception as e:
        try:
            conn.sendall(f"Error: {e}\n".encode())
        except:
            pass
        conn.close()

# Conversación interactiva entre administrativo y cliente
def administrativo(gestor_colas, admin_id):
    while True:
        turno = gestor_colas.obtener_turno()
        if turno:
            prioridad, _, tramite, cliente_id, conn, addr = turno
            print(f"[ADMIN {admin_id}] Atendiendo turno de {tramite} (cliente {cliente_id}, prioridad {prioridad})")
            try:
                conn.sendall(f"Usted está siendo atendido por el administrativo {admin_id}. Puede comenzar a conversar.\n".encode())
                while True:
                    # Recibir mensaje del cliente
                    try:
                        mensaje_cliente = conn.recv(1024).decode().strip()
                    except:
                        print(f"[ADMIN {admin_id}] El cliente se desconectó.")
                        break
                    if not mensaje_cliente:
                        print(f"[ADMIN {admin_id}] El cliente se desconectó.")
                        break
                    print(f"[ADMIN {admin_id}] Cliente {cliente_id}: {mensaje_cliente}")
                    # Si el cliente escribe 'FIN', terminar la conversación
                    if mensaje_cliente.strip().upper() == "FIN":
                        print(f"[ADMIN {admin_id}] El cliente {cliente_id} finalizó la conversación.")
                        conn.sendall("FIN".encode())
                        break
                    # El administrativo responde
                    respuesta = input(f"[ADMIN {admin_id}] Escriba su respuesta (o 'FIN' para terminar): ")
                    conn.sendall(respuesta.encode())
                    if respuesta.strip().upper() == "FIN":
                        print(f"[ADMIN {admin_id}] Conversación finalizada con cliente {cliente_id}.")
                        break
            except Exception as e:
                print(f"[ADMIN {admin_id}] Error en la conversación: {e}")
            finally:
                conn.close()
        else:
            import time
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="Servidor de turnos")
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    gestor_colas = GestorColas()

    # Lanzar 3 hilos administrativos
    admin_threads = []
    for i in range(3):
        t = threading.Thread(target=administrativo, args=(gestor_colas, i+1), daemon=True)
        t.start()
        admin_threads.append(t)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.host, args.port))
    server.listen()
    print(f"Servidor escuchando en {args.host}:{args.port}")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr, gestor_colas))
            thread.start()
    except KeyboardInterrupt:
        print("Servidor detenido.")

if __name__ == "__main__":
    main()
