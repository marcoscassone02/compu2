import socket
import argparse

def elegir_tramite():
    print("Seleccione el tipo de trámite:")
    print("1. Pago")
    print("2. Reclamo")
    print("3. Consulta")
    while True:
        opcion = input("Ingrese el número de la opción: ")
        if opcion == "1":
            return "pago"
        elif opcion == "2":
            return "reclamo"
        elif opcion == "3":
            return "consulta"
        else:
            print("Opción inválida. Intente de nuevo.")

def main():
    parser = argparse.ArgumentParser(description="Cliente de turnos")
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--tramite', choices=['pago', 'reclamo', 'consulta'], help="Tipo de trámite")
    # Eliminar cliente_id del parser
    args = parser.parse_args()

    tramite = args.tramite or elegir_tramite()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.host, args.port))
        mensaje = f"tramite:{tramite}"
        s.sendall(mensaje.encode())
        print("Esperando a ser atendido por un administrativo...")
        try:
            # Recibir el cliente_id asignado por el servidor
            cliente_id_msg = s.recv(1024).decode()
            if cliente_id_msg.startswith("CLIENTE_ID:"):
                cliente_id = cliente_id_msg.split(":", 1)[1].strip()
                print(f"Su identificador de cliente es: {cliente_id}")
            else:
                print("No se recibió un identificador de cliente válido del servidor.")
                return
            while True:
                respuesta = s.recv(1024).decode()
                if not respuesta:
                    print("La conexión con el servidor se cerró.")
                    break
                print(f"ADMIN: {respuesta}")
                if respuesta.strip().upper() == "FIN":
                    print("La conversación ha finalizado.")
                    break
                # El cliente responde
                mensaje_cliente = input("Usted: ")
                s.sendall(mensaje_cliente.encode())
                if mensaje_cliente.strip().upper() == "FIN":
                    print("Has finalizado la conversación.")
                    break
        except Exception as e:
            print(f"Error en la conversación: {e}")

if __name__ == "__main__":
    main()