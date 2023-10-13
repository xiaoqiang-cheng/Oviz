from Utils.common_utils import *
from Utils.point_cloud_utils import read_pcd, read_bin
from log_sys import send_log_msg
import os
import cv2
from MsgManager.manager import NodeRegister


class Model(QThread):
    hasNewMsg = Signal(float)
    def __init__(self):
        super().__init__()
        self.offline_frame_cnt = 0
        self.data_frame_list = []
        self.database = {}
        self.curr_frame_data = {}
        self.qviz_node = NodeRegister()

    def __del__(self):
        self.wait()
        self.quit()

    def run(self):
        while True:
            print("live")
            msg =  self.qviz_node.sub()
            self.curr_frame_data = msg['data']
            print(self.curr_frame_data)
            self.hasNewMsg.emit(msg['timestamp'])

    def get_curr_frame_data(self, index):
        if index >= self.offline_frame_cnt: return 0
        key = self.data_frame_list[index]
        self.curr_frame_data = {}

        for group, subdatabase  in self.database.items():
            self.curr_frame_data[group] = {}
            for topic_type, values in subdatabase.items():
                self.curr_frame_data[group][topic_type] = []
                for value in values:
                    if key in value.keys():
                        data_path = value[key]
                        parse_data = eval("self.smart_read_%s"%topic_type)(data_path)
                        self.curr_frame_data[group][topic_type].append(parse_data)

        return key

    def remove_sub_database(self, key_str):
        self.database.pop(key_str)
        self.curr_frame_data.pop(key_str)

    def remove_sub_element_database(self, group, ele_key, index):
        self.database[group][ele_key].pop(index)
        self.curr_frame_data[group][ele_key].pop(index)

    def smart_read_bbox3d(self, bbox_path):
        return np.loadtxt(bbox_path, dtype=np.float32)

    def smart_read_pointcloud(self, pc_path):
        if pc_path.endswith(".pcd"):
            pc = read_pcd(pc_path)
        elif pc_path.endswith(".bin"):
            pc = read_bin(pc_path)
        return pc

    def smart_read_image(self, image_path):
        img = cv2.imread(image_path)
        return img

    def deal_image_folder(self, group, folder_path, ele_index):
        cnt = self.deal_folder(group, folder_path, ele_index, IMAGE, [".jpg", ".png", ".tiff"])
        return cnt

    def deal_pointcloud_folder(self, group, folder_path, ele_index):
        cnt = self.deal_folder(group, folder_path, ele_index, POINTCLOUD, [".pcd", ".bin"])
        return cnt

    def deal_bbox3d_folder(self, group, folder_path, ele_index):
        cnt = self.deal_folder(group, folder_path, ele_index, BBOX3D, [".txt"])
        return cnt

    def deal_folder(self, group, folder_path, ele_index, topic_type, allowed_extensions):
        latest_database = {}

        datanames = os.listdir(folder_path)

        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in allowed_extensions:
                latest_database[key] = os.path.join(folder_path, f)

        cnt = len(latest_database)
        if cnt > 0:
            self.data_frame_list = sorted(latest_database.keys())
            self.offline_frame_cnt = cnt
            send_log_msg(NORMAL, f"共发现了{'、'.join(allowed_extensions)}格式的文件 {cnt} 帧")

            group_data = self.database.setdefault(group, {})
            topic_data = group_data.setdefault(topic_type, [])

            if ele_index < len(topic_data):
                topic_data[ele_index] = latest_database
            else:
                topic_data.append(latest_database)

        return cnt
