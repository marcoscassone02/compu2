import socket
import argparse
import threading
import select
import sys


def elegir_tramite():
    print("Seleccione el tipo de trámite:")
    print("1. Pago")
    print("2. Reclamo")
    print("3. Consulta")
    while True:
        opcion = input("Ingrese el número de la opción: ")
        if opcion == "1":
            return "pago"
        elif opcion == "2":
            return "reclamo"
        elif opcion == "3":
            return "consulta"
        else:
            print("Opción inválida. Intente de nuevo.")


def escuchar_mensajes(s: socket.socket, done: threading.Event):
    while not done.is_set():
        try:
            respuesta = s.recv(1024).decode(errors="ignore")
            if not respuesta:
                print("\n[Servidor desconectado]")
                done.set()
                break

            print(f"\n{respuesta.strip()}")
            if respuesta.strip().upper() == "FIN":
                print("[La conversación ha finalizado]")
                done.set()
                break

        except Exception as e:
            print(f"\n[Error de conexión: {e}]")
            done.set()
            break

    try:
        s.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        s.close()
    except Exception:
        pass


def enviar_mensajes(s: socket.socket, done: threading.Event):
    print("(Escribí mensajes. Para terminar: FIN)")
    while not done.is_set():
        r, _, _ = select.select([sys.stdin], [], [], 0.2)
        if done.is_set():
            break

        if r:
            mensaje_cliente = sys.stdin.readline()
            if not mensaje_cliente:  # EOF
                done.set()
                break

            mensaje_cliente = mensaje_cliente.rstrip("\n")
            try:
                s.sendall(mensaje_cliente.encode())
            except Exception:
                done.set()
                break

            if mensaje_cliente.strip().upper() == "FIN":
                done.set()
                break


def main():
    parser = argparse.ArgumentParser(description="Cliente de turnos")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--name", help="Nombre del cliente")
    parser.add_argument("--tramite", choices=["pago", "reclamo", "consulta"], help="Tipo de trámite")
    args = parser.parse_args()

    nombre = args.name or input("Ingrese su nombre: ")
    tramite = args.tramite or elegir_tramite()

    s = None
    try:
        s = socket.create_connection((args.host, args.port))

        mensaje = f"nombre:{nombre};tramite:{tramite}"
        s.sendall(mensaje.encode())

        # Recibe ID
        cliente_id_msg = s.recv(1024).decode(errors="ignore")
        if cliente_id_msg.startswith("CLIENTE_ID:"):
            cliente_id = cliente_id_msg.split(":", 1)[1].strip()
            print(f"Su identificador de cliente es: {cliente_id}")
        else:
            print("No se recibió un identificador de cliente válido del servidor.")
            return

        done = threading.Event()
        t = threading.Thread(target=escuchar_mensajes, args=(s, done), daemon=True)
        t.start()

        enviar_mensajes(s, done)
        print("[Fin de la sesión de cliente]")

    except Exception as e:
        print(f"\n[Cliente] No se pudo conectar a {args.host}:{args.port} -> {e}")
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()