import socket
import pickle
import time


class TCPMiddleWare():
    def __init__(self, ip = None, port=12345):
        self.ip = ip
        self.port = port
        self.ending_symbol = b'kxkxkxkxkx'
        self.ending_symbol_length = len(self.ending_symbol)
        self.tcp_socket = None
        self.client_socket = None
        if ip is None:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.bind(("", self.port))
            self.tcp_socket.listen(1)  # 接受一个客户端连接
        else:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
                try:
                    self.client_socket, self.client_address = self.tcp_socket.accept()
                    print("监听成功", self.client_address)
                    self.connect_flag = True
                except:
                    print("监听失败")
            else:
                try:
                    self.client_socket.connect((self.ip, self.port))
                    print("连接成功")
                    self.connect_flag = True
                except:
                    print("连接失败")



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

    def set_control(self):
        self.shared_dict['control'] = True
        self.shared_dict['data'] = {}
        serialized_data = pickle.dumps(self.shared_dict)
        self.client_socket.send(serialized_data)
        self.client_socket.send(self.ending_symbol)

    def is_decontrol(self):
        msg = self.sub()
        return msg['control']

    def reset_decontrol(self):
        pass

    def _sleep(self, ms=10.0):
        time.sleep(ms / 1000.0)

    def close(self):
        print("ready to close tcp")

        if self.tcp_socket:
            print(self.tcp_socket)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host = 'localhost'
            try:
                client_socket.connect((host, self.port))
                client_socket.close()
            except Exception as e:
                print("主动连接结束监听！")

            self.tcp_socket.close()

        if self.client_socket:
            self.client_socket.close()
        print("close done!")


    # def __del__(self):
    #     self.close()

if __name__ == "__main__":
    serv = TCPMiddleWare()
    msg = serv.sub()
    print(msg)
    serv.pub(msg)
    print("done")