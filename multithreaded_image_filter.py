import cv2
import numpy as np
import signal
from multiprocessing import Process, Array, Lock
import ctypes
import argparse
import os

def cargar_foto(ruta: str, num_partes: int):
    """Carga una foto desde un archivo y la divide en partes iguales."""
    foto = cv2.imread(ruta)
    if foto is None:
        raise ValueError("No se pudo cargar la foto. Verifique la ruta.")
    altura, ancho = foto.shape[:2]

    # Ajuste para asegurar que todas las partes tengan la misma altura
    altura_ajustada = (altura // num_partes) * num_partes
    foto = foto[:altura_ajustada, :]
    altura_partes = altura_ajustada // num_partes
    partes_foto = [foto[i * altura_partes:(i + 1) * altura_partes, :] for i in range(num_partes)]
    return partes_foto

def filtro_gris(imagen):
    """Aplica un filtro en escala de grises a la foto."""
    return cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

def filtro_sepia(imagen):
    """Aplica un filtro sepia a la foto."""
    sepia_kernel = np.array([[0.272, 0.534, 0.131],
                             [0.349, 0.686, 0.168],
                             [0.393, 0.769, 0.189]])
    return cv2.transform(imagen, sepia_kernel)

def aplicar_filtro(parte_foto, funcion_filtro):
    """Aplica una función de filtro a una parte de la foto."""
    return funcion_filtro(parte_foto)

def trabajador(parte_foto, nombre_filtro, array_compartido, indice, bloqueo, forma_parte):
    """Proceso de trabajo que aplica un filtro a una parte de la foto y almacena el resultado en un array compartido."""
    pid = os.getpid()
    print(f"Proceso trabajador (PID: {pid}) iniciado para filtro '{nombre_filtro}'")
    funciones_filtro = {
        'blanco_y_negro': filtro_gris,
        'sepia': filtro_sepia
    }
    funcion_filtro = funciones_filtro.get(nombre_filtro)
    if not funcion_filtro:
        raise ValueError(f"Filtro desconocido: {nombre_filtro}")
    parte_procesada = funcion_filtro(parte_foto)
    parte_aplanada = parte_procesada.flatten()
    with bloqueo:
        inicio = indice * forma_parte[0] * forma_parte[1] * forma_parte[2]
        array_compartido[inicio:inicio + len(parte_aplanada)] = parte_aplanada
    print(f"Proceso trabajador (PID: {pid}) completado.")

def coordinador(num_partes, forma_parte, array_compartido, bloqueo):
    """Combina las partes procesadas de la foto en una sola imagen."""
    print("Proceso coordinador iniciado.")
    imagen_completa = np.zeros((forma_parte[0] * num_partes, forma_parte[1], forma_parte[2]), dtype=np.uint8)
    with bloqueo:
        for i in range(num_partes):
            inicio = i * forma_parte[0] * forma_parte[1] * forma_parte[2]
            fin = inicio + (forma_parte[0] * forma_parte[1] * forma_parte[2])
            parte = np.array(array_compartido[inicio:fin]).reshape(forma_parte)
            imagen_completa[i * forma_parte[0]:(i + 1) * forma_parte[0], :, :] = parte
    print("Proceso coordinador completado.")
    return imagen_completa

def procesar_foto(partes_fotos, nombre_filtro, ruta_salida):
    """Procesa una foto utilizando multiprocessing y guarda el resultado en un archivo."""
    num_partes = len(partes_fotos)
    forma_parte = partes_fotos[0].shape
    array_compartido = Array(ctypes.c_uint8, num_partes * forma_parte[0] * forma_parte[1] * forma_parte[2])
    bloqueo = Lock()

    procesos = []
    print(f"Iniciando {num_partes} procesos de trabajo...")
    for i, parte in enumerate(partes_fotos):
        p = Process(target=trabajador, args=(parte, nombre_filtro, array_compartido, i, bloqueo, forma_parte))
        procesos.append(p)
        p.start()
        print(f"Proceso (PID: {p.pid}) iniciado para la parte {i + 1}.")
    for p in procesos:
        p.join()
        print(f"Proceso (PID: {p.pid}) finalizado.")
    imagen_completa = coordinador(num_partes, forma_parte, array_compartido, bloqueo)
    cv2.imwrite(ruta_salida, imagen_completa)
    print(f"Imagen procesada y guardada como '{ruta_salida}'")

def manejador_interrupciones(signal, frame):
    """Maneja la señal de interrupción para terminar procesos correctamente."""
    print("Interrupción recibida. Terminando procesos...")
    for proceso in procesos:
        proceso.terminate()
        print(f"Proceso (PID: {proceso.pid}) terminado.")
    print("Todos los procesos han sido terminados.")
    exit(0)

signal.signal(signal.SIGINT, manejador_interrupciones)

def main():
    parser = argparse.ArgumentParser(description='Procesamiento de imágenes en paralelo.')
    parser.add_argument('ruta', type=str, help='Ruta a la foto de entrada')
    parser.add_argument('salida', type=str, help='Ruta para guardar la foto de salida')
    parser.add_argument('--filtro', type=str, choices=['blanco_y_negro', 'sepia'], default='sepia',
                        help='Filtro a aplicar a la foto')
    parser.add_argument('--procesos', type=int, default=5, help='Número de procesos paralelos')
    args = parser.parse_args()
    if not os.path.isfile(args.ruta):
        raise ValueError(f"La ruta especificada '{args.ruta}' no es válida o no es un archivo.")
    print(f"Cargando foto desde '{args.ruta}' y dividiéndola en {args.procesos} partes.")
    partes_foto = cargar_foto(args.ruta, args.procesos)
    print("Foto cargada y dividida en partes.")
    print(f"Aplicando filtro '{args.filtro}' a la foto.")
    procesar_foto(partes_foto, args.filtro, args.salida)
    print(f"Proceso completado. Foto guardada como '{args.salida}'.")

if __name__ == '__main__':
    main()
