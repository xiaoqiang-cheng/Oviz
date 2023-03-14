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
import vispy

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

rgb_color_map = {}

class View(QObject):
    pointSizeChanged = Signal(int)
    def __init__(self) -> None:
        super().__init__()
        self.ui = QUiLoader().load('Config/qviz.ui')
        self.color_map =parse_json("Config/color_map.json")
        self.canvas_cfg = parse_json("Config/init_canvas_cfg3d.json")

        self.canvas = Canvas()
        self.struct_canvas_init(self.canvas_cfg)

        self.spliter_dict = {}
        self.dock_log_info = LogDockWidget()
        self.dock_range_slide = RangeSlideDockWidget()

        self.image_dock = {}
        self.point_size = 1

        self.set_qspilter("main_form",
                Qt.Horizontal,
                [self.ui.pointcloud_vis_widget,
                    self.ui.pointcloud_vis_setting_area],
                [7, -1],
                self.ui.centralwidget.layout())

        self.ui.pointcloud_vis_widget_layout.addWidget(self.canvas.native)

        self.add_pointcloud_setting_widget()

        self.add_image_dock_widget(image_dock_config)
        self.ui.addDockWidget(Qt.LeftDockWidgetArea, self.dock_log_info)
        self.ui.addDockWidget(Qt.BottomDockWidgetArea, self.dock_range_slide)

        self.add_list_kind_color()

        self.version_label = QLabel("v0.0.1")
        self.ui.statusbar.addWidget(self.version_label)

        self.ui.installEventFilter(self)  # 将事件过滤器安装到UI对象上

        self.set_car_visible(False)

        self.image_flag = False
        self.log_flag = False
        self.slide_flag = False

        self.ui.action_show_slide.triggered.connect(self.show_range_slide)
        self.ui.action_show_log.triggered.connect(self.show_dock_log)
        self.ui.action_show_image.triggered.connect(self.show_dock_image)

        self.show_range_slide()
        self.show_dock_image()
        self.show_dock_log()



    def show_range_slide(self):
        if self.slide_flag:
            self.dock_range_slide.show()
        else:
            self.dock_range_slide.hide()

        self.slide_flag = not self.slide_flag

    def show_dock_image(self):
        for k, v in self.image_dock.items():
            if self.image_flag:
                v.show()
            else:
                v.hide()
        self.image_flag = not self.image_flag

    def show_dock_log(self):
        if self.log_flag:
            self.dock_log_info.show()
        else:
            self.dock_log_info.hide()
        self.log_flag = not self.log_flag

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ShortcutOverride:
            if event.key() == Qt.Key_Plus:
                self.point_size += 1
                self.pointSizeChanged.emit(self.point_size)
            elif event.key() == Qt.Key_Minus:
                self.point_size -= 1
                if self.point_size < 1:
                    self.point_size = 1
                self.pointSizeChanged.emit(self.point_size)
            return True
        return False


    def add_pointcloud_setting_widget(self):
        self.button_select_pointcloud = FolderSelectWidget(widget_titie="选择点云")
        self.button_select_bbox = FileSelectWidget(widget_titie="选择bbox")

        self.show_voxel_mode = QCheckBox("voxel模式")
        self.checkbox_show_grid = QCheckBox("显示grid")
        self.checkbox_show_car = QCheckBox("显示车模型")
        self.checkbox_online_mode = QCheckBox("保存数据")
        self.checkbox_dump_alldata = QCheckBox("在线模式")


        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.button_select_pointcloud)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.button_select_bbox)

        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.show_voxel_mode)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_show_grid)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_show_car)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_dump_alldata)
        self.ui.pointcloud_vis_setting_frame.layout().addWidget(self.checkbox_online_mode)


    def add_list_kind_color(self):
        self.ui.listwidget_id_color_map.clear()
        for c, val in self.color_map.items():
            lw = QListWidgetItem(c)
            lw.setBackground(QColor(val))
            self.ui.listwidget_id_color_map.addItem(lw)

    def update_color_map(self, name, color):
        self.color_map[name] = color


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
        pt_dim = int(self.ui.linetxt_point_dim.text())
        xyz_dims = list(map(int, self.ui.linetxt_xyz_dim.text().split(',')))
        wlh_dims = list(map(int, self.ui.linetxt_wlh_dim.text().split(',')))
        color_dims = list(map(int, self.ui.linetxt_color_dim.text().split(',')))
        return pt_dim, xyz_dims, wlh_dims, color_dims

    def rgb_to_hex_numpy(self, rgb_list):
        rgb_array = np.array(rgb_list)
        hex_array = np.zeros((len(rgb_list),), dtype='U7')
        hex_array[:] = '#'
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 0], 16)), 2)
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 1], 16)), 2)
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 2], 16)), 2)
        return hex_array

    def color_str_to_rgb(self, color_str):
        color_int = int(color_str[1:], 16)
        r = (color_int >> 16) & 255
        g = (color_int >> 8) & 255
        b = color_int & 255
        return np.array([r / 255.0, g / 255.0, b / 255.0, 1])


    def color_id_to_color_list(self, id_list):
        try:
            if id_list.shape[-1] == 1:
                id_list = id_list.reshape(-1)
                color_dim = 3
                rgb_color_map = {}
                for key, value in self.color_map.items():
                    rgb_color_map[key] = self.color_str_to_rgb(value)
                    color_dim = len(rgb_color_map[key])
                ret_color = np.zeros((len(id_list), color_dim))
                for key, value in rgb_color_map.items():
                    mask = id_list == int(key)
                    ret_color[mask] = value
                return ret_color, True
            elif (id_list.shape[-1] == 3 or id_list.shape[-1] == 4):
                # you must supply normal rgb|a array
                return id_list, True
            else:
                return self.color_map["-1"], True
        except:
            return self.color_map["-1"], False



    def set_data_range(self, listname):
        self.dock_range_slide.set_range(listname)

    def show(self):
        self.ui.show()

    def set_voxel_mode(self, mode):
        self.canvas.set_visible("point_voxel", mode)
        self.canvas.set_visible("voxel_line", mode)
        self.canvas.set_visible("point_cloud", not mode)

    def set_car_visible(self, mode):
        self.canvas.set_visible("car_model", mode)

    def set_point_cloud(self, points, color = "#00ff00", size = 1):
        # self.canvas.clear_voxel("point_voxel", "view3d")
        self.canvas.draw_point_cloud("point_cloud", points, color, size)

    def set_point_voxel(self, points, w, l, h, face):
        self.canvas.draw_point_voxel("point_voxel", points, w, l, h, face, face)
        self.canvas.draw_voxel_line("voxel_line", points, w, l, h)

    def set_image(self, img, meta_form):
        self.image_dock[meta_form].set_image(img)
