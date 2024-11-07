from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

SERVER_NAME = 'localhost'

def handle_receive(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                # Connection has been closed
                print("Client disconnected.")
                break
            print(f"Client says: {message}")
            if message.startswith("Bye from Client"):
                # Client wants to terminate the connection
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def handle_send(client_socket, server_id):
    while True:
        response = input("You: ")
        client_socket.sendall(response.encode())
        if response == f"Bye from Server {server_id}":
            # Server wants to terminate the connection
            break

def server():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((SERVER_NAME, 12000))
    server_socket.listen(1)
    print("Server is listening on port 12000...")
    
    client_socket, address = server_socket.accept()
    print(f"Connected to client at {address}")
    
    # Receive client ID
    client_id = client_socket.recv(1024).decode()
    print(f'Client says: Hello from Client {client_id}')
    
    server_id = input('Enter your user ID: ')
    client_socket.sendall(server_id.encode())
    print(f"Sent server ID: {server_id}")

    # Create threads for sending and receiving messages
    receive_thread = threading.Thread(target=handle_receive, args=(client_socket,))
    send_thread = threading.Thread(target=handle_send, args=(client_socket, server_id))

    receive_thread.start()
    send_thread.start()

    # Wait for the send thread to finish
    send_thread.join()
    # Close the socket
    client_socket.close()
    server_socket.close()
    print("Server connection closed.")

if __name__ == '__main__':
    server()