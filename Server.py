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
            if message.startswith("SEND_FILE"):
                # Client wants to send a file
                parts = message.split()
                if len(parts) != 2:
                    print("Invalid SEND_FILE command from client.")
                    continue
                filename = parts[1]
                # Send acknowledgment to client
                client_socket.sendall("READY_TO_RECEIVE_FILE".encode())
                # Receive file size
                # Receive file size (10 bytes)
                file_size_data = b''
                while len(file_size_data) < 10:
                    chunk = client_socket.recv(10 - len(file_size_data))
                    if not chunk:
                        print("Connection closed while reading file size.")
                        stop_event.set()
                        session.app.exit()
                        return
                    file_size_data += chunk

                file_size = int(file_size_data.decode())
                # Receive file data
                file_data = b''
                while len(file_data) < file_size:
                    data = client_socket.recv(1024)
                    file_data += data
                # Display the file content
                print("\nReceived file content from client:")
                print(file_data.decode())
                # Save the file locally
                with open('received_' + filename, 'wb') as file:
                    file.write(file_data)
                # Append a line to the file
                with open('received_' + filename, 'a') as file:
                    file.write('\nThis is an added line from the server.')
                # Read the modified file
                with open('received_' + filename, 'rb') as file:
                    modified_file_data = file.read()
                modified_file_size = len(modified_file_data)
                # Notify client that modified file is being sent
                client_socket.sendall("SENDING_MODIFIED_FILE".encode())
                # Send modified file size
                client_socket.sendall(str(modified_file_size).encode())
                # Send modified file data
                client_socket.sendall(modified_file_data)
                print(f"Sent modified file 'received_{filename}' back to client.")
            else:
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