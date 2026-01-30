# Descripción verbal de la aplicación

Esta aplicación implementa un sistema de turnos virtual cliente-servidor similar al de bancos/entes públicos.

- Múltiples clientes (CLI) se conectan por TCP al servidor y solicitan un turno indicando el tipo de trámite: reclamo, pago o consulta.
- El servidor mantiene una cola de espera y asigna automáticamente clientes a operadores (3 operadores por defecto) en cuanto un operador está libre.
- Una vez asignado, el cliente y el operador mantienen una conversación por terminal (chat) hasta que alguno finaliza la atención.

## Prioridad y fairness (aging)
La prioridad se basa en:
1) Prioridad por trámite: reclamo > pago > consulta.
2) Envejecimiento: cada 10 minutos de espera, el turno sube un nivel de prioridad:
   - consulta -> (10 min) pago -> (20 min) reclamo
   - pago -> (10 min) reclamo
Desempate: FIFO por orden de llegada.

## Tecnologías clave
- Servidor TCP asincrónico: asyncio (I/O no bloqueante).
- IPC local: multiprocessing.Queue para auditoría en proceso separado.
- Cola distribuida: Celery + Redis para persistencia asíncrona.
- Base de datos: SQLite (tickets, sesiones y mensajes).
- CLI: argparse en server/client/admin.
