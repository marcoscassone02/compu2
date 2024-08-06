
# Procesamiento de Imágenes en Paralelo

Este proyecto permite aplicar filtros a una imagen utilizando procesamiento paralelo con Python y OpenCV. Puedes aplicar filtros de blanco y negro o sepia a una imagen dividiéndola en partes y procesándolas en paralelo.

## Requisitos

- Python 3.x
- `virtualenv` (opcional, pero recomendado)

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone git@github.com:marcoscassone02/compu2.git

2. **Crear y activar entorno virtual**
    ```bash
    python3 -m venv env
    source env/bin/activate   # En Windows, usa `env\Scripts\activate`
3. **Instalar dependencias**
    ```bash
    pip install -r requirements.txt
## Uso
1. **Ejecutar el script**
    ```bash
    python3 multithreaded_image_filter.py <ruta_a_imagen_entrada> <ruta_a_imagen_salida> --filtro <blanco_y_negro|sepia> --procesos <numero_de_procesos>
2. **Ejemplo**
    ```bash
    python3 multithreaded_image_filter.py /home/Imagenes/flower.jpg /home/Imágenes/resultado.jpg --filtro blanco_y_negro --procesos 4

