import io
from aiohttp import web
from PIL import Image

async def process_image(request):
    """Convierte la imagen a escala de grises."""
    try:
        data = await request.post()
        image_file = data['image'].file.read()

      
        image = Image.open(io.BytesIO(image_file))
        gray_image = image.convert('L')

        
        output = io.BytesIO()
        gray_image.save(output, format='JPEG')
        output.seek(0)

      
        return web.Response(body=output.read(), content_type='image/jpeg')

    except Exception as e:
        return web.Response(text=f"Error processing image: {e}", status=500)

async def init_app():
    app = web.Application()
    app.add_routes([web.post('/process', process_image)])  
    return app

if __name__ == '__main__':
    web.run_app(init_app(), port=8080)  
