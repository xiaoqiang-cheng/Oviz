from Utils.common_utils import *
from View.viz_core import Canvas
from log_sys import send_log_msg
from View.custom_widget import *
from View.dock_view import *
import cv2

'''
TODO: 扩展|magic link|filter|在线录
'''
dock_layout_map = {
    "top"    : Qt.TopDockWidgetArea,
    "buttom" : Qt.BottomDockWidgetArea,
    "left"   : Qt.LeftDockWidgetArea,
    "right"  : Qt.RightDockWidgetArea
}

rgb_color_map = {}

class View(QObject):
    pointSizeChanged = Signal(int)
    def __init__(self) -> None:
        super().__init__()
        self.ui = QUiLoader().load('Config/qviz.ui')
        self.canvas_cfg = self.get_user_config("init_canvas_cfg3d.json")
        self.color_map = self.get_user_config("color_map.json")
        self.layout_config = self.get_user_config("layout_config.json")

        self.canvas = Canvas(self.color_map["-2"])
        self.struct_canvas_init(self.canvas_cfg)
        self.ui.setDockNestingEnabled(True)

        self.spliter_dict = {}
        self.dock_log_info = LogDockWidget()
        self.dock_range_slide = RangeSlideDockWidget()
        # need add some layout
        self.control_box_layout_dict = {}
        self.control_box_layout_dict = self.set_control_box()
        self.dock_control_box = ControlBoxDockWidget(layout_dict=self.control_box_layout_dict)

        self.image_dock = {}
        self.point_size = 1


        self.ui.centralwidget.setContentsMargins(0, 0, 0, 0)
        self.ui.centralwidget.layout().setContentsMargins(0,0,0,0)
        self.ui.pointcloud_vis_widget.setContentsMargins(0, 0, 0, 0)

        self.ui.pointcloud_vis_widget_layout.addWidget(self.canvas.native)
        self.ui.pointcloud_vis_widget_layout.setContentsMargins(0, 0, 0, 0)

        # self.add_pointcloud_setting_widget()

        self.add_image_dock_widget(self.layout_config["image_dock_config"])
        self.ui.addDockWidget(Qt.LeftDockWidgetArea, self.dock_log_info)
        self.ui.addDockWidget(Qt.BottomDockWidgetArea, self.dock_range_slide)
        self.ui.addDockWidget(Qt.RightDockWidgetArea, self.dock_control_box)


        self.author_info = QLabel("Author: xiaoqiang")
        self.email_info = QLabel("Email: xiaoqiang.cheng@foxmail.com")
        self.version_label = QLabel("v0.0.1")
        self.ui.statusbar.addWidget(self.author_info, 1)
        self.ui.statusbar.addWidget(self.email_info, 2)
        self.ui.statusbar.addWidget(self.version_label)

        self.ui.installEventFilter(self)  # 将事件过滤器安装到UI对象上

        self.set_car_visible(False)

        self.ui.action_show_slide.triggered.connect(self.show_range_slide)
        self.ui.action_show_log.triggered.connect(self.show_dock_log)
        self.ui.action_show_image.triggered.connect(self.show_dock_image)
        self.ui.action_show_image_titlebar.triggered.connect(self.show_image_titlebar)
        self.ui.action_show_status_bar.triggered.connect(self.show_status_bar)
        self.ui.action_show_control_box.triggered.connect(self.show_control_box)

        self.operation_menu = self.ui.menubar.addMenu("操作")
        self.operation_menu.addAction("保存").setShortcut("Ctrl+S")
        self.operation_menu_triggered = self.operation_menu.triggered[QAction]

        self.load_history_menu = self.ui.menubar.addMenu("历史记录")

        if os.path.exists(DUMP_HISTORY_DIR):
            for pkl_name in os.listdir(DUMP_HISTORY_DIR):
                self.load_history_menu.addAction(pkl_name)
        else:
            self.load_history_menu.addAction("[empty]")
        self.load_history_menu_triggered = self.load_history_menu.triggered[QAction]

        self.dock_control_box.unfold()
        self.mouse_record_screen = False
        self.last_event_type = None

        self.record_screen_image_list = []
        self.record_image_start_time = None
        self.record_screen_save_dir = None


    def create_color_map_widget(self):
        color_id_map_list = QListWidget()
        style_sheet = '''
                QListView::item:selected {
                    color: #FFFFFF;
                    padding: 10px;
                    border-left: 3px solid black;
                }
        '''
        color_id_map_list.setStyleSheet(style_sheet)

        color_id_map_list.clear()
        for c, val in self.color_map.items():
            lw = QListWidgetItem(c)
            lw.setBackground(QColor(val))
            color_id_map_list.addItem(lw)
        return color_id_map_list

    def set_control_box(self):
        ret = dict()

        for key, value in self.layout_config['control_box'].items():
            ret[key] = {}
            ret[key]["layout"] = eval(value['type'])()
            for wk, wv in value["widget"].items():
                ret[key][wk] = eval(wv['type'])(**wv['params'])
                ret[key]["layout"].addWidget(ret[key][wk])

        return ret


    def set_spilter_style(self):
        qss = '''
            QMainWindow::separator {
                width: 1px; /* 设置分隔条宽度 */
                height: 1px; /* 设置分隔条高度 */
            }
        '''
        self.ui.setStyleSheet(qss)

    def get_user_config(self, config_name):
        default_config_file = os.path.join("Config", config_name)
        default_cfg = parse_json(default_config_file)
        user_config_file = os.path.join(USER_CONFIG_DIR, config_name)
        if os.path.exists(user_config_file):
            user_cfg = parse_json(user_config_file)
        else:
            user_cfg = {}
        return rec_exsit_merge(default_cfg, user_cfg)

    def save_last_frame_num(self, num):
        self.layout_config["last_slide_num"] = num

    def save_layout_config(self):
        self.layout_config["image_flag"] = not self.image_flag
        self.layout_config["log_flag"]   = not self.log_flag
        self.layout_config["slide_flag"] = not self.slide_flag
        self.layout_config["status_bar_flag"] = not self.status_bar_flag
        self.layout_config["control_box_flag"] = not self.control_box_flag

        for key in self.canvas_cfg.keys():
            if "camera" in self.canvas_cfg[key].keys():
                self.canvas_cfg[key]['camera'].update(self.canvas.get_canvas_camera(key))


        for key in self.layout_config['image_dock_path'].keys():
            self.layout_config['image_dock_path'][key] = self.image_dock[key].folder_path

        if not os.path.exists(USER_CONFIG_DIR):
            os.mkdir(USER_CONFIG_DIR)

        write_json(self.layout_config, "%s/layout_config.json"%USER_CONFIG_DIR)
        write_json(self.color_map, "%s/color_map.json"%USER_CONFIG_DIR)
        write_json(self.canvas_cfg, "%s/init_canvas_cfg3d.json"%USER_CONFIG_DIR)
        self.save_layout()

    def grab_form(self, frame_name, ext):
        self.record_screen_save_dir = \
            os.path.join(self.control_box_layout_dict['record_screen_setting']['button_select_record_save'].folder_path, self.record_image_start_time)
        if not os.path.exists(self.record_screen_save_dir ):
            os.makedirs(self.record_screen_save_dir)
        image_name = frame_name + "_" + str(time.time()) + ext
        output_path = os.path.join(self.record_screen_save_dir, image_name)
        self.ui.grab().save(output_path, "PNG", quality=100)
        self.record_screen_image_list.append(output_path)

    def export_grab_video(self):
        import matplotlib.pyplot as plt

        video_name = os.path.join(self.control_box_layout_dict['record_screen_setting']['button_select_record_save'].folder_path,
                self.record_image_start_time + ".mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        if len(self.record_screen_image_list) == 0: return

        frame_size = (1280, 720)
        out = cv2.VideoWriter(video_name, fourcc, 10, frame_size)
        plt.figure("Preview")
        for image_path in self.record_screen_image_list:
            img = cv2.imread(image_path)
            if img is not None:
                plt.cla()
                img = cv2.resize(img, frame_size)
                out.write(img)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                plt.axis('off')
                plt.imshow(img)
                plt.pause(0.001)
        plt.close()
        out.release()
        self.record_screen_image_list = []
        self.record_image_start_time = get_wall_time_str()
        os.system("xdg-open %s"%self.control_box_layout_dict['record_screen_setting']['button_select_record_save'].folder_path)

    def revet_layout_config(self):
        for module, value in self.control_box_layout_dict.items():
            for wk, wv in value.items():
                try:
                    wv.revert()
                except:
                    pass

        self.image_flag = self.layout_config["image_flag"]
        self.log_flag = self.layout_config["log_flag"]
        self.slide_flag = self.layout_config["slide_flag"]
        self.status_bar_flag = self.layout_config["status_bar_flag"]
        self.control_box_flag = self.layout_config["control_box_flag"]

        self.show_range_slide()
        self.show_dock_log()
        self.show_dock_image()
        self.show_status_bar()
        self.show_control_box()

        for key, val in self.layout_config['image_dock_path'].items():
            self.image_dock[key].set_topic_path(val)

        self.dock_range_slide.set_frmae_text(self.layout_config["last_slide_num"])
        self.load_layout()

    def save_layout(self):
        p = '%s/layout.ini'%USER_CONFIG_DIR
        with open(p, 'wb') as f:
            s = self.ui.saveState()
            f.write(bytes(s))
            f.flush()

    def load_layout(self):
        p = '%s/layout.ini'%USER_CONFIG_DIR
        if os.path.exists(p):
            with open(p, 'rb') as f:
                s = f.read()
                self.ui.restoreState(s)

    def create_input_dialog(self, title, info):
        inputs_name, ok = QInputDialog.getText(self.ui, title, info, QLineEdit.Normal)
        return inputs_name, ok

    def show_control_box(self):
        if self.control_box_flag:
            self.dock_control_box.show()
        else:
            self.dock_control_box.hide()

        self.control_box_flag = not self.control_box_flag


    def show_range_slide(self):
        if self.slide_flag:
            self.dock_range_slide.show()
        else:
            self.dock_range_slide.hide()

        self.slide_flag = not self.slide_flag

    def show_status_bar(self):
        if self.status_bar_flag:
            self.ui.statusbar.show()
        else:
            self.ui.statusbar.hide()
        self.status_bar_flag = not self.status_bar_flag

    def show_image_titlebar(self):
        for k, v in self.image_dock.items():
            v.set_image_title_bar()

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
            elif event.key() == Qt.Key_P:
                self.canvas.print_3dview_camera_params()
            elif event.key() == Qt.Key_R:
                dock_widget_num = len(self.image_dock.values())
                print("Target Size:", [self.ui.width() / dock_widget_num] * dock_widget_num)
                self.ui.resizeDocks(list(self.image_dock.values()), [self.ui.width() / dock_widget_num] * dock_widget_num, Qt.Horizontal)
                print("main widnows width:", self.ui.width())
                for key, value in self.image_dock.items():
                    print(key, value.width())

            return True

        if self.mouse_record_screen:
            if (event.type() == QEvent.UpdateRequest) and \
                (self.last_event_type in [QEvent.HoverMove, QEvent.Wheel]):
                self.grab_form(self.dock_range_slide.curr_filename.text(), ".png")
        self.last_event_type = event.type()
        return False

    def update_color_map(self, name, color):
        self.color_map[name] = color

    def add_image_dock_widget(self, wimage:dict):
        for n, v in wimage.items():
            self.image_dock[n] = ImageDockWidget(dock_title=n)
            self.ui.addDockWidget(dock_layout_map[v],  self.image_dock[n])


    def struct_canvas_init(self, cfg_dict:dict):
        for key, results in cfg_dict.items():
            if "camera" in results.keys():
                self.canvas.create_view(results["type"], key, results['camera'])
            else:
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
        self.spliter_dict[spliter_name].setStyleSheet("QSplitter {width: 0px; height: 0px; }")

        for w in widget_list:
            self.spliter_dict[spliter_name].addWidget(w)

        for i, f in enumerate(factor_list):
            self.spliter_dict[spliter_name].setStretchFactor(i, f)
        layout_set.addWidget(self.spliter_dict[spliter_name])


    def send_update_vis_flag(self):
        self.dock_range_slide.update_handled = True

    def get_pointsetting(self):
        pt_dim = int(self.control_box_layout_dict['point_setting']['linetxt_point_dim'].text())
        pt_type = self.control_box_layout_dict['point_setting']['linetxt_point_type'].text()
        xyz_dims = list(map(int, self.control_box_layout_dict['point_setting']['linetxt_xyz_dim'].text().split(',')))
        wlh_dims = list(map(int, self.control_box_layout_dict['point_setting']['linetxt_wlh_dim'].text().split(',')))
        color_dims = list(map(int, self.control_box_layout_dict['point_setting']['linetxt_color_dim'].text().split(',')))
        return pt_dim, pt_type, xyz_dims, wlh_dims, color_dims

    def get_bbox3dsetting(self):
        size_dims = list(map(int, self.control_box_layout_dict['bbox3d_setting']['bbox3d_txt_xyzwhlt_dim'].text().split(',')))
        color_dims = list(map(int, self.control_box_layout_dict['bbox3d_setting']['bbox3d_txt_color_dim'].text().split(',')))
        arrow_dims = list(map(int, self.control_box_layout_dict['bbox3d_setting']['bbox3d_txt_arrow_dim'].text().split(',')))
        text_dims = list(map(int, self.control_box_layout_dict['bbox3d_setting']['bbox3d_txt_text_dim'].text().split(',')))
        format_dims = self.control_box_layout_dict['bbox3d_setting']['bbox3d_txt_format_dim'].text()

        return size_dims, color_dims, arrow_dims, text_dims, format_dims

    def rgb_to_hex_numpy(self, rgb_list):
        rgb_array = np.array(rgb_list)
        hex_array = np.zeros((len(rgb_list),), dtype='U7')
        hex_array[:] = '#'
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 0], 16)), 2)
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 1], 16)), 2)
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 2], 16)), 2)
        return hex_array

    def color_str_to_rgb(self, color_str, alpha = 1.0):
        color_int = int(color_str[1:], 16)
        r = (color_int >> 16) & 255
        g = (color_int >> 8) & 255
        b = color_int & 255
        return np.array([r / 255.0, g / 255.0, b / 255.0, alpha])


    def color_id_to_color_list(self, id_list):
        try:
            if id_list.shape[-1] == 1:
                id_list = id_list.reshape(-1).astype(np.int32)
                color_dim = 3
                rgb_color_map = {}
                for key, value in self.color_map.items():
                    rgb_color_map[key] = self.color_str_to_rgb(value)
                    color_dim = len(rgb_color_map[key])
                ret_color = np.zeros((len(id_list), color_dim))
                for key, value in rgb_color_map.items():
                    # TODO bug if key is not int str
                    mask = id_list == int(key)
                    ret_color[mask] = value
                return ret_color, True
            elif (id_list.shape[-1] == 2):
                color_dim = 3
                rgb_color_map = {}
                for key, value in self.color_map.items():
                    rgb_color_map[key] = self.color_str_to_rgb(value)
                    color_dim = len(rgb_color_map[key])
                ret_color = np.zeros((len(id_list), color_dim))
                for key, value in rgb_color_map.items():
                    mask = (id_list[:, 0].astype(np.uint8) == int(key))
                    ret_color[mask] = value
                    ret_color[mask, -1] = np.clip(id_list[mask, -1], 0.0, 1.0)
                return ret_color, True
            elif (id_list.shape[-1] == 3):
                ret_color = np.ones((len(id_list), 4))
                ret_color[:, :3] = np.clip(id_list, 0.0, 1.0)
                return ret_color, True
            elif (id_list.shape[-1] == 4):
                # you must supply normal rgb|a array
                return np.clip(id_list, 0.0, 1.0), True
            else:
                return self.color_map["-1"], True
        except:
            return self.color_map["-1"], False


    def set_color_map_list(self):
        dlg = QColorDialog()
        dlg.setWindowFlags(self.ui.windowFlags() | Qt.WindowStaysOnTopHint)
        item = self.control_box_layout_dict['global_setting']['color_id_map_list'].currentItem()
        if dlg.exec_():
            cur_color = dlg.currentColor()
            if item.background().color() != cur_color:
                item.setBackground(cur_color)
                self.update_color_map(item.text(), cur_color.name())
                if (item.text() == "-2"):
                    self.set_canvas_bgcolor()
                self.control_box_layout_dict["global_setting"]["color_id_map_list"].clearSelection()
                return True
        self.control_box_layout_dict["global_setting"]["color_id_map_list"].clearSelection()
        return False

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
        if mode:
            self.set_car_model_pos()

    def set_car_model_pos(self, x = 0, y = 0, z = 0,
                    r = -90,s = 1):
        mesh = self.canvas.vis_module['car_model']
        mesh.transform.rotate(r, (0, 0, 1))
        mesh.transform.scale((s, s, s))
        # mesh.transform.translate((x, y, z))

    def set_reference_line_visible(self, mode):
        if mode:
            self.set_reference_line()
        self.canvas.set_visible("reference_line", mode)

    def set_bbox3d_visible(self, mode):
        self.canvas.set_visible("bbox3d_line", mode)

    def set_point_cloud(self, points, color = "#00ff00", size = 1):
        # self.canvas.clear_voxel("point_voxel", "view3d")
        self.canvas.draw_point_cloud("point_cloud", points, color, size)

    def set_point_voxel(self, points, w, l, h, face):
        self.canvas.draw_point_voxel("point_voxel", points, w, l, h, face, face)
        self.canvas.draw_voxel_line("voxel_line", points, w, l, h)

    def set_image(self, img, meta_form):
        self.image_dock[meta_form].set_image(img)

    def set_bbox3d(self, bboxes3d, color, arrow, text_info, show_format):
        self.canvas.draw_box3d_line("bbox3d_line", bboxes3d, color)
        # show arrow
        if len(arrow) !=  0:
            self.canvas.set_visible("obj_arrow", True)
            self.set_bbox3d_arrow(bboxes3d, arrow, color)
        else:
            self.canvas.set_visible("obj_arrow", False)

        # show text
        if len(text_info) != 0:
            self.canvas.set_visible("text", True)
            text_pos = bboxes3d[:, 0:3]
            text_pos[:, -1] += 2.0
            text = []
            for txt in text_info:
                text.append(show_format%tuple(txt))
            self.set_bbox3d_text(text_pos, text, (0.5, 0.5, 0.5, 1))
        else:
            self.canvas.set_visible("text", False)

    def set_bbox3d_text(self, pos, txt, color):
        self.canvas.draw_text("text", txt, pos, color)

    def set_bbox3d_arrow(self, bboxes, vel_list, color):
        self.canvas.draw_bbox3d_arrow("obj_arrow", bboxes, vel_list, color)

    def set_reference_line(self):
        self.canvas.draw_reference_line("reference_line")

    def set_canvas_bgcolor(self):
        self.canvas.set_vis_bgcolor(value=self.color_map["-2"])