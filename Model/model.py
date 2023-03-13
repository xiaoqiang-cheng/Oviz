from Utils.common_utils import *
from Utils.point_cloud_utils import read_pcd, read_bin
from log_sys import send_log_msg
import os
import cv2

class Model():
    def __init__(self, cfg_path = "Config/global_config.json"):
        # super(Model, self).__init__()
        self.global_cfg_path = cfg_path
        self.global_cfg = parse_json(self.global_cfg_path)
        self.offline_frame_cnt = 0
        self.point_cloud_ext = ".bin"
        self.data_frame_list = []
        # format "key"(only filename like timestamp), "topicname": data
        self.database = {}
        self.topic_path_meta = {}
        self.curr_frame_data = {}

    def get_curr_frame_data(self, index, dim = 4):
        key = self.data_frame_list[index]
        curr_data_dict = self.database[key]
        self.curr_frame_data = {}

        for topic, file in curr_data_dict.items():
            topic_type = self.topic_path_meta[topic][0]
            data_path = os.path.join(topic, file)
            if topic_type == POINTCLOUD:
                pc = self.smart_read_pointcloud(data_path, dim)
                self.curr_frame_data[topic] = pc
            elif topic_type == IMAGE:
                self.curr_frame_data[topic] = self.smart_read_image(data_path)
                # ret[topic] = pc
        send_log_msg(NORMAL, "获取第%d帧数据: %s"%(index, key))
        # return ret

    def smart_read_pointcloud(self, pc_path, dim = 4):
        if self.point_cloud_ext == ".pcd":
            pc = read_pcd(pc_path)
        elif self.point_cloud_ext == ".bin":
            pc = read_bin(pc_path, dim)

        return pc

    def smart_read_image(self, image_path):
        img = cv2.imread(image_path)
        return img

    def deal_image_folder(self, image_path, meta_form):
        datanames = os.listdir(image_path)
        self.topic_path_meta[image_path] = [IMAGE, meta_form]

        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in [".jpg", ".png", ".tiff"]:
                if key not in self.database.keys():
                    self.database[key] = {}
                self.database[key][image_path] = f

        cnt = len(self.database.keys())
        self.data_frame_list = list(self.database.keys())
        self.data_frame_list.sort()
        self.offline_frame_cnt = cnt
        send_log_msg(NORMAL, "共发现了%s格式的文件 %d 帧"%(ext, cnt))
        return cnt

    def deal_pointcloud_folder(self, pc_path, meta_form = 0):
        datanames = os.listdir(pc_path)
        self.topic_path_meta[pc_path] = [POINTCLOUD, meta_form]
        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in [".pcd", ".bin"]:
                self.point_cloud_ext = ext
            else:
                continue

            if key not in self.database.keys():
                self.database[key] = {}
            self.database[key][pc_path] = f

        pc_cnt = len(self.database.keys())
        self.data_frame_list = list(self.database.keys())
        self.data_frame_list.sort()
        self.offline_frame_cnt = pc_cnt
        send_log_msg(NORMAL, "共发现了%s格式的文件 %d 帧"%(self.point_cloud_ext, pc_cnt))
        return pc_cnt




