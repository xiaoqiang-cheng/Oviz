import socket
import pickle
import time


class TCPMiddleWare():
    def __init__(self, ip = None, port=12345, buffer_size = 10485760):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.ending_symbol = b'kxkxkxkxkx'
        self.ending_symbol_length = len(self.ending_symbol)
        if ip is None:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.bind(("", self.port))
            self.tcp_socket.listen(1)  # 接受一个客户端连接
            # self.tcp_socket.settimeout(5)
        else:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.client_socket.settimeout(5)

        self.connect_flag = False

        self.shared_dict = {
            'data': {},
            'timestamp': -1.0,
            'control': False
        }

    def check_listen_and_connect_tcp(self):
        if (not self.connect_flag):
            print("ready to connect remote machine...")
            if self.ip is None:
                self.client_socket, self.client_address = self.tcp_socket.accept()
                print("监听成功", self.client_address)
            else:
                self.client_socket.connect((self.ip, self.port))
                print("连接成功")

            self.connect_flag = True

    def pub(self, msg):
        self.check_listen_and_connect_tcp()
        self.shared_dict['timestamp'] = time.time()
        self.shared_dict['data'] = msg
        serialized_data = pickle.dumps(self.shared_dict)
        print(len(serialized_data))
        self.client_socket.send(serialized_data)
        self.client_socket.send(self.ending_symbol)


    def recv(self, buffer):
        data = []
        while True:
            packet = self.client_socket.recv(4096)
            data.append(packet)
            if len(packet) >= self.ending_symbol_length and \
                    packet[-self.ending_symbol_length:] == self.ending_symbol: break
            if len(packet) < self.ending_symbol_length: break
        return data

    def sub(self, event = None):
        self.check_listen_and_connect_tcp()
        if self.client_socket:
            # data = self.client_socket.recv(self.buffer_size)  # 适当调整缓冲区大小
            data = self.recv(4096)
            cvt_data = b"".join(data)
            print(len(cvt_data))
            if cvt_data:
                # msg = pickle.loads(data)
                msg = pickle.loads(cvt_data[:-self.ending_symbol_length])
                return msg
            else:
                self.connect_flag = False
                return None
        return None

    def wait_control(self, event = None):
        while not self._is_decontrol():
            self._sleep()

    def set_control(self):
        self.shared_dict['control'] = True
        self.shared_dict['data'] = {}
        serialized_data = pickle.dumps(self.shared_dict)
        self.client_socket.send(serialized_data)
        self.client_socket.send(self.ending_symbol)

    def _is_decontrol(self):
        msg = self.sub()
        return msg['control']

    def _sleep(self, ms=10.0):
        time.sleep(ms / 1000.0)

    def close(self):
        try:
            self.client_socket.settimeout(0)
            self.client_socket.close()
        except:
            pass

        try:
            self.client_socket.settimeout(0)
            self.tcp_socket.close()
        except:
            pass

    def __del__(self):
        self.close()

if __name__ == "__main__":
    serv = TCPMiddleWare()
    msg = serv.sub()
    print(msg)
    serv.pub(msg)
    print("done")