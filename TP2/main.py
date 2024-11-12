import subprocess
import time
import os
import socket

def is_server_running(host='127.0.0.1', port=8080):
    """Verifica si el servidor está corriendo en el puerto especificado."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.timeout, socket.error):
        return False

def start_server():
    """Inicia el servidor asíncrono."""
    print("Iniciando el servidor...")
    # Ejecuta el servidor en un proceso separado
    server_process = subprocess.Popen(["python3", "async_server.py"])
    return server_process

def start_client():
    """Inicia el cliente que interactúa con el servidor."""
    print("Iniciando el cliente...")
    # Ejecuta el cliente en un proceso separado
    client_process = subprocess.Popen(["python3", "client.py"])
    return client_process

def main():
    """Función principal para iniciar el servidor y luego el cliente."""
    # Asegúrate de que los directorios necesarios existan
    if not os.path.exists("imagen_procesada"):
        os.makedirs("imagen_procesada")

    # Inicia el servidor
    server_process = start_server()

    # Verifica si el servidor está en funcionamiento
    print("Esperando a que el servidor esté disponible...")
    while not is_server_running():
        time.sleep(1)  # Espera 1 segundo antes de volver a intentar

    print("Servidor disponible. Iniciando el cliente...")
    
    # Inicia el cliente
    client_process = start_client()

    # Espera a que el cliente termine
    client_process.wait()

    # Finaliza el servidor después de que el cliente haya terminado
    print("Cliente completado. Finalizando servidor...")
    server_process.terminate()
    server_process.wait()

if __name__ == "__main__":
    main()