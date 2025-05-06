import socket
import threading
from servidor.gestor_colas import GestorColas

# Configuración
HOST = '127.0.0.1'
PORT = 65432

# Crear instancia de GestorColas
gestor_colas = GestorColas()

def manejar_cliente(conn, addr):
    print(f"[+] Nueva conexión desde {addr}")

    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break

            print(f"[{addr}] Mensaje recibido: {data}")

            # Parseo simple: esperamos mensajes tipo "SOLICITAR:Pago" o "ATENDER"
            if data.startswith("SOLICITAR:"):
                tipo_tramite = data.split(":")[1]
                turno = gestor_colas.solicitar_turno(tipo_tramite)
                conn.sendall(f"Tu turno es: {turno}".encode('utf-8'))

            elif data == "ATENDER":
                turno = gestor_colas.obtener_siguiente_turno()
                if turno:
                    conn.sendall(f"Atendiendo turno: {turno}".encode('utf-8'))
                else:
                    conn.sendall("No hay turnos en la cola.".encode('utf-8'))
            else:
                conn.sendall("Comando no reconocido.".encode('utf-8'))

    except Exception as e:
        print(f"[!] Error con {addr}: {e}")

    finally:
        conn.close()
        print(f"[-] Conexión cerrada con {addr}")


def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[*] Servidor escuchando en {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            hilo = threading.Thread(target=manejar_cliente, args=(conn, addr))
            hilo.start()
            print(f"[~] Número de hilos activos: {threading.active_count() - 1}")


if __name__ == "__main__":
    iniciar_servidor()
