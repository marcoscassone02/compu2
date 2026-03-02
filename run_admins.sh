#!/bin/bash
set -e

HOST="localhost"
PORT="5000"
ADMINS=3

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ruta correcta
ADMIN_FILE="cliente/administrativo.py"

if [ ! -f "$ADMIN_FILE" ]; then
  echo "No encuentro $ADMIN_FILE en $SCRIPT_DIR"
  echo "Revisá la ruta o mové el script a la carpeta raíz del proyecto."
  exit 1
fi

for i in $(seq 1 $ADMINS); do
  gnome-terminal -- bash -c "python3 $ADMIN_FILE --host $HOST --port $PORT --admin_id A$i; exec bash"
done

echo "Lanzando $ADMINS administrativos en nuevas terminales..."
