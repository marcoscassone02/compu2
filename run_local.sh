#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/3] Levantando Redis + Celery worker (docker compose)..."
docker compose up -d

echo "[2/3] Iniciando servidor (esto abrirá 3 terminales para operadores si es posible)..."
python3 src/server.py --host 127.0.0.1 --port 9000 --spawn-admins 3

