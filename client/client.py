import socket
import sys
import threading
import json
import struct

HEADER_LENGTH = 4

def send_message(sock, message):
    """Send a message with a header indicating its length"""
    message_length = len(message)
    header = struct.pack("!I", message_length)
    sock.sendall(header + message)

def receive_message(sock):
    while True:
        try:
            header = b""
            while len(header) < HEADER_LENGTH:
                packet = sock.recv(HEADER_LENGTH - len(header))
                if not packet:
                    print("Connection closed by the server.")
                    return
                header += packet
            message_length = struct.unpack("!I", header)[0]
            data = b""
            while len(data) < message_length:
                packet = sock.recv(message_length - len(data))
                if not packet:
                    print("Connection closed by the server.")
                    return
                data += packet
            message = json.loads(data.decode())
            if message["type"] == "chat" or message["type"] == "join" or message["type"] == "leave":
                print(f"*** {message['nick']} has joined the chat" if message["type"] == "join" else
                      f"*** {message['nick']} has left the chat" if message["type"] == "leave" else
                      f"{message['nick']}: {message['message']}")
        except socket.timeout:
            continue  # Ignore timeout errors and try again
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

def chat_client(nick, host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    # connect to remote host
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Unable to connect: {e}")
        sys.exit()

    hello_message = json.dumps({"type": "hello", "nick": nick}).encode()
    send_message(sock, hello_message)

    threading.Thread(target=receive_message, args=(sock,)).start()

    while True:
        msg = input(nick + "> ")
        if msg == "/q":
            break
        chat_message = json.dumps({"type": "chat", "message": msg}).encode()
        send_message(sock, chat_message)

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python chat_client.py nickname host port")
        sys.exit()

    nickname = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    chat_client(nickname, host, port)
