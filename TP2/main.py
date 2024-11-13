import aiohttp
import asyncio

async def send_image_to_gray_server():
    """Envía una imagen al servidor de procesamiento de escala de grises."""
    async with aiohttp.ClientSession() as session:
        
        with open('test_image.jpeg', 'rb') as f:
            image_data = f.read()

        
        data = aiohttp.FormData()
        data.add_field('image', image_data, filename='test_image.jpeg', content_type='image/jpeg')

        async with session.post('http://localhost:8080/process', data=data) as response:
            if response.status == 200:
                gray_image_data = await response.read()
                return gray_image_data
            else:
                print(f"Error al procesar la imagen en escala de grises. Status: {response.status}")
                return None

async def send_image_to_scale_server(gray_image_data):
    """Envía la imagen al servidor de escalado."""
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('image', gray_image_data, filename='gray_image.jpeg', content_type='image/jpeg')
        data.add_field('scale', '0.3')  # Factor de escala 

        async with session.post('http://localhost:8081/scale', data=data) as response:
            if response.status == 200:
                scaled_image_data = await response.read()
                with open('imagen_escalada.jpeg', 'wb') as f:
                    f.write(scaled_image_data)  
                print("Imagen escalada y guardada como 'imagen_escalada.jpeg'.")
            else:
                print(f"Error al escalar la imagen. Status: {response.status}")

async def main():
    
    gray_image_data = await send_image_to_gray_server()

    if gray_image_data:
        
        await send_image_to_scale_server(gray_image_data)

if __name__ == '__main__':
    asyncio.run(main())
