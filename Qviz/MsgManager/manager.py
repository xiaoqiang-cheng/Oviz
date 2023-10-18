from types import FunctionType, MethodType
from UltraDict import UltraDict
import getpass
import time
import copy

def get_mac_address():
    import uuid
    node = uuid.getnode()
    mac = uuid.UUID(int = node).hex[-12:]
    return mac


class NodeRegister():
    def __init__(self, name = None, node_type = None):
        # name: username+mac
        if name is None:
            self.name = getpass.getuser() + "_" + get_mac_address()

        if node_type is None:
            self.shared_dict = UltraDict(name=self.name, auto_unlink = False)
            self.shared_dict.setdefault('data', {})
            self.shared_dict.setdefault('timestamp', -1.0)
            self.shared_dict.setdefault('control', False)
            self.shared_dict.setdefault('lock', False)
        self.last_msg_timestamp = -1.0

    def __del__(self):
        self.shared_dict.unlink()
        self.shared_dict.close()

    def sleep(self, ms = 10.0):
        time.sleep(ms / 1000.0)

    def lock(self):
        self.shared_dict['lock'] = True

    def unlock(self):
        self.shared_dict['lock'] = False

    def get_lock_state(self):
        return self.shared_dict['lock']

    def wait_unlock(self):
        while self.get_lock_state():
            self.sleep()

    def set_control(self):
        # self.wait_unlock()
        self.lock()
        self.shared_dict['control'] = True
        self.unlock()

    def set_decontrol(self):
        self.wait_unlock()
        self.lock()
        self.shared_dict['control'] = False
        self.unlock()

    def wait_control(self):
        self.set_decontrol()
        while not self.shared_dict['control']:
            self.sleep()
        self.set_decontrol()

    def has_new_msg(self):
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
        self.wait_unlock()
        self.lock()
        self.shared_dict['timestamp'] = time.time()
        self.shared_dict['data'] = msg
        self.unlock()

    def sub(self):
        if self.has_new_msg():
            self.wait_unlock()
            self.lock()
            msg = copy.deepcopy(self.shared_dict)
            self.unlock()
            return msg
        else:
            return None






