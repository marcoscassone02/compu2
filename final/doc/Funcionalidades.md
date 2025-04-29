# Lista de Funcionalidades por Entidad

# Cliente Usuario (cliente_usuario.py)

Mostrar menú para seleccionar tipo de trámite.
Enviar solicitud de turno al servidor (nombre + tipo de trámite).
Esperar confirmación del servidor con número de turno asignado.

# Servidor (servidor.py)

Aceptar múltiples conexiones de clientes mediante sockets.
Procesar las solicitudes concurrentemente usando hilos o procesos.
Agregar los turnos a una cola de prioridad según el tipo de trámite.
Gestionar la cola y enviar turnos al cliente administrativo vía IPC.
Registrar los turnos atendidos en la base de datos (opcional).

# Cliente Administrativo (cliente_admin.py)

Conectarse con el servidor para obtener el próximo turno.
Mostrar datos del turno (nombre, trámite, número).
Notificar al servidor que el turno fue atendido.

# Base de Datos (gestor_bd.py)

Crear tabla para almacenar historial de turnos.
Insertar registros de turnos atendidos.
Consultar turnos históricos (fecha, tipo, estado).

# Comunicación (ipc_queue.py)

Implementar mecanismo IPC (ej. cola multiproceso) para compartir información entre los subprocesos del servidor y el proceso administrativo