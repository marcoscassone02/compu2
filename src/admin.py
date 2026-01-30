import argparse
import asyncio
import sys
from common import json_dumps, json_loads

HELP = """
Comandos:
  /end        Finaliza la sesión actual (si existe)
  /quit       Sale del programa
"""

async def sender_loop(writer: asyncio.StreamWriter, state: dict):
    print(HELP.strip())
    loop = asyncio.get_event_loop()

    while True:
        # leer stdin sin bloquear el loop principal: executor
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        line = line.rstrip("\n")

        if line == "/quit":
            break

        if line == "/end":
            sid = state.get("session_id")
            if sid:
                writer.write(json_dumps({"type": "END", "session_id": sid}))
                await writer.drain()
            else:
                print("[ADMIN] No hay sesión activa.")
            continue

        sid = state.get("session_id")
        if not sid:
            print("[ADMIN] Esperando asignación... (no podés chatear todavía)")
            continue

        writer.write(json_dumps({"type": "CHAT", "session_id": sid, "text": line}))
        await writer.drain()

async def receiver_loop(reader: asyncio.StreamReader, state: dict):
    while True:
        line = await reader.readline()
        if not line:
            print("[ADMIN] Conexión cerrada por el servidor.")
            return
        msg = json_loads(line)
        t = msg.get("type")

        if t == "WELCOME":
            print(f"[ADMIN] Conectado como {msg.get('name')}. Esperando clientes...")
        elif t == "ASSIGNED":
            state["session_id"] = msg.get("session_id")
            print(f"\n[ADMIN] ✅ Asignado cliente={msg.get('client')} tramite={msg.get('tramite')} sid={state['session_id']}\n")
        elif t == "CHAT":
            print(f"{msg.get('name')} ({msg.get('from')}): {msg.get('text')}")
        elif t == "SESSION_ENDED":
            reason = msg.get("reason")
            sid = msg.get("session_id")
            if state.get("session_id") == sid:
                state["session_id"] = None
            print(f"\n[ADMIN] 🔚 Sesión finalizada. reason={reason}. Esperando próximo cliente...\n")
        elif t == "ERROR":
            print(f"[ADMIN][ERROR] {msg.get('message')}")
        else:
            print(f"[ADMIN] {msg}")

async def main():
    parser = argparse.ArgumentParser(description="Operador (admin) - chat por turnos")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    reader, writer = await asyncio.open_connection(args.host, args.port)

    # HELLO
    writer.write(json_dumps({"type": "HELLO", "role": "admin", "name": args.name}))
    await writer.drain()

    state = {"session_id": None}

    await asyncio.gather(
        receiver_loop(reader, state),
        sender_loop(writer, state),
    )

    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
