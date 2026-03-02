import socket
import argparse
import threading
import select
import sys


def escuchar_mensajes(s: socket.socket, stop: threading.Event, in_session: threading.Event):
    """
    - stop: termina el programa administrativo (SALIR / Ctrl+C)
    - in_session: indica si el admin está atendiendo a un cliente
    """
    while not stop.is_set():
        try:
            server_msg = s.recv(1024).decode(errors="ignore")
            if not server_msg:
                print("\n[Servidor desconectado]")
                stop.set()
                break

            msg = server_msg.strip()
            if msg:
                print(f"\n{msg}")

            if msg.startswith("Atendiendo a Cliente"):
                in_session.set()

            if msg.upper() == "FIN":
                in_session.clear()
                print("[Conversación finalizada. Quedás disponible para otro turno.]")
                continue

        except Exception as e:
            print(f"\n[Error de conexión: {e}]")
            stop.set()
            break

    try:
        s.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    try:
        s.close()
    except Exception:
        pass


def enviar_mensajes(s: socket.socket, stop: threading.Event, in_session: threading.Event):
    """
    - Permite escribir mensajes.
    - FIN: cierra sesión actual, pero el admin queda activo.
    - SALIR o /exit: cierra el programa administrativo.
    """
    print("(Escribí mensajes. FIN termina la conversación. SALIR (/exit) cierra el admin.)")

    while not stop.is_set():
        r, _, _ = select.select([sys.stdin], [], [], 0.2)
        if stop.is_set():
            break

        if r:
            line = sys.stdin.readline()
            if not line:  
                stop.set()
                break

            msg = line.rstrip("\n")
            if not msg:
                continue

            if msg.strip().lower() in ("salir", "/exit"):
                stop.set()
                break

            if msg.strip().upper() == "FIN":
                try:
                    s.sendall(msg.encode())
                except Exception:
                    stop.set()
                    break
                in_session.clear()
                print("[FIN enviado. Esperando nuevo turno...]")
                continue

            try:
                s.sendall(msg.encode())
            except Exception:
                stop.set()
                break


def main():
    parser = argparse.ArgumentParser(description="Administrativo de Turnos")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--admin_id", required=True)
    args = parser.parse_args()

    s = None
    try:
        s = socket.create_connection((args.host, args.port))
        s.sendall(f"ADMIN_LOGIN:{args.admin_id}".encode())

        stop = threading.Event()
        in_session = threading.Event()

        t_escuchar = threading.Thread(
            target=escuchar_mensajes,
            args=(s, stop, in_session),
            daemon=True,
        )
        t_escuchar.start()

        enviar_mensajes(s, stop, in_session)
        print("[Fin de la sesión administrativa]")

    except KeyboardInterrupt:
        print("\n[Admin] Interrumpido por usuario.")
    except Exception as e:
        print(f"\n[Admin] No se pudo conectar a {args.host}:{args.port} -> {e}")
    finally:
        if s is not None:
            try:
                s.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()