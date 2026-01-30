import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict

# JSON Lines (1 mensaje JSON por linea) sobre TCP
def json_dumps(obj: Dict[str, Any]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")

def json_loads(line: bytes) -> Dict[str, Any]:
    return json.loads(line.decode("utf-8"))

# Prioridad base (menor = mayor prioridad)
BASE_PRIORITY = {
    "reclamo": 0,
    "pago": 1,
    "consulta": 2,
}

AGING_SECONDS = 10 * 60  # 10 minutos

def now_unix() -> float:
    return time.time()

def new_session_id() -> str:
    return str(uuid.uuid4())

def base_priority(tramite: str) -> int:
    return BASE_PRIORITY.get(tramite.lower().strip(), 2)

def effective_priority(tramite: str, created_at_unix: float, now_unix_ts: float) -> int:
    """
    Aging:
      - consulta (2) -> a los 10 min: 1 (pago) -> a los 20 min: 0 (reclamo)
      - pago (1) -> a los 10 min: 0 (reclamo)
      - reclamo (0) -> queda 0
    """
    base = base_priority(tramite)
    waited = max(0.0, now_unix_ts - created_at_unix)
    promos = int(waited // AGING_SECONDS)
    return max(0, base - promos)

@dataclass
class WaitingClient:
    ticket_id: int
    client_name: str
    tramite: str
    created_at_unix: float
    reader: Any
    writer: Any
