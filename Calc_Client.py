# calculator_client.py

import socket

def start_client(host='localhost', port=65432):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, port))
        print(f"[+] Connected to server at {host}:{port}")
        print("Enter mathematical expressions to calculate or 'exit' to quit.")
        while True:
            # Get user input
            expression = input("Enter expression: ")
            if expression.lower() == 'exit':
                client.sendall(expression.encode('utf-8'))
                print("[-] Exiting.")
                break
            # Send the expression to the server
            client.sendall(expression.encode('utf-8'))
            # Receive the result from the server
            result = client.recv(1024).decode('utf-8')
            print(f"Result: {result}")
    except ConnectionRefusedError:
        print("[!] Server is not available.")
    except Exception as e:
        print(f"[!] An error occurred: {e}")
    finally:
        client.close()

if __name__ == '__main__':
    start_client()