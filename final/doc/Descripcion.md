# Descripción Verbal de la Aplicación

Quiero desarrollar una aplicación cliente-servidor (CLI-Serv) que simule un sistema de turnos virtuales como los utilizados en bancos o entes gubernamentales. El sistema debe permitir que múltiples clientes soliciten turnos de manera concurrente, especificando el tipo de trámite a realizar (pago, reclamo, consulta, etc.), y que un cliente administrativo los atienda en orden de prioridad.

La aplicación estará compuesta por:

Clientes (usuarios) que ejecutan una aplicación CLI para solicitar turnos.

Un servidor que escucha conexiones de los clientes, registra los turnos y los organiza en una cola de prioridad.

Un cliente administrativo (también CLI) que consulta al servidor para atender turnos.

Se utilizará concurrencia para manejar múltiples conexiones de clientes simultáneamente mediante el uso de hilos o procesos. Se aplicará asincronismo para el manejo eficiente de la entrada/salida de los sockets. Los procesos involucrados (recepción de turnos, atención y persistencia en base de datos) se comunicarán mediante mecanismos de IPC como colas o pipes. La arquitectura se diseñará de forma que los componentes puedan trabajar en paralelo.

Se almacenarán los turnos atendidos en una base de datos SQLite para futuras consultas o reportes. 