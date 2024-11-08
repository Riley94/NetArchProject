import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

def handle_receive(client_socket, stop_event, server_id, session):
    while not stop_event.is_set():
        try:
            response = client_socket.recv(1024)
            if not response:
                print("\nServer disconnected.")
                stop_event.set()
                break
            response = response.decode()
            print(f"\nServer says: {response}")
            if response == f"Bye from Server {server_id}":
                print("Termination message received from server.")
                stop_event.set()
                session.app.exit()
                break
        except ConnectionResetError:
            print("\nConnection was reset by the server.")
            break
        except socket.timeout:
            continue
        except Exception as e:
            print(f"\nError receiving message: {e}")
            stop_event.set()
            session.app.exit()
            break

    # Do not close the socket here

def handle_send(client_socket, stop_event, client_id, session):
    with patch_stdout():
        while not stop_event.is_set():
            try:
                message = session.prompt()
                if stop_event.is_set():
                    break
                client_socket.sendall(message.encode())
                if message == f"Bye from Client {client_id}":
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

def client():
    server_name = 'localhost'
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_name, 12000))
    print("Connected to the server.")

    client_id = input('Enter your user ID: ')
    client_socket.sendall(client_id.encode())
    print(f"Sent client ID: {client_id}")

    server_id = client_socket.recv(1024).decode()
    print(f"Hello from Server {server_id}.")

    client_socket.settimeout(1.0)

    session = PromptSession()
    stop_event = threading.Event()

    # Create threads for sending and receiving messages
    receive_thread = threading.Thread(target=handle_receive, args=(client_socket, stop_event, server_id, session))
    send_thread = threading.Thread(target=handle_send, args=(client_socket, stop_event, client_id, session))

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