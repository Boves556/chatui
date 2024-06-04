import socket
import sys
import threading
import json

def receive_message(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("Connection closed by the server.")
                break
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
    sock.send(hello_message)

    threading.Thread(target=receive_message, args=(sock,)).start()

    while True:
        msg = input(nick + "> ")
        if msg == "/q":
            break
        chat_message = json.dumps({"type": "chat", "message": msg}).encode()
        sock.send(chat_message)

    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python chat_client.py nickname host port")
        sys.exit()

    nickname = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    chat_client(nickname, host, port)