import threading
from .ultra_middleware import UltraMiddleWare
# from .udp_middleware import UDPMiddleWare
from .tcp_middleware import TCPMiddleWare
import threading

class MiddleManager(threading.Thread):
    def __init__(self, callback_func = None, target_port=None, event = None) -> None:
        super().__init__()
        self.event = event
        self.callback_func = callback_func
        self.init_oviz_api(target_port = target_port)

    def init_oviz_api(self, ip = None, target_port=None):
        if target_port  is None:
            self.default_middleware = UltraMiddleWare()
        else:
            self.default_middleware = TCPMiddleWare(ip, target_port)

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def close(self):
        self.default_middleware.close()

    def set_control(self):
        try:
            self.default_middleware.set_control()
        except:
            pass

    def reset_decontrol(self):
        try:
            self.default_middleware.reset_decontrol()
        except:
            pass

    def pub(self, msg):
        self.default_middleware.pub(msg)

    def is_decontrol(self):
        return self.default_middleware.is_decontrol()

    def run(self):
        while not self.event.is_set():
            msg = self.default_middleware.sub(self.event)
            if msg:
                self.callback_func(msg)
                self.event.wait(0.1)
