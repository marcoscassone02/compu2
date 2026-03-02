# Lista de Funcionalidades por Entidad

A) Cliente CLI (cliente/cliente.py)

Conectarse al servidor (host/port; IPv4/IPv6 según host).
Enviar “hello” con datos: nombre:<X>;tramite:<pago|reclamo|consulta>.
Recibir CLIENTE_ID:<id>.
Esperar hasta ser atendido.
Intercambiar mensajes con el administrativo (chat simple).
Terminar conversación enviando FIN.
Manejar desconexión del servidor (cerrar limpio).

B) Administrativo CLI (cliente/administrativo.py)

Conectarse al servidor y autenticarse: ADMIN_LOGIN:<admin_id>.
Recibir confirmación “ADMIN CONECTADO” y quedar en espera.
Cuando recibe asignación (“Atendiendo a Cliente…”), entrar en sesión.
Enviar/recibir mensajes al cliente (relay vía Proxy).
Finalizar sesión con FIN (queda disponible para otro cliente sin cerrar el programa).
Comando local para salir del programa: SALIR o /exit.
Manejo de desconexión / cierre limpio.

C) Proxy Server (servidor/proxy_server.py)

Rol principal: red + sesiones.
Escuchar en IPv4 / IPv6 / dual (según --family).
Aceptar conexiones concurrentes con selectors.
Detectar tipo de conexión en el primer mensaje (ADMIN_LOGIN vs CLIENT_HELLO).
Mantener mapas de estado:
    sock→rol, sock→id, cliente_id→sock, admin_id→sock
peer[cliente_sock]↔admin_sock cuando hay sesión
transcript por sesión (admin_id, cliente_id)
Enviar eventos al Turnos Service:
    ADMIN_READY al conectar admin
    NEW_TURNO al conectar cliente
    ADMIN_DISCONNECTED si cae un admin
    Recibir ASSIGN del Turnos Service y emparejar sockets.
Relay de mensajes cliente↔admin y loguear transcript.
Al recibir FIN: cerrar sesión lógica, liberar admin, notificar Turnos.
Al finalizar sesión: enviar evento al DB Worker para persistir turno + conversación.

D) Turnos Service (servidor/turnos_service.py)

Rol: lógica de asignación y prioridades.
Mantener cola de turnos con prioridad (heapq) y aging (espera ⇒ mejora prioridad).
Mantener cola FIFO de admins disponibles (deque).
Consumir eventos desde Proxy:
    ADMIN_READY: agrega admin a disponibles
    NEW_TURNO: agrega cliente a cola con prioridad
    ADMIN_DISCONNECTED: elimina admin si estaba esperando
Emitir asignaciones hacia Proxy (ASSIGN) cuando haya admin + turno.

E) DB Worker (servidor/db_worker.py + db.py)

Rol: persistencia desacoplada.
Inicializar DB (tabla si no existe).
Consumir tareas de guardado desde IPC queue.
Guardar en SQLite:
    cliente_id, nombre, trámite, prioridad, admin_id, timestamp, conversacion
Reportar errores sin tumbar el servidor.