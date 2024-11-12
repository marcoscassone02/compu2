import requests


def upload_image(image_path, scale_factor):
    url = "http://127.0.0.1:8080/upload"  # Asegúrate de usar la URL correcta
    with open(image_path, 'rb') as f:
        files = {'file': (image_path, f, 'image/jpeg')}
        data = {'scale_factor': scale_factor}
        try:
            response = requests.post(url, files=files, data=data)
            return response.json()  # Asegúrate de que el servidor retorne un JSON
        except requests.exceptions.RequestException as e:
            print(f"Error al enviar la solicitud: {e}")
            return None


def main():
    image_path = 'test_image.jpeg'  # Reemplaza con tu ruta de imagen
    scale_factor = 0.25  # Ajusta el factor de escala según tus necesidades
    
    print(f"Subiendo la imagen desde: {image_path} con factor de escala: {scale_factor}")
    result = upload_image(image_path, scale_factor)

    if result:
        if result['status'] == 'success':
            print(f"Imagen procesada con éxito. Ruta de la imagen escalada: {result['file_path']}")
        else:
            print(f"Error: {result['message']}")
    else:
        print("No se pudo procesar la imagen o el servidor no respondió correctamente.")

if __name__ == "__main__":
    main()