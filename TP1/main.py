import cv2
import numpy as np
import multiprocessing as mp
import signal
from scipy.ndimage import gaussian_filter
from multiprocessing import Pipe, Array


NUM_PROCESOS = 4  
IMAGE_PATH = "imagen.jpeg"  


def signal_handler(sig, frame):
    print("Interrupción detectada. Terminando procesos...")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Cargar y dividir la imagen
def cargar_y_dividir_imagen(path, num_partes):
    imagen = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # Cargar en escala de grises
    if imagen is None:
        raise FileNotFoundError("No se pudo cargar la imagen.")
    
    altura, ancho = imagen.shape
    partes = np.array_split(imagen, num_partes, axis=0)  # División horizontal
    return partes, (altura, ancho)

# Aplicar filtro a cada parte
def aplicar_filtro(imagen_parcial):
    return gaussian_filter(imagen_parcial, sigma=5)  # Filtro de desenfoque simple

# Procesamiento paralelo con comunicación

def trabajador(parte, conn):
    resultado = aplicar_filtro(parte)
    conn.send(resultado)
    conn.close()

def procesamiento_paralelo(partes):
    procesos = []
    conexiones = []
    resultados = []
    
    for parte in partes:
        padre, hijo = Pipe()
        proceso = mp.Process(target=trabajador, args=(parte, hijo))
        procesos.append(proceso)
        conexiones.append(padre)
        proceso.start()
        
    
    for proceso, conexion in zip(procesos, conexiones):
        resultados.append(conexion.recv())
        proceso.join()
        
    
    return resultados

# Uso de memoria compartida
def procesamiento_memoria_compartida(partes, altura, ancho):
    altura_parte = altura // NUM_PROCESOS  # Asegura que cada parte tenga el mismo tamaño
    memoria_compartida = Array('B', altura * ancho)  # Array de tamaño total de la imagen
    procesos = []
    
    
    def trabajador_memoria(idx, parte):
        resultado = aplicar_filtro(parte)
        resultado_flat = resultado.flatten()
        inicio = idx * altura_parte * ancho
        fin = inicio + len(resultado_flat)
        memoria_compartida[inicio:fin] = resultado_flat  # Almacena en memoria compartida
        

    for idx, parte in enumerate(partes):
        proceso = mp.Process(target=trabajador_memoria, args=(idx, parte))
        procesos.append(proceso)
        proceso.start()
        

    for proceso in procesos:
        proceso.join()
        

    imagen_final = np.frombuffer(memoria_compartida.get_obj(), dtype=np.uint8).reshape(altura, ancho)
    return imagen_final


# Función principal
def main():
    partes, (altura, ancho) = cargar_y_dividir_imagen(IMAGE_PATH, NUM_PROCESOS)
    
    # Procesamiento con comunicación por Pipes
    resultado_pipes = procesamiento_paralelo(partes)
    imagen_final_pipes = np.vstack(resultado_pipes)
    # cv2.imwrite("resultado_pipes.jpeg", imagen_final_pipes)
    
    # Procesamiento con memoria compartida
    imagen_final_memoria = procesamiento_memoria_compartida(partes, altura, ancho)
    cv2.imwrite("resultado_memoria.jpeg", imagen_final_memoria)
    
    print("Procesamiento completado y resultados guardados.")

if __name__ == "__main__":
    main()