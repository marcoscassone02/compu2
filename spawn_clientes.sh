#!/bin/bash
set -e

HOST="localhost"
PORT="5000"
CLIENTS=7

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CLIENT_FILE="cliente/cliente.py"

if [ ! -f "$CLIENT_FILE" ]; then
  echo "No encuentro $CLIENT_FILE en $SCRIPT_DIR"
  echo "Revisá la ruta o mové el script a la carpeta raíz del proyecto."
  exit 1
fi

TRAMITES=("pago" "reclamo" "consulta")

for i in $(seq 1 $CLIENTS); do
  NOMBRE="Cliente_$i"
  TRAMITE=${TRAMITES[$(( (i-1) % 3 ))]}

  gnome-terminal -- bash -c \
  "python3 $CLIENT_FILE --host $HOST --port $PORT --name $NOMBRE --tramite $TRAMITE; exec bash"

done

echo "Lanzando $CLIENTS clientes en nuevas terminales..."