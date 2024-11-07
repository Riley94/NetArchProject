from socket import *
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

def handle_receive(client_socket, server_id):
    while True:
        try:
            response = client_socket.recv(1024)
            if not response:
                print("\nServer disconnected.")
                break
            response = response.decode()
            print(f"\nServer says: {response}")
            if response == f"Bye from Server {server_id}":
                print("Termination message received from server.")
                break
        except ConnectionResetError:
            print("\nConnection was reset by the server.")
            break
        except Exception as e:
            print(f"\nError receiving message: {e}")
            break

    # Do not close the socket here

def handle_send(client_socket, client_id):
    session = PromptSession()
    with patch_stdout():
        while True:
            try:
                message = session.prompt()
                client_socket.sendall(message.encode())
                if message == f"Bye from Client {client_id}":
                    print("Termination message sent.")
                    break
            except EOFError:
                break
            except Exception as e:
                print(f"\nError sending message: {e}")
                break

    # Do not shutdown or close the socket here

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
    receive_thread = threading.Thread(target=handle_receive, args=(client_socket, server_id))
    send_thread = threading.Thread(target=handle_send, args=(client_socket, client_id))

    receive_thread.start()
    send_thread.start()

    # Wait for both threads to finish
    send_thread.join()
    receive_thread.join()

    # Close the socket
    client_socket.close()
    print("Client connection closed.")

if __name__ == '__main__':
    client()