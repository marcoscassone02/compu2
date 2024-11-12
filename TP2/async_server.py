import os
from aiohttp import web
from PIL import Image
import io

# Ruta donde se almacenarán las imágenes procesadas
OUTPUT_DIR = "imagen_procesada"

async def handle(request):
    """Maneja las solicitudes HTTP de los clientes."""
    try:
        # Espera la imagen
        data = await request.post()
        image_file = data["file"]
        scale_factor = float(data.get("scale_factor", 1))  

        # Guarda la imagen temporalmente
        image_path = f"{OUTPUT_DIR}/temp_image.png"
        with open(image_path, "wb") as f:
            f.write(image_file.file.read())

        # Convertir la imagen a escala de grises
        grayscale_image_path = await convert_to_grayscale(image_path)

        # Ahora, la imagen en escala de grises debe ser pasada al servidor de escalado
        scaled_image_path = await scale_image(grayscale_image_path, scale_factor)

        # Eliminar las imágenes temporales después del procesamiento
        os.remove(image_path)  # Eliminar la imagen original
        os.remove(grayscale_image_path)  # Eliminar la imagen en escala de grises

        # Retornar la ruta de la imagen escalada
        return web.json_response({"status": "success", "file_path": scaled_image_path})

    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)})

async def convert_to_grayscale(image_path):
    """Convierte la imagen a escala de grises."""
    with Image.open(image_path) as img:
        grayscale_img = img.convert("L")
        grayscale_image_path = f"{OUTPUT_DIR}/grayscale_image.png"
        grayscale_img.save(grayscale_image_path)
    return grayscale_image_path

async def scale_image(image_path, scale_factor):
    """Escala la imagen utilizando el factor de escala."""
    with Image.open(image_path) as img:
        width, height = img.size
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        img = img.resize((new_width, new_height))
        scaled_image_path = f"{OUTPUT_DIR}/imagen_final.png"
        img.save(scaled_image_path)
    return scaled_image_path

# Configuración del servidor HTTP
app = web.Application()
app.router.add_post("/upload", handle)

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    web.run_app(app, host='127.0.0.1', port=8080)