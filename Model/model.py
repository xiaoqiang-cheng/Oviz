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
        if index >= self.offline_frame_cnt: return 0
        key = self.data_frame_list[index]
        self.curr_frame_data = {}

        for group, subdatabase  in self.database.items():
            self.curr_frame_data[group] = {}
            for meta_form in subdatabase.keys():
                topic_type = self.topic_path_meta[meta_form]
                if key in subdatabase[meta_form].keys():
                    data_path = subdatabase[meta_form][key]
                    if topic_type == POINTCLOUD:
                        self.curr_frame_data[group][meta_form] = self.smart_read_pointcloud(data_path)
                    elif topic_type == IMAGE:
                        self.curr_frame_data[group][meta_form] = self.smart_read_image(data_path)
                    elif topic_type == BBOX3D:
                        self.curr_frame_data[group][meta_form] = self.smart_read_bbox3d(data_path)
        return key

    def remove_sub_database(self, key_str):
        self.database.pop(key_str)
        self.curr_frame_data.pop(key_str)

    def remove_sub_element_database(self, group, ele_key, index):
        # very very dirty and ugly, ready to refactor it
        if index == 0:
            index = ""
        if ele_key == "point_setting":
            self.database[group].pop("Point Cloud%s"%str(index))
            self.curr_frame_data[group].pop("Point Cloud%s"%str(index))
        elif ele_key == "bbox3d_setting":
            self.database[group].pop("3D Bbox%s"%str(index))
            self.curr_frame_data[group].pop("3D Bbox%s"%str(index))

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

    def deal_image_folder(self, group, folder_path, meta_form):
        cnt = self.deal_folder(group, folder_path, meta_form, IMAGE, [".jpg", ".png", ".tiff"])
        return cnt

    def deal_pointcloud_folder(self, group, folder_path, meta_form):
        cnt = self.deal_folder(group, folder_path, meta_form, POINTCLOUD, [".pcd", ".bin"])
        return cnt

    def deal_bbox3d_folder(self, group, folder_path, meta_form):
        cnt = self.deal_folder(group, folder_path, meta_form, BBOX3D, [".txt"])
        return cnt

    def deal_folder(self, group, folder_path, meta_form, TOPIC_META, allowed_extensions):
        database = {}
        database[meta_form] = {}

        self.topic_path_meta[meta_form] = TOPIC_META

        datanames = os.listdir(folder_path)

        for f in datanames:
            key, ext = os.path.splitext(f)
            if ext in allowed_extensions:
                database[meta_form][key] = os.path.join(folder_path, f)

        cnt = len(database[meta_form].keys())
        if cnt > 0:
            self.data_frame_list = sorted(database[meta_form].keys())
            self.offline_frame_cnt = cnt
            send_log_msg(NORMAL, f"共发现了{'、'.join(allowed_extensions)}格式的文件 {cnt} 帧")
            if group in self.database.keys():
                self.database[group].update(database)
            else:
                self.database[group] = database
        return cnt
