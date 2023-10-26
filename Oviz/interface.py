from .MsgManager.manager import MiddleManager
from .Utils.common_utils import *
import time
import cv2
from Oviz.Utils.point_cloud_utils import read_pcd, read_bin

group_template = ['template', "sub_1"]

class Oviz:
    _oviz_node = MiddleManager()
    '''
        data:
            group:
                pointcloud: []
                image: []
            group2
    '''

    _data = dict()
    @staticmethod
    def init_oviz_api(ip, port = 12345):
        Oviz._oviz_node.init_oviz_api(ip, port)

    @staticmethod
    def imshow(group = "template", msg = None):
        group_data = Oviz._data.setdefault(group, {})
        topic_data = group_data.setdefault(IMAGE, [])
        if isinstance(msg, str):
            msg_data = cv2.imread(msg)
            topic_data.append(msg_data)
        else:
            topic_data.append(msg)

    @staticmethod
    def pcshow(group = "template", msg = None):
        group_data = Oviz._data.setdefault(group, {})
        topic_data = group_data.setdefault(POINTCLOUD, [])
        if isinstance(msg, str):
            if msg.endswith(".pcd"):
                pc = read_pcd(msg)
            elif msg.endswith(".bin"):
                pc = read_bin(msg)
            topic_data.append(pc)
        else:
            topic_data.append(msg)

    @staticmethod
    def bb3dshow(group = "template", msg = None):
        group_data = Oviz._data.setdefault(group, {})
        topic_data = group_data.setdefault(BBOX3D, [])
        topic_data.append(msg)

    @staticmethod
    def waitKey(cnt = -1):
        Oviz._oviz_node.pub(Oviz._data)
        if cnt < 0:
            Oviz._oviz_node.wait_control()
        else:
            time.sleep(cnt)
        Oviz._data.clear()
