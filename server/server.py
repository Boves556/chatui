import socket
import select
import sys
import json
import struct

HEADER_LENGTH = 4

def send_message(sock, message):
    """Send a message with a header indicating its length"""
    message_length = len(message)
    header = struct.pack("!I", message_length)
    sock.sendall(header + message)

def receive_message(sock):
    """Receive a message prefixed with a header indicating its length"""
    header = b""
    while len(header) < HEADER_LENGTH:
        packet = sock.recv(HEADER_LENGTH - len(header))
        if not packet:
            return None
        header += packet
    message_length = struct.unpack("!I", header)[0]
    data = b""
    while len(data) < message_length:
        packet = sock.recv(message_length - len(data))
        if not packet:
            return None
        data += packet
    return data

def broadcast(sock, message, clients, client_names):
    """Send a message to all clients except the sender"""
    for client_socket in clients:
        if client_socket != sock:
            try:
                send_message(client_socket, message)
            except Exception as e:
                print(f"Error sending message: {e}")
                client_socket.close()
                clients.remove(client_socket)
                if client_socket in client_names:
                    leave_message = json.dumps({"type": "leave", "nick": client_names[client_socket]}).encode()
                    broadcast(client_socket, leave_message, clients, client_names)
                    del client_names[client_socket]

def chat_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", port))
    server_socket.listen(10)

    clients = []
    client_names = {}

    print(f"Chat server started on port {port}.")

    while True:
        read_sockets, _, _ = select.select([server_socket] + clients, [], [])
        for sock in read_sockets:
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                clients.append(sockfd)
                print(f"Client {addr} connected")
            else:
                try:
                    data = receive_message(sock)
                    if data:
                        json_data = json.loads(data.decode())
                        if json_data["type"] == "hello":
                            client_names[sock] = json_data["nick"]
                            join_message = json.dumps({"type": "join", "nick": json_data["nick"]}).encode()
                            broadcast(sock, join_message, clients, client_names)
                        elif json_data["type"] == "chat":
                            broadcast_message = json.dumps({"type": "chat", "nick": client_names[sock], "message": json_data["message"]}).encode()
                            broadcast(sock, broadcast_message, clients, client_names)
                    else:
                        if sock in clients:
                            clients.remove(sock)
                            leave_message = json.dumps({"type": "leave", "nick": client_names[sock]}).encode()
                            broadcast(sock, leave_message, clients, client_names)
                            del client_names[sock]
                except Exception as error:
                    print(f"Client disconnected: {error}")
                    sock.close()
                    if sock in clients:
                        clients.remove(sock)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py port")
        sys.exit()

    port = int(sys.argv[1])
    chat_server(port)
