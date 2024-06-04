import socket
import select
import sys
import json

def broadcast(sock, message, clients, client_names):
    """Send a message to all clients except the sender"""
    for client_socket in clients:
        if client_socket != sock:
            try:
                client_socket.send(message)
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
        read_sockets, write_sockets, error_sockets = select.select([server_socket] + clients, [], [])
        for sock in read_sockets:
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                clients.append(sockfd)
                print("Client (%s, %s) connected" % addr)
            else:
                try:
                    data = sock.recv(4096)
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
                    print(f"Client {addr} disconnected: {error}")
                    sock.close()
                    if sock in clients:
                        clients.remove(sock)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chat_server.py port")
        sys.exit()

    port = int(sys.argv[1])
    chat_server(port)