from MsgManager.manager import NodeRegister
from Utils.common_utils import *
import time
import cv2

group_template = ['template', "sub_1"]

class Qviz:
    _qviz_node = NodeRegister()
    '''
        data:
            group:
                pointcloud: []
                image: []
            group2
    '''
    _data = dict()
    @staticmethod
    def imshow(group = "template", msg = None):
        group_data = Qviz._data.setdefault(group, {})
        topic_data = group_data.setdefault(IMAGE, [])

        if isinstance(msg, str):
            msg_data = cv2.imread(msg)
            topic_data.append(msg_data)
        else:
            topic_data.append(msg)

    @staticmethod
    def pcshow(group = "template", msg = None):
        group_data = Qviz._data.setdefault(group, {})
        topic_data = group_data.setdefault(POINTCLOUD, [])
        topic_data.append(msg)

    @staticmethod
    def bb3dshow(group = "template", msg = None):
        group_data = Qviz._data.setdefault(group, {})
        topic_data = group_data.setdefault(BBOX3D, [])
        topic_data.append(msg)

    @staticmethod
    def waitKey(cnt = -1):
        Qviz._qviz_node.pub(Qviz._data)
        if cnt < 0:
            Qviz._qviz_node.wait_control()
        else:
            time.sleep(cnt)
        Qviz._data.clear()

if __name__=="__main__":
    import numpy as np
    while True:
        Qviz.imshow(msg=np.zeros((100000)))
        Qviz.waitKey()
        time.sleep(1)

