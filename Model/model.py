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
        self.data_frame_list = []
        self.database = {}
        self.topic_path_meta = {}
        self.curr_frame_data = {}

    def dump_database(self):
        return [self.database, self.topic_path_meta]

    def reload_database(self, model_data):
        self.database, self.topic_path_meta = model_data
        for meta_form, value in self.database.items():
            self.data_frame_list = list(value.keys())
            self.data_frame_list.sort()

    def get_curr_frame_data(self, index):
        key = self.data_frame_list[index]
        self.curr_frame_data = {}
        for meta_form in self.database.keys():
            topic_type = self.topic_path_meta[meta_form]
            if key in self.database[meta_form].keys():
                data_path = self.database[meta_form][key]
                if topic_type == POINTCLOUD:
                    self.curr_frame_data[meta_form] = self.smart_read_pointcloud(data_path)
                elif topic_type == IMAGE:
                    self.curr_frame_data[meta_form] = self.smart_read_image(data_path)
                elif topic_type == BBOX3D:
                    self.curr_frame_data[meta_form] = self.smart_read_bbox3d(data_path)
        return key

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

    def deal_image_folder(self, image_path, meta_form):
        self.database[meta_form] = {}
        self.topic_path_meta[meta_form] = IMAGE

        datanames = os.listdir(image_path)
        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in [".jpg", ".png", ".tiff"]:
                self.database[meta_form][key] = os.path.join(image_path, f)

        cnt = len(self.database[meta_form].keys())
        self.data_frame_list = list(self.database[meta_form].keys())
        self.data_frame_list.sort()
        self.offline_frame_cnt = cnt
        send_log_msg(NORMAL, "共发现了%s格式的文件 %d 帧"%(ext, cnt))
        return cnt

    def deal_pointcloud_folder(self, pc_path, meta_form):
        self.database[meta_form] = {}
        self.topic_path_meta[meta_form] = POINTCLOUD

        datanames = os.listdir(pc_path)
        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in [".pcd", ".bin"]:
                self.database[meta_form][key] = os.path.join(pc_path, f)

        pc_cnt = len(self.database[meta_form].keys())
        self.data_frame_list = list(self.database[meta_form].keys())
        self.data_frame_list.sort()
        self.offline_frame_cnt = pc_cnt
        send_log_msg(NORMAL, "共发现了%s格式的文件 %d 帧"%(ext, pc_cnt))
        return pc_cnt

    def deal_bbox3d_folder(self, pc_path, meta_form):
        self.database[meta_form] = {}
        self.topic_path_meta[meta_form] = BBOX3D

        datanames = os.listdir(pc_path)
        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in [".txt"]:
                self.database[meta_form][key] = os.path.join(pc_path, f)

        cnt = len(self.database[meta_form].keys())
        self.data_frame_list = list(self.database[meta_form].keys())
        self.data_frame_list.sort()
        self.offline_frame_cnt = cnt
        send_log_msg(NORMAL, "共发现了%s格式的文件 %d 帧"%(ext, cnt))
        return cnt



