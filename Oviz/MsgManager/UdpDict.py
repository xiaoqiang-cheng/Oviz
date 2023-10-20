import socket
import pickle
import time

class UDPDict:
    def __init__(self, target_ip, target_port, buffer_size = 10485760) -> None:
        self.target_ip = target_ip
        self.target_port = target_port
        self.buffer_size = buffer_size
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(("0.0.0.0", target_port))

    def pub(self, msg : dict):
        serialized_data = pickle.dumps(msg)
        msg["timestamp"] = time.time()
        self.send_sock.sendto(serialized_data, (self.target_ip, self.target_port))


    def sub(self):
        data, addr = self.recv_sock.recvfrom(self.buffer_size)
        msg = pickle.loads(data)
        return msg



