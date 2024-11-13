import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

def broadcast_message(message, sender_socket, group_name, groups):
    with groups_lock:
        for client in groups[group_name]:
            if client != sender_socket:
                try:
                    client.sendall(message.encode('utf-8'))
                except Exception as e:
                    print(f"Error broadcasting to a client: {e}")

def handle_receive(client_socket, stop_event, client_id, session, group_name, groups):
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
                print(f"\n[{group_name}] {client_id} says: {message}")
                # Broadcast the message to other clients in the same group
                broadcast_message(f"{client_id}: {message}", client_socket, group_name, groups)
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
                if response == f"Bye from Server {server_id}":
                    print("Termination message sent.")
                    stop_event.set()
                    break
                client_socket.sendall(response.encode())
                
            except EOFError:
                break
            except Exception as e:
                print(f"\nError sending message: {e}")
                stop_event.set()
                break

    # Do not shutdown or close the socket here

def handle_client(client_socket, stop_event, address, groups):
    session = PromptSession()
    client_id = ''
    server_id = 'Server'

    try:
        # Receive client ID
        client_id = client_socket.recv(1024).decode('utf-8')
        print(f'Client says: Hello from Client {client_id}')
        # Send server ID
        client_socket.sendall(server_id.encode('utf-8'))
        print(f"Sent server ID to Client {client_id}.")

        # Receive group name from client
        group_name = client_socket.recv(1024).decode('utf-8')
        print(f"Client {client_id} wants to join group '{group_name}'.")

        # Add client to the group
        with groups_lock:
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(client_socket)

        # Set a timeout on the socket
        client_socket.settimeout(1.0)

        # Create threads for sending and receiving messages
        receive_thread = threading.Thread(target=handle_receive, args=(client_socket, stop_event, client_id, session, group_name, groups))
        send_thread = threading.Thread(target=handle_send, args=(client_socket, stop_event, server_id, session))

        receive_thread.start()
        send_thread.start()

        # Wait for both threads to finish
        receive_thread.join()
        send_thread.join()
    except Exception as e:
        print(f"Error with client {client_id}: {e}")
    finally:
        # Remove the client socket from the group
        with groups_lock:
            groups[group_name].remove(client_socket)
            if not groups[group_name]:
                del groups[group_name]
        client_socket.close()
        print(f"Connection with Client {client_id} closed.")

def server():
    SERVER_NAME = 'localhost'
    SERVER_PORT = 12000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_NAME, SERVER_PORT))
    server_socket.listen(5)  # Allow up to 5 pending connections
    print(f"Server is listening on port {SERVER_PORT}...")
    client_threads = []
    groups = {}
    global groups_lock
    groups_lock = threading.Lock()

    global stop_event 
    stop_event = threading.Event()

    server_socket.settimeout(1.0)
    
    try:
        while not stop_event.is_set():
            try:
                client_socket, address = server_socket.accept()
                print(f"Connected to client at {address}")

                # Start a new thread to handle the client
                client_thread = threading.Thread(target=handle_client, args=(client_socket, stop_event, address, groups))
                client_thread.start()
                client_threads.append(client_thread)

            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        # Signal all threads to stop
        for thread in client_threads:
            thread.join()
        server_socket.close()
        print("Server connection closed.")

if __name__ == '__main__':
    server()