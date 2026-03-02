def parse_hello(msg: str):
    """
    Devuelve un dict con:
      - {"type":"ADMIN_LOGIN","admin_id":...}
      - {"type":"CLIENT_HELLO","nombre":...,"tramite":...}
      - None si no se puede parsear todavía
    """
    msg = (msg or "").strip()
    if not msg:
        return None

    if msg.startswith("ADMIN_LOGIN:"):
        admin_id = msg.split(":", 1)[1].strip()
        return {"type": "ADMIN_LOGIN", "admin_id": admin_id}

    # formato: nombre:Juan;tramite:consulta
    if ";" in msg and ":" in msg:
        partes = {}
        for chunk in msg.split(";"):
            if ":" in chunk:
                k, v = chunk.split(":", 1)
                partes[k.strip()] = v.strip()
        if "tramite" in partes:
            return {
                "type": "CLIENT_HELLO",
                "nombre": partes.get("nombre", "Desconocido"),
                "tramite": partes.get("tramite"),
            }

    return None


def build_client_id(cliente_id: str) -> str:
    return f"CLIENTE_ID:{cliente_id}\n"