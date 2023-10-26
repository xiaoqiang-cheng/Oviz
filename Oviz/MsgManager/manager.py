import threading
from .ultra_middleware import UltraMiddleWare
from .udp_middleware import UDPMiddleWare
import threading

class MiddleManager(threading.Thread):
    def __init__(self, callback_func = None, event = None) -> None:
        super().__init__()
        self.event = event
        self.callback_func = callback_func

    def init_oviz_api(self, target_ip = None, target_port=None):
        if target_ip  is None:
            self.default_middleware = UltraMiddleWare()
        else:
            self.default_middleware = UDPMiddleWare(target_ip=target_ip,
                    target_port=target_port)

    def set_control(self):
        self.default_middleware.set_control()

    def pub(self, msg):
        self.default_middleware.pub(msg)

    def wait_control(self):
        self.default_middleware.wait_control(self.event)

    def run(self):
        while not self.event.is_set():
            msg = self.default_middleware.sub(self.event)
            self.callback_func(msg)
            self.event.wait(0.1)
