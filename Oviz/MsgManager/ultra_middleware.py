from .UltraDict import UltraDict
import getpass
import time
import copy
import platform

def get_mac_address():
    import uuid
    node = uuid.getnode()
    mac = uuid.UUID(int = node).hex[-12:]
    return mac


class UltraMiddleWare():
    def __init__(self, name = None, node_type = None):
        # name: username+mac
        if name is None:
            self.name = getpass.getuser() + "_" + get_mac_address()

        if "Windows" in platform.platform():
            self.shared_dict = UltraDict(name=self.name, auto_unlink = False, shared_lock=True)
        else:
            self.shared_dict = UltraDict(name=self.name, auto_unlink = False)

        self.shared_dict['data'] = {}
        self.shared_dict['timestamp'] = -1.0
        self.shared_dict['control'] = False
        self.last_msg_timestamp = -1.0

    def __del__(self):
        self.close()

    def close(self):
        self.shared_dict.unlink()
        self.shared_dict.close()

    def set_control(self):
        self.shared_dict['control'] = True

    def is_decontrol(self):
        # msg = self.sub()
        return self.shared_dict['control']

    def reset_decontrol(self):
        self.shared_dict['control'] = False

    def _has_new_msg(self):
        try:
            if self.last_msg_timestamp == self.shared_dict['timestamp']:
                return False
            if abs(time.time() - self.shared_dict['timestamp']) > 5.0:
                return False
            self.last_msg_timestamp = self.shared_dict['timestamp']
            return True
        except:
            return False

    def pub(self, msg):
        self.shared_dict['data'] = msg
        self.shared_dict['timestamp'] = time.time()
        self.last_msg_timestamp = self.shared_dict['timestamp']

    def sub(self, event = None):
        while (not self._has_new_msg()):
            if event:
                if event.is_set():
                    return None
                event.wait(0.1)
            else:
                self._sleep()
        msg = copy.deepcopy(self.shared_dict)
        return msg

    def _sleep(self, ms = 10.0):
        time.sleep(ms / 1000.0)

