import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('0.0.0.0', 12345))

message = "Hello, server!"
s.sendall(message.encode())

data = s.recv(1024)
print("Received:", data.decode())

s.close()