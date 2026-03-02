# 🏦 CLI-Serv Turnos

Sistema distribuido cliente-servidor que simula un sistema de atención virtual con asignación dinámica de turnos.

Implementa concurrencia, paralelismo, comunicación asíncrona (IPC) y persistencia en base de datos.

---

## 🚀 Características

- 🔄 Múltiples clientes y administrativos concurrentes
- ⚡ I/O multiplexado con `selectors`
- 🧠 Cola de prioridad con *aging*
- 🔀 Procesos independientes (`multiprocessing`)
- 🔗 Comunicación asíncrona mediante `Queue`
- 💾 Persistencia en SQLite
- 🌐 Soporte IPv4 / IPv6 / Dual Stack
- 🐳 Despliegue con Docker

---

## 🏗 Arquitectura

**Componentes principales:**

- **Proxy Server**
  - Maneja conexiones TCP
  - Empareja cliente ↔ administrativo
  - Registra conversaciones

- **Turnos Service (Proceso separado)**
  - Gestiona cola de prioridad
  - Asigna turnos disponibles

- **DB Worker (Proceso separado)**
  - Persiste turnos y conversaciones en SQLite

Base de datos utilizada:

data/turnos.db

## 🐳 Ejecutar con Docker

```bash
docker compose up --build
```

## Crear Administradores

```bash
./run_admins.sh
```
## Crear Cliente

```bash
python3 cliente/cliente.py --host localhost --port 5000
```