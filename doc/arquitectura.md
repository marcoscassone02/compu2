# Arquitectura

```mermaid
flowchart LR
  C1[Cliente CLI] -- TCP/JSONL --> S[Servidor asyncio]
  C2[Cliente CLI] -- TCP/JSONL --> S
  A1[Operador CLI] -- TCP/JSONL --> S
  A2[Operador CLI] -- TCP/JSONL --> S
  A3[Operador CLI] -- TCP/JSONL --> S

  S -- IPC: multiprocessing.Queue --> AUD[Proceso Auditor (audit.log)]
  S -- Celery tasks --> R[(Redis Broker)]
  R --> W[Worker Celery]
  W --> DB[(SQLite: tickets/sessions/messages)]

---

# final/doc/funcionalidades.md
```md
# Funcionalidades por entidad

## Servidor (asyncio)
- Acepta múltiples conexiones TCP concurrentes.
- Registra clientes y operadores mediante HELLO.
- Encola turnos (ENQUEUE).
- Asigna automáticamente clientes a operadores libres.
- Rutea mensajes de chat entre cliente y operador (CHAT).
- Finaliza sesión (END) y deja al operador disponible nuevamente.
- Emite eventos y delega persistencia a Celery.

## Cliente (CLI)
- Conecta al servidor (HELLO).
- Solicita turno (ENQUEUE tramite).
- Espera asignación (ASSIGNED).
- Conversa con el operador (CHAT).
- Finaliza atención (/end).

## Operador (CLI)
- Conecta al servidor (HELLO).
- Espera asignación automática.
- Conversa con el cliente (CHAT).
- Finaliza atención (/end) y vuelve a estado libre.

## Proceso auditor (IPC)
- Recibe eventos internos del servidor mediante multiprocessing.Queue.
- Escribe audit.log sin bloquear el loop principal del servidor.

## Worker Celery
- Consume tareas desde Redis.
- Persiste en SQLite:
  - Turno creado
  - Inicio/fin de sesión
  - Mensajes de conversación (fecha/hora, emisor, texto)
