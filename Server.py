import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

SERVER_NAME = 'localhost'

def handle_receive(client_socket, stop_event, client_id, session):
    while not stop_event.is_set():
        try:
            message = client_socket.recv(1024)
            if not message:
                print("\nClient disconnected.")
                stop_event.set()
                break
            message = message.decode()
            print(f"\nClient says: {message}")
            if message == f"Bye from Client {client_id}":
                print("Termination message received from client.")
                stop_event.set()
                session.app.exit()
                break
        except ConnectionResetError:
            print("\nConnection was reset by the client.")
            break
        except socket.timeout:
            continue
        except Exception as e:
            print(f"\nError receiving message: {e}")
            stop_event.set()
            session.app.exit()
            break

    # Do not close the socket here

def handle_send(client_socket, stop_event, server_id, session):
    with patch_stdout():
        while not stop_event.is_set():
            try:
                response = session.prompt()
                if stop_event.is_set():
                    break
                client_socket.sendall(response.encode())
                if response == f"Bye from Server {server_id}":
                    print("Termination message sent.")
                    stop_event.set()
                    break
            except EOFError:
                break
            except Exception as e:
                print(f"\nError sending message: {e}")
                stop_event.set()
                break

    # Do not shutdown or close the socket here

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

    client_socket.settimeout(1.0)

    session = PromptSession()
    stop_event = threading.Event()

    # Create threads for sending and receiving messages
    receive_thread = threading.Thread(target=handle_receive, args=(client_socket, stop_event, client_id, session))
    send_thread = threading.Thread(target=handle_send, args=(client_socket, stop_event, server_id, session))

    receive_thread.start()
    send_thread.start()

    # Wait for both threads to finish
    send_thread.join()
    receive_thread.join()

    # Close the client socket and server socket
    client_socket.close()
    server_socket.close()
    print("Server connection closed.")

if __name__ == '__main__':
    server()