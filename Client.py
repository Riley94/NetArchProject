import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import os

def handle_receive(client_socket, stop_event, server_id, session):
    while not stop_event.is_set():
        try:
            response = client_socket.recv(1024)
            if not response:
                print("\nServer disconnected.")
                stop_event.set()
                break
            response = response.decode()
            if response.startswith("READY_TO_RECEIVE_FILE"):
                continue
            elif response.startswith("SENDING_MODIFIED_FILE"):
                # Server is sending back the modified file
                # Receive the file size
                modified_file_size_data = client_socket.recv(1024).decode()
                modified_file_size = int(modified_file_size_data)
                # Receive the file data
                modified_file_data = b''
                while len(modified_file_data) < modified_file_size:
                    data = client_socket.recv(1024)
                    modified_file_data += data
                # Display the modified file content
                print("\nReceived modified file content:")
                print(modified_file_data.decode())
            else:
                print(response)
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
                if message.startswith("SEND_FILE"):
                    # Extract filename
                    parts = message.split()
                    if len(parts) != 2:
                        print("Invalid SEND_FILE command. Usage: SEND_FILE filename")
                        continue
                    filename = parts[1]
                    if not os.path.exists(filename):
                        print(f"File '{filename}' does not exist.")
                        continue
                    # Notify server about file transfer
                    client_socket.sendall(message.encode())
                    # Wait for server's response (handled in handle_receive)
                    # After server sends 'READY_TO_RECEIVE_FILE', proceed to send the file
                    # Open the file and send the data
                    with open(filename, 'rb') as file:
                        file_data = file.read()
                    file_size = len(file_data)
                    file_size_str = str(file_size).zfill(10)
                    print(f"File size: {file_size} bytes")
                    # Send file size
                    client_socket.sendall(file_size_str.encode())
                    # Send file data
                    client_socket.sendall(file_data)
                    print(f"Sent file '{filename}' to server.")
                else:
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
    SERVER_NAME = 'localhost'
    SERVER_PORT = 12000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_NAME, SERVER_PORT))
    print("Connected to the server.")

    client_id = input('Enter your user ID: ')
    client_socket.sendall(client_id.encode())
    print(f"Sent client ID: {client_id}")

    server_id = client_socket.recv(1024).decode()
    print(f"Hello from Server {server_id}.")

    # Send group name to server
    group_name = input('Enter the group name you want to join: ')
    client_socket.sendall(group_name.encode('utf-8'))
    print(f"Requested to join group '{group_name}'.")

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