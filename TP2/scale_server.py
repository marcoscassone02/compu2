import io
from aiohttp import web
from PIL import Image

async def scale_image(request):
    """Escala la imagen según el factor de escala proporcionado."""
    try:
        data = await request.post()
        image_file = data['image'].file.read()
        scale_factor = float(data.get('scale', 0.5))

        
        image = Image.open(io.BytesIO(image_file))
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        scaled_image = image.resize(new_size)

        
        output = io.BytesIO()
        scaled_image.save(output, format='JPEG')
        output.seek(0)

        
        return web.Response(body=output.read(), content_type='image/jpeg')

    except Exception as e:
        return web.Response(text=f"Error scaling image: {e}", status=500)

async def init_app():
    app = web.Application()
    app.add_routes([web.post('/scale', scale_image)])  
    return app

if __name__ == '__main__':
    web.run_app(init_app(), port=8081) 
