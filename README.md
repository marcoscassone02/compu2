# 🏦 Sistema de Turnos Virtual – Cliente/Servidor

## 📌 Descripción
Este proyecto implementa una aplicación **cliente–servidor en Python** que simula un **sistema de turnos virtuales**, similar a los utilizados en bancos u organismos públicos.  
Múltiples clientes pueden solicitar turnos de manera concurrente y son atendidos por operadores administrativos mediante una conversación en terminal.

El sistema aplica conceptos de **concurrencia, asincronismo, IPC y colas distribuidas**, separando la lógica de atención de la persistencia de datos para mantener el servidor siempre responsivo.

---

## ⚙️ Características principales
- Conexión de múltiples clientes concurrentes mediante **sockets TCP**
- Comunicación **asíncrona** usando `asyncio`
- Gestión de turnos **FIFO**
- Prioridad por tipo de trámite (`reclamo`, `pago`, `consulta`)
- Escalamiento automático de prioridad según tiempo de espera
- Conversación en tiempo real cliente–operador por terminal
- Persistencia asíncrona con **Celery + Redis**
- Almacenamiento de datos en **SQLite**
- Uso de **cola de tareas distribuida**
- Aplicaciones **CLI** con parseo de argumentos
- Despliegue utilizando **Docker**

---

## 🧱 Arquitectura
El sistema está compuesto por los siguientes elementos:

- **Servidor**  
  Gestiona conexiones, cola de turnos y asignación de operadores.

- **Clientes**  
  Solicitan turnos y mantienen una conversación con el operador asignado.

- **Operadores (admins)**  
  Atienden turnos desde terminales independientes.

- **Worker Celery**  
  Ejecuta tareas de persistencia en segundo plano.

- **Redis**  
  Broker de la cola distribuida.

- **SQLite**  
  Base de datos para auditoría y trazabilidad.

---

## 📋 Requisitos
- Python 3.10 o superior
- Docker
- Docker Compose

---

## 🚀 Ejecución del proyecto

### 1️⃣ Levantar Redis y el worker
```bash
docker compose up -d
