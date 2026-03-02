# servidor/proxy_server.py
import os
import sys
import socket
import selectors
import argparse
import threading
from multiprocessing import Process, Queue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from protocol import parse_hello, build_client_id
from turnos_service import run_turnos_service
from db_worker import run_db_worker

PRIORIDADES = {"pago": 1, "reclamo": 2, "consulta": 3}


def main():
    parser = argparse.ArgumentParser(description="Proxy Server (selectors) - Turnos")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument(
        "--family",
        choices=["ipv4", "ipv6", "dual"],
        default="ipv4",
        help="Familia IP del servidor: ipv4, ipv6 o dual (IPv6 + IPv4-mapped si el SO lo permite)"
        )
    args = parser.parse_args()

    q_to_turnos = Queue()
    q_to_proxy = Queue()
    q_to_db = Queue()

    p_turnos = Process(target=run_turnos_service, args=(q_to_turnos, q_to_proxy), daemon=True)
    p_db = Process(target=run_db_worker, args=(q_to_db,), daemon=True)
    p_turnos.start()
    p_db.start()

    sel = selectors.DefaultSelector()

    sessions_lock = threading.Lock()
    admin_state_lock = threading.Lock()

  
    role_by_sock = {}       # sock -> "CLIENT" | "ADMIN"
    id_by_sock = {}         # sock -> cliente_id o admin_id
    sock_by_client_id = {}  # cliente_id -> sock
    sock_by_admin_id = {}   # admin_id -> sock

    client_meta = {}        # cliente_id -> {"nombre","tramite"}
    admin_busy = set()      # admins ocupados (protegido por admin_state_lock)

    peer = {}               # sock -> sock emparejado (cliente<->admin)
    transcript = {}         

    client_id_lock = threading.Lock()
    client_id_counter = 0

    def log_session(admin_id, cliente_id, line):
        key = (admin_id, cliente_id)
        transcript.setdefault(key, []).append(line)

    def close_socket(sock):
        try:
            sel.unregister(sock)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

    def unpair(sock, reason_msg=None):
        """Rompe una sesión si existe y libera admin."""
        with sessions_lock:
            other = peer.pop(sock, None)
            if other:
                peer.pop(other, None)


        if other and reason_msg:
            try:
                other.sendall((reason_msg + "\n").encode())
            except Exception:
                pass

        admin_id = None
        cliente_id = None
        with sessions_lock:
            if sock in role_by_sock and role_by_sock.get(sock) == "ADMIN":
                admin_id = id_by_sock.get(sock)
            if other in role_by_sock and role_by_sock.get(other) == "ADMIN":
                admin_id = id_by_sock.get(other)
            if sock in role_by_sock and role_by_sock.get(sock) == "CLIENT":
                cliente_id = id_by_sock.get(sock)
            if other in role_by_sock and role_by_sock.get(other) == "CLIENT":
                cliente_id = id_by_sock.get(other)

        if admin_id and cliente_id:

            lines = transcript.pop((admin_id, cliente_id), [])
            meta = client_meta.get(cliente_id, {})
            tramite = meta.get("tramite", "desconocido")
            prioridad = PRIORIDADES.get(tramite, 3)
            q_to_db.put({
                "cliente_id": str(cliente_id),
                "nombre": meta.get("nombre", "Desconocido"),
                "tramite": tramite,
                "prioridad": int(prioridad),
                "admin_id": str(admin_id),
                "conversacion": "\n".join(lines) if lines else None
            })

        if admin_id:
            with admin_state_lock:
                admin_busy.discard(admin_id)

            if admin_id in sock_by_admin_id and sock_by_admin_id[admin_id]:
                q_to_turnos.put({"type": "ADMIN_READY", "admin_id": admin_id})

    def accept(sock):
        conn, addr = sock.accept()
        conn.setblocking(False)
        sel.register(conn, selectors.EVENT_READ, data={"addr": addr, "buf": ""})
        print(f"[PROXY] Conexión entrante desde {addr}")

    def handle_read(conn, data):
        nonlocal client_id_counter
        try:
            chunk = conn.recv(1024)
        except BlockingIOError:
            return
        except Exception:
            unpair(conn, reason_msg="El otro extremo se desconectó.")
            cleanup_conn(conn)
            return

        if not chunk:
            unpair(conn, reason_msg="El otro extremo se desconectó.")
            cleanup_conn(conn)
            return

        msg = chunk.decode(errors="ignore")
        if conn not in role_by_sock:
            parsed = parse_hello(msg)
            if not parsed:
                data["buf"] += msg
                parsed = parse_hello(data["buf"])
                if not parsed:
                    return

            if parsed["type"] == "ADMIN_LOGIN":
                admin_id = parsed["admin_id"]
                with sessions_lock:
                    role_by_sock[conn] = "ADMIN"
                    id_by_sock[conn] = admin_id
                    sock_by_admin_id[admin_id] = conn

                print(f"[PROXY] Admin {admin_id} conectado")
                conn.sendall(f"--- ADMIN {admin_id} CONECTADO ---\nEsperando turnos...\n".encode())

                q_to_turnos.put({"type": "ADMIN_READY", "admin_id": admin_id})
                return

            if parsed["type"] == "CLIENT_HELLO":
                nombre = parsed["nombre"]
                tramite = parsed["tramite"]
                with client_id_lock:
                    client_id_counter += 1
                    cliente_id = str(client_id_counter)

                with sessions_lock:
                    role_by_sock[conn] = "CLIENT"
                    id_by_sock[conn] = cliente_id
                    sock_by_client_id[cliente_id] = conn
                    client_meta[cliente_id] = {"nombre": nombre, "tramite": tramite}

                conn.sendall(build_client_id(cliente_id).encode())
                conn.sendall("Esperando a ser atendido por un administrativo...\n".encode())
                print(f"[PROXY] Turno recibido Cliente {cliente_id} ({nombre}) trámite={tramite}")

                q_to_turnos.put({
                    "type": "NEW_TURNO",
                    "cliente_id": cliente_id,
                    "nombre": nombre,
                    "tramite": tramite
                })
                return

        with sessions_lock:
            dst = peer.get(conn)

        if not dst:
            try:
                conn.sendall("[Aún no estás emparejado. Esperá...]\n".encode())
            except Exception:
                pass
            return

                # Log y relay (con prefijo + FIN correcto)
        with sessions_lock:
            src_role = role_by_sock.get(conn)
            src_id = id_by_sock.get(conn)
            dst_id = id_by_sock.get(dst)

        clean = msg.strip()

        if clean.upper() == "FIN":
            try:
                conn.sendall("FIN\n".encode())
            except Exception:
                pass
            try:
                dst.sendall("FIN\n".encode())
            except Exception:
                pass

            unpair(conn, reason_msg=None)

            with sessions_lock:
                role_conn = role_by_sock.get(conn)
                role_dst = role_by_sock.get(dst)

            if role_conn == "CLIENT":
                cleanup_conn(conn)
            elif role_dst == "CLIENT":
                cleanup_conn(dst)

            return

        if src_role == "ADMIN":
            admin_id = src_id
            cliente_id = dst_id
            out = f"Admin {admin_id}: {clean}\n"
        else:
            cliente_id = src_id
            admin_id = dst_id
            out = f"Cliente {cliente_id}: {clean}\n"

        # guardar transcript con lo mismo que se muestra
        log_session(admin_id, cliente_id, out.strip())

        # reenviar con etiqueta
        try:
            dst.sendall(out.encode())
        except Exception:
            unpair(conn, reason_msg="El otro extremo se desconectó.")
            cleanup_conn(dst)
            cleanup_conn(conn)
            return

    def cleanup_conn(conn):
        # remover de maps
        with sessions_lock:
            r = role_by_sock.pop(conn, None)
            ident = id_by_sock.pop(conn, None)

        if r == "CLIENT" and ident:
            with sessions_lock:
                sock_by_client_id.pop(ident, None)
                client_meta.pop(ident, None)
        if r == "ADMIN" and ident:
            with sessions_lock:
                sock_by_admin_id.pop(ident, None)
            with admin_state_lock:
                admin_busy.discard(ident)
            q_to_turnos.put({"type": "ADMIN_DISCONNECTED", "admin_id": ident})

        close_socket(conn)

    # Server socket (IPv4 / IPv6 / Dual)
    if args.family == "ipv4":
        family = socket.AF_INET
        bind_addr = (args.host, args.port)

    elif args.family == "ipv6":
        family = socket.AF_INET6
        bind_addr = (args.host, args.port, 0, 0)

    else:  
        family = socket.AF_INET6
        bind_addr = (args.host, args.port, 0, 0)

    server = socket.socket(family, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if args.family == "dual":
        try:
            server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except OSError:
            print("[PROXY] Aviso: el SO no permite dual-stack (IPV6_V6ONLY).")

    server.bind(bind_addr)
    server.listen()
    server.setblocking(False)
    sel.register(server, selectors.EVENT_READ, data=None)

    print(f"[PROXY] Escuchando en {args.host}:{args.port}")

    try:
        while True:
            while True:
                try:
                    evt = q_to_proxy.get_nowait()
                except Exception:
                    break

                if evt.get("type") == "ASSIGN":
                    admin_id = evt["admin_id"]
                    cliente_id = evt["cliente_id"]
                    tramite = evt["tramite"]
                    nombre = evt["nombre"]

                    with sessions_lock:
                        admin_sock = sock_by_admin_id.get(admin_id)
                        client_sock = sock_by_client_id.get(cliente_id)

                    if not admin_sock or not client_sock:
                        if admin_sock:
                            q_to_turnos.put({"type": "ADMIN_READY", "admin_id": admin_id})
                        continue

                    with admin_state_lock:
                        if admin_id in admin_busy:
                            q_to_turnos.put({"type": "ADMIN_READY", "admin_id": admin_id})
                            continue
                        admin_busy.add(admin_id)

                    with sessions_lock:
                        peer[admin_sock] = client_sock
                        peer[client_sock] = admin_sock

                    print(f"[PROXY] Emparejado Admin {admin_id} <-> Cliente {cliente_id} ({nombre})")

                    try:
                        admin_sock.sendall(
                            f"Atendiendo a Cliente {cliente_id} ({nombre}) - Trámite: {tramite}\n".encode()
                        )
                        client_sock.sendall(
                            f"Usted está siendo atendido por el administrativo {admin_id}. Puede comenzar a conversar.\n".encode()
                        )
                    except Exception:
                        unpair(admin_sock, reason_msg="Error iniciando conversación.")
                        cleanup_conn(admin_sock)
                        cleanup_conn(client_sock)

            events = sel.select(timeout=0.2)
            for key, mask in events:
                if key.data is None:
                    accept(key.fileobj)
                else:
                    handle_read(key.fileobj, key.data)

    except KeyboardInterrupt:
        print("\n[PROXY] Deteniendo...")
    finally:
        try:
            q_to_turnos.put(None)
            q_to_db.put(None)
        except Exception:
            pass
        try:
            p_turnos.terminate()
            p_db.terminate()
        except Exception:
            pass
        try:
            sel.close()
        except Exception:
            pass
        try:
            server.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()