# Sistema de Procesamiento de Imágenes Asíncrono en Python
Este proyecto implementa un sistema de procesamiento de imágenes que permite a los clientes enviar imágenes a un servidor HTTP. El servidor convierte la imagen a escala de grises y luego la escala según un factor de tamaño especificado por el cliente. Toda la comunicación y el procesamiento se realiza de forma asíncrona en el servidor HTTP, sin requerir un segundo servidor de escalado.

# Requisitos
Python 3.7+
Librerías Python: aiohttp, Pillow, requests
Sockets y Multiprocessing: utilizados para manejar las conexiones de forma concurrente y eficiente.

# Estructura del Proyecto
main.py: Archivo principal que inicia el servidor HTTP (async_server) y gestiona la ejecución del cliente.
async_server.py: Servidor HTTP asíncrono que recibe la imagen del cliente, la convierte a escala de grises, la escala según el factor proporcionado y la envía de vuelta al cliente.
client.py: Cliente que envía una imagen al async_server junto con un factor de escala.

# Ejecucion
git clone <git@github.com:marcoscassone02/compu2.git>
cd <TP2>
python3 main.py
