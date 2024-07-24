import socket
import struct
import threading

def get_data(clientsocket, stop_event):
    while not stop_event.is_set():
        if data:
            data = clientsocket.recv(8)
            print(struct.unpack('!', data))
        else:
            break
    clientsocket.close()


def send_data(clientsocket, int1, int2):
    data = struct.pack('!II', int1, int2)
    clientsocket.sendall(data)