import argparse
import asyncio
import shutil
import subprocess
from collections import deque
from multiprocessing import Process, Queue
from typing import Dict, Optional, Tuple

from common import (
    WaitingClient,
    effective_priority,
    json_dumps,
    json_loads,
    new_session_id,
    now_unix,
)
from audit_ipc import audit_loop
from tasks import (
    persist_event,
    persist_message,
    persist_session_end,
    persist_session_start,
    persist_ticket,
)

class AdminConn:
    def __init__(self, name: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.name = name
        self.reader = reader
        self.writer = writer
        self.busy: bool = False
        self.session_id: Optional[str] = None

class Session:
    def __init__(self, session_id: str, ticket: WaitingClient, admin: AdminConn):
        self.session_id = session_id
        self.ticket = ticket
        self.admin = admin
        self.active: bool = True

class TurnosServer:
    def __init__(self, audit_q: Queue):
        self.audit_q = audit_q
        self.next_ticket_id = 1

        # Espera (no fijamos prioridad en estructura porque cambia con el tiempo)
        self.waiting: deque[WaitingClient] = deque()

        # Admins conectados
        self.admins: Dict[str, AdminConn] = {}

        # Sesiones activas
        self.sessions: Dict[str, Session] = {}

        # lock simple para asignacion
        self.assign_lock = asyncio.Lock()

    def _log(self, msg: str) -> None:
        self.audit_q.put(msg)

    async def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        self._log(f"CONN {addr}")

        role = None
        name = None

        try:
            # Primer mensaje debe ser HELLO
            line = await reader.readline()
            if not line:
                return
            hello = json_loads(line)
            if hello.get("type") != "HELLO":
                writer.write(json_dumps({"type": "ERROR", "message": "First message must be HELLO"}))
                await writer.drain()
                return

            role = hello.get("role")
            name = str(hello.get("name", "")).strip() or "anon"

            if role == "admin":
                admin = AdminConn(name=name, reader=reader, writer=writer)
                self.admins[name] = admin
                self._log(f"ADMIN_UP name={name}")
                persist_event.delay("ADMIN_UP", {"admin": name})
                writer.write(json_dumps({"type": "WELCOME", "role": "admin", "name": name}))
                await writer.drain()

                # Intentar asignar inmediatamente si hay clientes esperando
                await self.try_assign()

                # Quedarse escuchando mensajes del admin (CHAT / END)
                await self.admin_loop(admin)

            elif role == "client":
                self._log(f"CLIENT_UP name={name}")
                persist_event.delay("CLIENT_UP", {"client": name})
                writer.write(json_dumps({"type": "WELCOME", "role": "client", "name": name}))
                await writer.drain()

                # Quedarse escuchando mensajes del cliente (ENQUEUE / CHAT / END)
                await self.client_loop(client_name=name, reader=reader, writer=writer)

            else:
                writer.write(json_dumps({"type": "ERROR", "message": "role must be 'admin' or 'client'"}))
                await writer.drain()
                return

        except Exception as e:
            self._log(f"ERROR {addr} role={role} name={name} err={e}")
        finally:
            # Cleanup en desconexion
            try:
                await self.cleanup_connection(role, name, writer)
            except Exception as _:
                pass
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as _:
                pass
            self._log(f"DISCONN {addr} role={role} name={name}")

    async def cleanup_connection(self, role: Optional[str], name: Optional[str], writer: asyncio.StreamWriter):
        if role == "admin" and name and name in self.admins:
            admin = self.admins[name]

            # Si se desconecta en medio de sesion, finalizarla
            if admin.busy and admin.session_id and admin.session_id in self.sessions:
                session = self.sessions[admin.session_id]
                session.active = False
                persist_session_end.delay(session.session_id, "admin_disconnected")
                persist_event.delay("SESSION_END", {"session_id": session.session_id, "reason": "admin_disconnected"})
                await self._notify_client_end(session.ticket.writer, session.session_id, "admin_disconnected")

                # El cliente vuelve a espera? (decisión): lo reenfilamos para que no pierda el turno.
                self._log(f"REQUEUE ticket={session.ticket.ticket_id} client={session.ticket.client_name} reason=admin_disconnected")
                self.waiting.appendleft(session.ticket)

                del self.sessions[session.session_id]

            del self.admins[name]
            persist_event.delay("ADMIN_DOWN", {"admin": name})

        if role == "client" and name:
            # Si estaba esperando, quitarlo (comparando writer)
            self.waiting = deque([c for c in self.waiting if c.writer is not writer])

            # Si estaba en sesion activa, finalizar
            sid = self._find_session_by_writer(writer)
            if sid and sid in self.sessions:
                session = self.sessions[sid]
                session.active = False
                persist_session_end.delay(sid, "client_disconnected")
                persist_event.delay("SESSION_END", {"session_id": sid, "reason": "client_disconnected"})
                await self._notify_admin_end(session.admin.writer, sid, "client_disconnected")

                # Admin vuelve a idle
                session.admin.busy = False
                session.admin.session_id = None

                del self.sessions[sid]
                await self.try_assign()

            persist_event.delay("CLIENT_DOWN", {"client": name})

    def _find_session_by_writer(self, writer: asyncio.StreamWriter) -> Optional[str]:
        for sid, s in self.sessions.items():
            if s.ticket.writer is writer:
                return sid
        return None

    async def client_loop(self, client_name: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Cliente:
          - ENQUEUE {tramite}
          - CHAT {session_id, text}
          - END  {session_id}
        """
        while True:
            line = await reader.readline()
            if not line:
                break
            msg = json_loads(line)
            mtype = msg.get("type")

            if mtype == "ENQUEUE":
                tramite = str(msg.get("tramite", "consulta")).strip().lower()
                ticket_id = self.next_ticket_id
                self.next_ticket_id += 1

                wc = WaitingClient(
                    ticket_id=ticket_id,
                    client_name=client_name,
                    tramite=tramite,
                    created_at_unix=now_unix(),
                    reader=reader,
                    writer=writer,
                )
                self.waiting.append(wc)

                # Persist async
                persist_ticket.delay(ticket_id, tramite, client_name)
                persist_event.delay("TICKET_CREATED", {"ticket_id": ticket_id, "tramite": tramite, "client": client_name})

                self._log(f"TICKET_CREATED id={ticket_id} client={client_name} tramite={tramite}")

                writer.write(json_dumps({"type": "ENQUEUED", "ticket_id": ticket_id, "tramite": tramite}))
                await writer.drain()

                await self.try_assign()

            elif mtype == "CHAT":
                sid = str(msg.get("session_id", ""))
                text = str(msg.get("text", ""))

                if not sid or sid not in self.sessions:
                    writer.write(json_dumps({"type": "ERROR", "message": "Invalid session_id"}))
                    await writer.drain()
                    continue

                session = self.sessions[sid]
                # Solo permitir si este writer corresponde al cliente de la sesion
                if session.ticket.writer is not writer or not session.active:
                    writer.write(json_dumps({"type": "ERROR", "message": "Session not active for this client"}))
                    await writer.drain()
                    continue

                # Persistir y rutear al admin
                persist_message.delay(sid, "client", client_name, text)
                persist_event.delay("MESSAGE", {"session_id": sid, "from": "client", "name": client_name})

                await self._send(session.admin.writer, {"type": "CHAT", "session_id": sid, "from": "client", "name": client_name, "text": text})

            elif mtype == "END":
                sid = str(msg.get("session_id", ""))
                if sid and sid in self.sessions:
                    await self.end_session(sid, "client_end")
                else:
                    writer.write(json_dumps({"type": "ERROR", "message": "Invalid session_id"}))
                    await writer.drain()

            else:
                writer.write(json_dumps({"type": "ERROR", "message": f"Unknown type: {mtype}"}))
                await writer.drain()

    async def admin_loop(self, admin: AdminConn):
        """
        Admin:
          - CHAT {session_id, text}
          - END  {session_id}
        """
        while True:
            line = await admin.reader.readline()
            if not line:
                break
            msg = json_loads(line)
            mtype = msg.get("type")

            if mtype == "CHAT":
                sid = str(msg.get("session_id", ""))
                text = str(msg.get("text", ""))

                if not sid or sid not in self.sessions:
                    await self._send(admin.writer, {"type": "ERROR", "message": "Invalid session_id"})
                    continue

                session = self.sessions[sid]
                if session.admin is not admin or not session.active:
                    await self._send(admin.writer, {"type": "ERROR", "message": "Session not active for this admin"})
                    continue

                persist_message.delay(sid, "admin", admin.name, text)
                persist_event.delay("MESSAGE", {"session_id": sid, "from": "admin", "name": admin.name})

                await self._send(session.ticket.writer, {"type": "CHAT", "session_id": sid, "from": "admin", "name": admin.name, "text": text})

            elif mtype == "END":
                sid = str(msg.get("session_id", ""))
                if sid and sid in self.sessions:
                    await self.end_session(sid, "admin_end")
                else:
                    await self._send(admin.writer, {"type": "ERROR", "message": "Invalid session_id"})

            else:
                await self._send(admin.writer, {"type": "ERROR", "message": f"Unknown type: {mtype}"})

    async def _send(self, writer: asyncio.StreamWriter, payload: dict):
        writer.write(json_dumps(payload))
        await writer.drain()

    async def _notify_client_end(self, writer: asyncio.StreamWriter, session_id: str, reason: str):
        await self._send(writer, {"type": "SESSION_ENDED", "session_id": session_id, "reason": reason})

    async def _notify_admin_end(self, writer: asyncio.StreamWriter, session_id: str, reason: str):
        await self._send(writer, {"type": "SESSION_ENDED", "session_id": session_id, "reason": reason})

    async def end_session(self, session_id: str, reason: str):
        session = self.sessions.get(session_id)
        if not session:
            return
        session.active = False

        # Persist end
        persist_session_end.delay(session_id, reason)
        persist_event.delay("SESSION_END", {"session_id": session_id, "reason": reason})

        self._log(f"SESSION_END sid={session_id} reason={reason} admin={session.admin.name} client={session.ticket.client_name}")

        # Notificar a ambos
        await self._notify_client_end(session.ticket.writer, session_id, reason)
        await self._notify_admin_end(session.admin.writer, session_id, reason)

        # Admin vuelve idle
        session.admin.busy = False
        session.admin.session_id = None

        # Remover sesion
        del self.sessions[session_id]

        # Intentar asignar otro cliente al admin (auto)
        await self.try_assign()

    def pick_best_waiting_index(self) -> Optional[int]:
        """
        Elige el mejor ticket en espera según:
          1) menor prioridad efectiva (reclamo < pago < consulta, con aging cada 10 min)
          2) FIFO (más antiguo primero) como desempate
        """
        if not self.waiting:
            return None

        now_ts = now_unix()
        best_idx = None
        best_key: Optional[Tuple[int, float]] = None  # (prio_efectiva, created_at)

        for i, c in enumerate(self.waiting):
            pr = effective_priority(c.tramite, c.created_at_unix, now_ts)
            key = (pr, c.created_at_unix)
            if best_key is None or key < best_key:
                best_key = key
                best_idx = i

        return best_idx

    def get_idle_admin(self) -> Optional[AdminConn]:
        for a in self.admins.values():
            if not a.busy:
                return a
        return None

    async def try_assign(self):
        async with self.assign_lock:
            while True:
                admin = self.get_idle_admin()
                if not admin:
                    return
                idx = self.pick_best_waiting_index()
                if idx is None:
                    return

                # sacar ese cliente de la cola
                client = self.waiting[idx]
                del self.waiting[idx]

                # crear sesion
                sid = new_session_id()
                admin.busy = True
                admin.session_id = sid
                session = Session(session_id=sid, ticket=client, admin=admin)
                self.sessions[sid] = session

                # Persist start
                persist_session_start.delay(sid, client.ticket_id, admin.name, client.client_name, client.tramite)
                persist_event.delay("SESSION_START", {
                    "session_id": sid,
                    "ticket_id": client.ticket_id,
                    "admin": admin.name,
                    "client": client.client_name,
                    "tramite": client.tramite,
                })

                self._log(f"ASSIGNED sid={sid} ticket={client.ticket_id} client={client.client_name} tramite={client.tramite} admin={admin.name}")

                # Notificar a ambos
                await self._send(client.writer, {
                    "type": "ASSIGNED",
                    "session_id": sid,
                    "ticket_id": client.ticket_id,
                    "tramite": client.tramite,
                    "operator": admin.name,
                })
                await self._send(admin.writer, {
                    "type": "ASSIGNED",
                    "session_id": sid,
                    "ticket_id": client.ticket_id,
                    "tramite": client.tramite,
                    "client": client.client_name,
                })


def detect_terminal_command() -> Optional[Tuple[str, list]]:
    """
    Devuelve (binary, args_prefix) para abrir terminal y ejecutar comando.
    Best-effort en Linux.
    """
    # Preferencias comunes
    candidates = [
        ("gnome-terminal", ["--"]),
        ("x-terminal-emulator", ["-e"]),  # Debian/Ubuntu alternatives
        ("konsole", ["-e"]),
        ("xfce4-terminal", ["-e"]),
        ("xterm", ["-e"]),
    ]
    for bin_name, prefix in candidates:
        if shutil.which(bin_name):
            return (bin_name, prefix)
    return None

def spawn_admin_terminals(host: str, port: int, count: int):
    term = detect_terminal_command()
    if not term:
        print("[WARN] No se detectó un emulador de terminal para autospawn.")
        print("       Ejecutá manualmente en 3 terminales:")
        print(f"       python3 src/admin.py --host {host} --port {port} --name op1")
        print(f"       python3 src/admin.py --host {host} --port {port} --name op2")
        print(f"       python3 src/admin.py --host {host} --port {port} --name op3")
        return

    bin_name, prefix = term
    for i in range(1, count + 1):
        name = f"op{i}"
        cmd = ["python3", "src/admin.py", "--host", host, "--port", str(port), "--name", name]
        full = [bin_name] + prefix + cmd
        try:
            subprocess.Popen(full)
        except Exception as e:
            print(f"[WARN] No pude abrir terminal para {name}: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Servidor de turnos + chat (asyncio TCP)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--spawn-admins", type=int, default=3, help="Cantidad de operadores a abrir en terminales")
    args = parser.parse_args()

    audit_q: Queue = Queue()
    audit_proc = Process(target=audit_loop, args=(audit_q, "audit.log"), daemon=True)
    audit_proc.start()

    logic = TurnosServer(audit_q)

    server = await asyncio.start_server(logic.handle_conn, args.host, args.port)
    print(f"[SERVER] Listening on {args.host}:{args.port}")
    audit_q.put(f"SERVER_UP {args.host}:{args.port}")
    persist_event.delay("SERVER_UP", {"host": args.host, "port": args.port})

    # Spawn admins en terminales
    if args.spawn_admins > 0:
        spawn_admin_terminals(args.host, args.port, args.spawn_admins)

    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        audit_q.put("SERVER_DOWN")
        persist_event.delay("SERVER_DOWN", {})
        audit_q.put("__STOP__")
        audit_proc.join(timeout=2)

if __name__ == "__main__":
    asyncio.run(main())
