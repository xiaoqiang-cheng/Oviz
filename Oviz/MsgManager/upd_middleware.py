import socket
import pickle
import time

class UDPMiddleWare():
    def __init__(self, target_ip, target_port, buffer_size = 10485760) -> None:
        self.target_ip = target_ip
        self.target_port = target_port
        self.buffer_size = buffer_size
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(("0.0.0.0", target_port))
        self.shared_dict.setdefault('data', {})
        self.shared_dict.setdefault('timestamp', -1.0)
        self.shared_dict.setdefault('control', False)
        self.shared_dict.setdefault('lock', False)

    def pub(self, msg):
        self.shared_dict['timestamp'] = time.time()
        self.shared_dict['data'] = msg
        serialized_data = pickle.dumps(self.shared_dict)
        self.send_sock.sendto(serialized_data, (self.target_ip, self.target_port))


    def sub(self):
        data, addr = self.recv_sock.recvfrom(self.buffer_size)
        msg = pickle.loads(data)
        return msg

    def set_control(self):
        self.shared_dict['control'] = True
        serialized_data = pickle.dumps(self.shared_dict)
        self.send_sock.sendto(serialized_data, (self.target_ip, self.target_port))

    def is_decontrol(self):
        msg = self.sub()
        return msg['control']

    def sleep(self, ms = 10.0):
        time.sleep(ms / 1000.0)

    def wait_control(self):
        while not self.is_decontrol():
            self.sleep()


