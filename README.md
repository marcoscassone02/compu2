# TP1

# Estructura y Funcionamiento

Objetivo: Aplicar un desenfoque gaussiano a una imagen dividiéndola en partes y procesándolas en paralelo con multiprocessing.

1️⃣ Carga y División de la Imagen

Se lee la imagen en escala de grises.
Se divide en 4 partes (o el número de procesos definido).
2️⃣ Procesamiento Paralelo

Se aplican dos enfoques:
🔸 Pipes: Cada proceso aplica el filtro y envía el resultado a través de un Pipe.
🔸 Memoria Compartida: Cada proceso escribe su resultado en una memoria compartida.
3️⃣ Reconstrucción y Guardado

Se combinan los fragmentos procesados y se guarda la imagen final.

# Ejecucion
1.

pip install -r requirements.txt

2.

python3 main.py

# TP2

# Image Processing Server
Este proyecto consiste en un sistema que procesa imágenes en dos etapas utilizando dos servidores. El primer servidor convierte la imagen a escala de grises y el segundo servidor escala la imagen a un tamaño menor. Los dos servidores se ejecutan en segundo plano en la misma terminal y se comunican entre sí para completar el procesamiento de la imagen.

# Estructura del Proyecto
El proyecto consta de tres archivos principales:

main.py: Archivo principal que inicia ambos servidores y procesa la imagen en dos etapas (escala de grises y escalado).
gray_server.py: Servidor encargado de convertir una imagen a escala de grises.
scale_server.py: Servidor encargado de escalar la imagen a un tamaño menor.
test_image.jpeg: Imagen de prueba que se utiliza en el procesamiento.

# Requisitos
Python 3.6 o superior
Librerías de Python necesarias:
aiohttp
Pillow

# Ejecucion
1.

pip install -r requirements.txt

2.

python3 gray_server.py

3.

python3 scale_server.py

4.

python3 main.py
(Si se quiere cambiar la escala, cambiarla en el main donde dice Factor de escala)

