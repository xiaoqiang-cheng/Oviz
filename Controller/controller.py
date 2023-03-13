
import numpy as np
from Utils.point_cloud_utils import *
from View.view import View
from Model.model import Model
from PySide2.QtWidgets import QApplication
import os.path as osp
from Utils.common_utils import *
from log_sys import *
from PySide2.QtCore import QTimer, Qt
import PySide2
import sys
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

class Controller():
    def __init__(self) -> None:
        self.app = QApplication([])
        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside2", palette = DarkPalette))
        self.view = View()
        self.model = Model()
        self.system_online_mode = False

        # vis log timer
        self.Timer = QTimer()
        self.Timer.timeout.connect(self.monitor_timer)
        self.Timer.start(50)

        self.signal_connect()
        send_log_msg(NORMAL, "Qviz 系統开始运行！")


    def signal_connect(self):
        self.view.dock_range_slide.frameChanged.connect(self.update_system_vis)
        self.view.button_select_pointcloud.SelectDone.connect(self.select_pointcloud)
        for key in self.view.image_dock.keys():
            self.view.image_dock[key].SelectDone.connect(self.select_image)

    def select_image(self, topic_path, meta_form):
        send_log_msg(NORMAL, "亲，你选择了图像topic为: %s"%topic_path)
        if self.system_online_mode:
            pass
        else:
            cnt = self.model.deal_image_folder(topic_path, meta_form)
            self.view.set_data_range(self.model.data_frame_list)
            if cnt:
                self.update_system_vis(0)

    def select_pointcloud(self, topic_path, meta_form):
        send_log_msg(NORMAL, "亲，你选择了点云topic为: %s"%topic_path)
        if self.system_online_mode:
            pass
        else:
            cnt = self.model.deal_pointcloud_folder(topic_path, meta_form)
            self.view.set_data_range(self.model.data_frame_list)
            if cnt:
                self.update_system_vis(0)

    def update_system_vis(self, index):
        self.model.get_curr_frame_data(index)
        data_dict = self.model.curr_frame_data
        for topic, data in data_dict.items():
            topic_type, meta_form = self.model.topic_path_meta[topic]
            fun_name = topic_type + "_callback"
            callback_fun = getattr(self, fun_name, None)
            callback_fun(data, topic, meta_form)

        self.view.send_update_vis_flag()

    def run(self):
        self.view.show()
        self.app.exec_()

    def monitor_timer(self):
        get_msg = ret_log_msg()
        if get_msg != []:
            self.view.dock_log_info.display_append_msg_list(get_msg)


    def sigint_handler(self, signum = None, frame = None):
        sys.exit(self.app.exec_())

    def image_callback(self, msg, topic, meta_form):
        self.view.set_image(msg, meta_form)

    def pointcloud_callback(self, msg, topic, meta_form):
        if isinstance(msg, dict):
            self.view.set_point_cloud(msg["data"], show=1)
        else:
            self.view.set_point_cloud(msg[:, 0:3], show=1)
