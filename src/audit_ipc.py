import time
from multiprocessing import Queue

def audit_loop(q: Queue, logfile: str = "audit.log") -> None:
    with open(logfile, "a", encoding="utf-8") as f:
        f.write("\n=== Auditor iniciado ===\n")
        f.flush()
        while True:
            msg = q.get()
            if msg == "__STOP__":
                f.write("=== Auditor detenido ===\n")
                f.flush()
                break
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
            f.flush()
