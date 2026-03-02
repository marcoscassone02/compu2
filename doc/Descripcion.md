# Descripción Verbal de la Aplicación

Quiero armar una aplicación CLI-Serv que simule un sistema de turnos virtuales para atención al público.

Estan los clientes que se conectan al servidor, envían sus datos (nombre) y el tipo de trámite (pago, reclamo, consulta). Luego quedan en espera hasta que un administrativo lo atienda. Durante la atención, intercambian mensajes con el administrativo y finaliza con FIN.

Y tambien los administrativo que se conecta al servidor identificándose con ADMIN_LOGIN:<id>, quedan disponible para atender turnos, conversa con el cliente asignado y termina la conversación con FIN (sin cerrar su programa; vuelve a quedar disponible).

Del lado servidor, hay un Proxy Server que maneja las conexiones de red de muchos clientes y muchos administrativos en concurrencia, usando I/O multiplexado con selectors (event loop, sockets no bloqueantes).

Para la lógica del negocio se separan responsabilidades en paralelismo real (múltiples procesos):

Un proceso Turnos Service mantiene una cola de prioridad con aging (si un cliente espera demasiado, sube su prioridad) y una cola de administrativos disponibles. Decide emparejamientos y los envía al Proxy.

Un proceso DB Worker persiste en SQLite los turnos atendidos, con datos del cliente, admin, prioridad, timestamp y el transcript (conversación).

La comunicación entre procesos es asíncrona mediante IPC real usando multiprocessing.Queue:

Proxy → Turnos: eventos como NEW_TURNO, ADMIN_READY, ADMIN_DISCONNECTED.

Turnos → Proxy: evento ASSIGN con la asignación (admin_id, cliente_id, etc.).

Proxy → DB Worker: evento con los datos finales para guardar (incluye conversación).