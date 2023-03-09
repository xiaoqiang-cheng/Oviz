from time import time
from Utils.common_utils import *
from MsgManager.manager import NodeRegister
from PySide2.QtCore import QThread
import time

from log_sys import send_log_msg


class Model(QThread):
    def __init__(self, cfg_path = "Config/global_config.json"):
        super(Model, self).__init__()
        self.global_cfg_path = cfg_path
        self.global_cfg = parse_json(self.global_cfg_path)
        self.subnode = NodeRegister()

    def sub(self, topic, callback):
        self.subnode.sub(topic, callback)

    def unsub(self, topic):
        self.subnode.unsub(topic)

    def pub(self, topoic, data):
        self.subnode.pub(topoic, data)

    def save_global_cfg_when_close(self):
        write_json(self.global_cfg, self.global_cfg_path)

    def run(self):
        while True:
            self.subnode.subspin()
            time.sleep(self.global_cfg["update_sec"])


