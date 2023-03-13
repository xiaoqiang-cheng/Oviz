from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QSplitter, QTreeWidgetItem, QCheckBox,QListWidgetItem
from PySide2.QtCore import QTimer, Qt, QModelIndex
from PySide2.QtGui import QColor
import time
from Utils.common_utils import *
from View.uviz import Canvas
from log_sys import send_log_msg
from View.custom_widget import *
from View.dock_view import *

# 临时配置 需要写成配置文件的

image_dock_config = {
    "rl" : Qt.TopDockWidgetArea,
    "sl": Qt.TopDockWidgetArea,
    "fl": Qt.TopDockWidgetArea,
    "fc": Qt.TopDockWidgetArea,
    "fr": Qt.TopDockWidgetArea,
    "sr": Qt.TopDockWidgetArea,
    "rr":Qt.TopDockWidgetArea

}

color_map = {
    "0" : '#000000',
    "1" : '#00ff00',
    "2" : '#888a85',
    "3" : '#98e1e0',
    "4" : '#98e1e0',
    "5" : '#89e9b2',
    "6" : '#e7d9a1',
    "7" : '#fcaf3e',
    "8" : '#fe9999',
    "9" : '#73d216',
    "10" : '#fce94f',
    "11" : '#3465a4',
    "12" : '#ad7fa8',
    "13" : '#ad7fa8',
    "14" : '#c4a000',
    "15" : '#fce94f',
    "16" : '#fce94f',
    "17" : '#3465a4',
    "18" : '#ad7fa8',
    "19" : '#ad7fa8',
    "20" : '#c4a000',
    "21" : '#fce94f'
}


class View():
    def __init__(self) -> None:
        self.ui = QUiLoader().load('Config/qviz.ui')
        self.canvas_cfg = parse_json("Config/init_canvas_cfg3d.json")
        self.canvas = Canvas()
        self.struct_canvas_init(self.canvas_cfg)

        self.spliter_dict = {}
        self.dock_log_info = LogDockWidget()
        self.dock_range_slide = RangeSlideDockWidget()

        self.image_dock = {}

        self.set_qspilter("main_form",
                Qt.Horizontal,
                [self.ui.pointcloud_vis_frame,
                    self.ui.pointcloud_vis_setting_area],
                [7, -1],
                self.ui.mainwindow_frame.layout())

        self.ui.pointcloud_vis_frame.layout().addWidget(self.canvas.native)

        self.add_pointcloud_setting_widget()


        self.add_image_dock_widget(image_dock_config)
        self.ui.addDockWidget(Qt.LeftDockWidgetArea, self.dock_log_info)
        self.ui.addDockWidget(Qt.BottomDockWidgetArea, self.dock_range_slide)

        self.add_list_kind_color()

        self.version_label = QLabel("v0.0.1")
        self.ui.statusbar.addWidget(self.version_label)



    def add_pointcloud_setting_widget(self):
        self.button_select_pointcloud = FolderSelectWidget(widget_titie="选择点云")
        self.button_select_bbox = FileSelectWidget(widget_titie="选择bbox")

        self.checkbox_show_grid = QCheckBox("显示grid")
        self.checkbox_show_car = QCheckBox("显示车模型")
        self.checkbox_online_mode = QCheckBox("保存数据")
        self.checkbox_dump_alldata = QCheckBox("在线模式")


        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.button_select_pointcloud)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.button_select_bbox)


        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_show_grid)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_show_car)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_dump_alldata)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_online_mode)


    def add_list_kind_color(self):
        self.ui.listwidget_id_color_map.clear()
        for c, val in color_map.items():
            lw = QListWidgetItem(c)
            lw.setBackground(QColor(val))
            self.ui.listwidget_id_color_map.addItem(lw)


    def add_image_dock_widget(self, wimage:dict):
        for n, v in wimage.items():
            self.image_dock[n] = ImageDockWidget(dock_title=n)
            self.ui.addDockWidget(v,  self.image_dock[n])
        # keys_list = list(image_dock_config.keys())
        # for i, d in enumerate(keys_list[:-1]):
        #     self.ui.tabifyDockWidget(self.image_dock[d], self.image_dock[keys_list[i + 1]])

    def struct_canvas_init(self, cfg_dict:dict):
        for key, results in cfg_dict.items():
            self.canvas.create_view(results["type"], key)
            for vis_key, vis_res in results["vis"].items():
                self.canvas.creat_vis(vis_res['type'], vis_key, key)

    def set_qspilter(self, spliter_name,
                        spliter_dir,
                        widget_list,
                        factor_list,
                        layout_set):
        # Qt.Horizontal or v
        self.spliter_dict[spliter_name] = QSplitter(spliter_dir)

        for w in widget_list:
            self.spliter_dict[spliter_name].addWidget(w)

        for i, f in enumerate(factor_list):
            self.spliter_dict[spliter_name].setStretchFactor(i, f)
        layout_set.addWidget(self.spliter_dict[spliter_name])


    def send_update_vis_flag(self):
        self.dock_range_slide.update_handled = True

    def get_pointsetting(self):
        pt_dim = int(self.linetxt_point_dim.text())
        xyz_dims = list(map(int, self.linetxt_xyz_dim.text().split()))
        wlh_dims = list(map(int, self.linetxt_wlh_dim.text().split()))
        color_dims = list(map(int, self.linetxt_color_dim.text().split()))
        return pt_dim, xyz_dims, wlh_dims, color_dims


    def set_data_range(self, listname):
        self.dock_range_slide.set_range(listname)

    def show(self):
        self.ui.show()

    def set_point_cloud(self, points, show, color = "#00ff00", size = 1):
        if show:
            self.canvas.draw_point_cloud("point_cloud", points, color, size)

    def set_image(self, img, meta_form):
        self.image_dock[meta_form].set_image(img)
