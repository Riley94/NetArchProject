from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

def handle_receive(client_socket):
    while True:
        try:
            response = client_socket.recv(1024).decode()
            if not response:
                # Connection closed
                print("Server disconnected.")
                break
            print(f"Server says: {response}")
            if response.startswith("Bye from Server"):
                # Server wants to terminate the connection
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def handle_send(client_socket, client_id):
    while True:
        message = input("You: ")
        client_socket.sendall(message.encode())
        if message == f"Bye from Client {client_id}":
            # Client wants to terminate the connection
            break

def client():
    server_name = 'localhost'
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, 12000))
    print("Connected to the server.")

    client_id = input('Enter your user ID: ')
    client_socket.sendall(client_id.encode())
    print(f"Sent client ID: {client_id}")

    server_id = client_socket.recv(1024).decode()
    print(f"Hello from Server {server_id}.")

    # Create threads for sending and receiving messages
    receive_thread = Thread(target=handle_receive, args=(client_socket,))
    send_thread = Thread(target=handle_send, args=(client_socket, client_id))

    receive_thread.start()
    send_thread.start()

    # Wait for the send thread to finish
    send_thread.join()
    # Close the socket
    client_socket.close()
    print("Client connection closed.")

if __name__ == '__main__':
    client()