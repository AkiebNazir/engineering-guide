# BASIC EXAMPLE: Python Inbuilt socket
# Demonstrates the raw HTTP 101 Handshake mechanism using pure TCP sockets.
import socket
import hashlib
import base64

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 8080))
    server.listen(1)
    print("Listening on 8080...")

    client, addr = server.accept()
    request = client.recv(1024).decode()
    
    # Extract Sec-WebSocket-Key
    key = None
    for line in request.split("\r\n"):
        if line.startswith("Sec-WebSocket-Key: "):
            key = line.split(": ")[1]
            break

    # Compute response hash according to RFC 6455
    magic = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept = base64.b64encode(hashlib.sha1(key.encode() + magic).digest()).decode()

    # Send HTTP 101 Switching Protocols
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    )
    client.send(response.encode())
    print("WebSocket Handshake Complete! Connection upgraded.")
    
if __name__ == "__main__":
    start_server()
