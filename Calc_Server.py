# calculator_server.py

import socket
import threading

def handle_client(client_socket, address):
    print(f"[+] New connection from {address}")
    while True:
        try:
            # Receive the calculation request from the client
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                # Client disconnected
                print(f"[-] Connection closed by {address}")
                break
            if data.lower() == 'exit':
                print(f"[-] Client {address} requested to close the connection.")
                break
            print(f"[{address}] Received expression: {data}")

            # Evaluate the expression safely
            result = evaluate_expression(data)
            # Send the result back to the client
            client_socket.sendall(str(result).encode('utf-8'))
        except Exception as e:
            print(f"[!] Error with client {address}: {e}")
            break
    client_socket.close()

def evaluate_expression(expression):
    try:
        # Allowed functions and constants
        allowed_names = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            '__builtins__': {},
        }
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return result
    except Exception as e:
        return f"Error: {e}"

def start_server(host='localhost', port=65432):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[+] Server listening on {host}:{port}")

    try:
        while True:
            client_socket, address = server.accept()
            client_handler = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_handler.start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down.")
    finally:
        server.close()

if __name__ == '__main__':
    start_server()