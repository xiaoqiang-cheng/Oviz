from Oviz.Utils.common_utils import *
from .viz_core import Canvas
from Oviz.log_sys import send_log_msg
from .custom_widget import *
from .dock_view import *
import cv2

'''
TODO : 扩展 | magic link | filter | 在线录
'''

class View(QMainWindow):
    pointSizeChanged = Signal(int)
    addNewControlTab = Signal(str)
    removeControlTab = Signal(str)
    addSubControlTab = Signal(str, int)
    removeSubControlTab = Signal(str, int)
    removeImageDock = Signal(int)
    addImageDock = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Oviz")

        appIcon = QIcon(os.path.join(OVIZ_CONFIG_DIR, "oviz.png"))
        self.setWindowIcon(appIcon)

        self.load_system_config()
        self.create_central_widget()
        self.create_dock_widget()
        self.create_status_bar()
        self.create_menu_bar()
        self.set_spilter_style()
        self.point_size = 1
        self.mouse_record_screen = False
        self.last_event_type = None
        self.record_screen_image_list = []
        self.record_image_start_time = None
        self.record_screen_save_dir = None

        self.installEventFilter(self)  # 将事件过滤器安装到UI对象上

    def set_spilter_style(self):
        qss = '''
            QMainWindow::separator {
                width: 1px; /* 设置分隔条宽度 */
                height: 1px; /* 设置分隔条高度 */
            }
        '''
        self.setStyleSheet(qss)

    def load_system_config(self):
        self.canvas_cfg = self.get_user_config("init_canvas_cfg3d.json")
        self.color_map = self.get_user_config("color_map.json")
        self.layout_config = self.get_user_config("layout_config.json")
        self.menu_bar_config = self.get_user_config("menu_bar.json")
        self.status_bar_config = self.get_user_config("status_bar.json")


    def create_central_widget(self):
        self.canvas_cfg_set = {}
        self.canvas = Canvas(self.color_map["-2"])
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(QHBoxLayout())
        self.central_widget.layout().addWidget(self.canvas.native)
        self.central_widget.layout().setContentsMargins(0, 0, 0, 0)

    def create_dock_widget(self):
        self.image_dock = []
        self.setDockNestingEnabled(True)
        self.dock_log_info = LogDockWidget()
        self.dock_range_slide = RangeSlideDockWidget()
        self.dock_global_control_box_layout_dict = self.set_global_control_box()
        self.dock_global_control_box = ControlBoxDockWidget(title="GlobalSetting", layout_dict=self.dock_global_control_box_layout_dict)

        # need add some layout
        self.dock_element_control_box_layout_dict = self.set_control_box()
        self.dock_element_control_box = ControlTabBoxDockWidget(title="ElementSetting", layout_dict=self.dock_element_control_box_layout_dict)

        self.create_image_dock_widgets(self.layout_config["image_dock_path"])
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_range_slide)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_global_control_box)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_element_control_box)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_log_info)

        self.dock_element_control_box.unfold()
        self.dock_global_control_box.unfold()

        self.dock_element_control_box.addSubControlBox.connect(self.add_sub_control_box_tab)
        self.dock_element_control_box.removeSubControlBox.connect(self.remove_sub_control_box_tab)
        self.dock_element_control_box.add_control_tab_button.clicked.connect(self.add_control_box_tab)
        self.dock_element_control_box.tabwidget.tabCloseRequested.connect(self.remove_control_box_tab)

    def create_menu_bar(self):
        self.menubar = self.menuBar()

        for key, value in self.menu_bar_config.items():
            _menu = self.menubar.addMenu(key)
            for e, s in value[0].items():
                action = _menu.addAction(e)
                action.setShortcut(s)
            _menu.triggered[QAction].connect(eval(value[1]))

        self.load_history_menu = self.menubar.addMenu("历史记录")

        if os.path.exists(DUMP_HISTORY_DIR):
            for pkl_name in os.listdir(DUMP_HISTORY_DIR):
                self.load_history_menu.addAction(pkl_name)
        else:
            self.load_history_menu.addAction("[empty]")
        self.load_history_menu_triggered = self.load_history_menu.triggered[QAction]
        self.load_history_menu_triggered.connect(self.reload_database)
        self.menubar.setMaximumHeight(1)

    def show_menu_bar(self):
        if self.menubar.height() < 10:
            self.menubar.setMaximumHeight(50)
        else:
            self.menubar.setMaximumHeight(1)

    def create_status_bar(self):
        self.statusbar = self.statusBar()
        for key, value in self.status_bar_config.items():
            tmp_widget = eval(value['type'])(**value['params'])
            tmp_widget.setOpenExternalLinks(True)
            self.statusbar.addWidget(tmp_widget, value['stretch'])

    def menu_bar_trigger_view(self, q):
        trigger_map = {
            "显示图片"      : self.show_dock_image,
            "显示日志"      : self.dock_log_info.toggle_hide,
            "显示进度条"     : self.dock_range_slide.toggle_hide,
            "显示元素控制台" : self.dock_element_control_box.toggle_hide,
            "显示全局控制台" : self.dock_global_control_box.toggle_hide,
            "显示图片标题栏" : self.show_dock_image_title,
            "显示状态栏"    : self.show_status_bar,
            "显示菜单栏"    : self.show_menu_bar
        }
        trigger_map[q.text()]()

    def update_config_buffer(self):
        for key in self.canvas_cfg.keys():
            if "camera" in self.canvas_cfg[key].keys():
                self.canvas_cfg[key]['camera'].update(self.canvas.get_canvas_camera("template"))
        # for key in self.layout_config['image_dock_path'].keys():
        #     self.layout_config['image_dock_path'][key] = self.image_dock[key].folder_path
        self.save_last_frame_num()

    def save_history_database(self):
        name, ok = self.create_input_dialog("提示", "请输入数据名称")
        if ok:
            self.update_config_buffer()
            history_config = {}
            history_config['layout_config.json'] = self.layout_config
            history_config['init_canvas_cfg3d.json'] = self.canvas_cfg
            history_config['layout.ini'] = self.saveState()
            serialize_data(history_config, os.path.join(DUMP_HISTORY_DIR, name))

    def reload_database(self, q):
        target_pkl_path = os.path.join(DUMP_HISTORY_DIR, q.text())
        history_config = deserialize_data(target_pkl_path)
        for key, value in history_config.items():
            target_path = os.path.join(USER_CONFIG_DIR, key)
            if key != "layout.ini":
                write_json(value, "%s"%target_path)
            else:
                with open(target_path, 'wb') as f:
                    f.write(bytes(value))
                    f.flush()
        os.system("oviz&")

    def menu_bar_trigger_operation(self, q):
        if q.text() == "保存":
            self.save_history_database()
        elif q.text() == "自动播放":
            self.dock_range_slide.toggle_state()
        elif q.text() == "上一帧":
            self.dock_range_slide.last_frame()
        elif q.text() == "下一帧":
            self.dock_range_slide.next_frame()

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
        for key, value in self.layout_config['element_control_box'].items():
            ret[key] = self.set_element_box(value, key)
        return ret

    def set_sub_element_box(self, value):
        ret = {}
        ret["layout"] = eval(value['type'])()
        for wk, wv in value["widget"].items():
            ret[wk] = eval(wv['type'])(**wv['params'])
            ret["layout"].addWidget(ret[wk])
        return ret

    def set_element_box(self, element_dict, group="template"):
        ret = dict()
        self.canvas_cfg_set[group] = self.canvas_cfg['view3d']
        self.struct_single_canvas(self.canvas, self.canvas_cfg['view3d'], group)
        for key, value in element_dict.items():
            if isinstance(value, list):
                ret[key] = []
                for val in value:
                    tmp = self.set_sub_element_box(val)
                    ret[key].append(tmp)
            else:
                ret[key] = self.set_sub_element_box(value)
        return ret

    def add_sub_control_box_tab(self, ele_key):
        parent_key = self.get_curr_control_box_name()
        target_index = len(self.layout_config['element_control_box'][parent_key][ele_key])
        template = copy.deepcopy(self.layout_config['element_control_box'][parent_key][ele_key][0])
        self.layout_config['element_control_box'][parent_key][ele_key].append(template)
        sub_element_widget = self.set_sub_element_box(template)
        self.dock_element_control_box_layout_dict[parent_key][ele_key].append(sub_element_widget)
        self.dock_element_control_box.boxes[parent_key][ele_key].add_single_box(target_index, sub_element_widget)
        self.addSubControlTab.emit(ele_key, target_index)

    def remove_sub_control_box_tab(self, ele_key, index):
        if index == 0:
            send_log_msg(ERROR, "template can not be remove")
        else:
            parent_key = self.get_curr_control_box_name()
            self.layout_config['element_control_box'][parent_key][ele_key].pop(index)
            self.dock_element_control_box.boxes[parent_key][ele_key].remove_single_box(index)
        self.removeSubControlTab.emit(ele_key, index)

    def add_control_box_tab(self):
        target_index = len(self.dock_element_control_box_layout_dict.keys())
        target_key = "sub_%s"%(target_index)
        self.layout_config['element_control_box'][target_key] = copy.deepcopy(self.layout_config['element_control_box']["template"])
        subwidget = self.set_element_box(self.layout_config['element_control_box'][target_key], target_key)
        self.dock_element_control_box_layout_dict[target_key] = subwidget
        self.dock_element_control_box.add_tab_widget(target_key, subwidget)
        self.dock_element_control_box.tabwidget.setCurrentIndex(target_index)
        self.addNewControlTab.emit(target_key)

    def remove_control_box_tab(self, index):
        if index == 0:
            send_log_msg(ERROR, "template can not be remove")
            return
        key = self.dock_element_control_box.tabwidget.tabText(index)
        self.layout_config['element_control_box'].pop(key)
        self.dock_element_control_box_layout_dict.pop(key)
        self.dock_element_control_box.remove_tab_widget(index)
        self.canvas_cfg_set.pop(key)
        self.canvas.pop_view(key)
        self.removeControlTab.emit(key)


    def set_global_control_box(self):
        ret = dict()

        for key, value in self.layout_config['global_control_box'].items():
            ret[key] = {}
            ret[key]["layout"] = eval(value['type'])()
            for wk, wv in value["widget"].items():
                ret[key][wk] = eval(wv['type'])(**wv['params'])
                ret[key]["layout"].addWidget(ret[key][wk])

        return ret

    def get_user_config(self, config_name):
        default_config_file = os.path.join(OVIZ_CONFIG_DIR, config_name)
        default_cfg = parse_json(default_config_file)
        user_config_file = os.path.join(USER_CONFIG_DIR, config_name)
        if os.path.exists(user_config_file):
            user_cfg = parse_json(user_config_file)
        else:
            user_cfg = {}
        return rec_merge_map_list(default_cfg, user_cfg)

    def save_last_frame_num(self):
        self.layout_config["last_slide_num"] = self.dock_range_slide.get_curr_index()

    def save_layout_config(self):
        self.update_config_buffer()

        if not os.path.exists(USER_CONFIG_DIR):
            os.mkdir(USER_CONFIG_DIR)
        write_json(self.layout_config, "%s/layout_config.json"%USER_CONFIG_DIR)
        write_json(self.color_map, "%s/color_map.json"%USER_CONFIG_DIR)
        write_json(self.canvas_cfg, "%s/init_canvas_cfg3d.json"%USER_CONFIG_DIR)
        self.save_layout()

    def grab_form(self, frame_name, ext):
        self.record_screen_save_dir = \
            os.path.join(self.dock_global_control_box_layout_dict['record_screen_setting']['folder_path'].folder_path, self.record_image_start_time)
        if not os.path.exists(self.record_screen_save_dir ):
            os.makedirs(self.record_screen_save_dir)
        image_name = frame_name + "_" + str(time.time()) + ext
        output_path = os.path.join(self.record_screen_save_dir, image_name)
        self.grab().save(output_path, "PNG", quality=100)
        self.record_screen_image_list.append(output_path)

    def export_grab_video(self):
        import matplotlib.pyplot as plt

        video_name = os.path.join(self.dock_global_control_box_layout_dict['record_screen_setting']['folder_path'].folder_path,
                self.record_image_start_time + ".mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        if len(self.record_screen_image_list) == 0: return

        frame_size = (self.width(), self.height())
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
        os.system("xdg-open %s"%self.dock_global_control_box_layout_dict['record_screen_setting']['folder_path'].folder_path)

    def revet_layout_config(self):
        group_index = 0
        for module, value in self.dock_element_control_box_layout_dict.items():
            self.dock_element_control_box.tabwidget.setCurrentIndex(group_index)
            group_index += 1
            for tk, tws in value.items():
                for ele_index, tw in enumerate(tws):
                    self.dock_element_control_box.boxes[module][tk].tab_widget.setCurrentIndex(ele_index)
                    for wk, wv in tw.items():
                        try:
                            wv.revert()
                        except Exception as e:
                            pass

        for tk, tw in self.dock_global_control_box_layout_dict.items():
            for wk, wv in tw.items():
                try:
                    wv.revert()
                except:
                    pass

        for i, val in enumerate(self.layout_config['image_dock_path']):
            self.image_dock[i].set_topic_path(val['default_value']['value'])

        self.load_layout()
        self.dock_range_slide.set_frmae_text(self.layout_config["last_slide_num"])

    def closeEvent(self, e):
        print("ready to close ui")
        e.accept()
        self.save_layout_config()

    def save_layout(self):
        p = '%s/layout.ini'%USER_CONFIG_DIR
        with open(p, 'wb') as f:
            s = self.saveState()
            f.write(bytes(s))
            f.flush()

    def load_layout(self):
        p = '%s/layout.ini'%USER_CONFIG_DIR
        if os.path.exists(p):
            with open(p, 'rb') as f:
                s = f.read()
                self.restoreState(s)

    def create_input_dialog(self, title, info):
        inputs_name, ok = QInputDialog.getText(self, title, info, QLineEdit.Normal)
        return inputs_name, ok

    def show_status_bar(self):
        if self.statusbar.isVisible():
            self.statusbar.hide()
        else:
            self.statusbar.show()

    def show_dock_image(self):
        for v in self.image_dock:
            v.toggle_hide()
        dock_widget_num = len(self.image_dock)
        self.resizeDocks(list(self.image_dock), [self.width() / dock_widget_num] * dock_widget_num, Qt.Horizontal)
        self.resizeDocks(list(self.image_dock), [list(self.image_dock)[0].height()] * dock_widget_num, Qt.Vertical)

    def show_dock_image_title(self):
        for v in self.image_dock:
            v.set_image_title_bar()

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
            elif event.key() == Qt.Key_R:
                dock_widget_num = len(self.image_dock)
                print("Target Size:", [self.width() / dock_widget_num] * dock_widget_num)
                self.resizeDocks(list(self.image_dock), [self.width() / dock_widget_num] * dock_widget_num, Qt.Horizontal)
                self.resizeDocks(list(self.image_dock), [list(self.image_dock)[0].height()] * dock_widget_num, Qt.Vertical)
                print("main widnows width:", self.width())
                for i, value in enumerate(self.image_dock):
                    print(i, value.width())

            return True

        if self.mouse_record_screen:
            if (event.type() == QEvent.UpdateRequest) and \
                (self.last_event_type in [QEvent.HoverMove, QEvent.Wheel]):
                self.grab_form(self.dock_range_slide.curr_filename.text(), ".png")
        self.last_event_type = event.type()
        return False

    def update_color_map(self, name, color):
        self.color_map[name] = color

    def create_image_dock_widgets(self, wimage:dict):
        for n, v in enumerate(wimage):
            self.add_single_image_dock(v)

    def add_single_image_dock(self, params = {}):
        curr_cnt = len(self.image_dock)
        self.image_dock.append(ImageDockWidget(dock_title=str(curr_cnt), **params))
        self.addDockWidget(Qt.TopDockWidgetArea,  self.image_dock[-1])
        self.image_dock[-1].addNewImageDock.connect(self.dynamic_add_image_dock)
        self.image_dock[-1].removeCurrImageDock.connect(self.dynamic_remove_image_dock)




        # for i, val in enumerate(self.image_dock):
        #     val.set_title(str(i))

    def dynamic_add_image_dock(self, index):
        # image_dock_config =
        self.layout_config['image_dock_path'].append(self.layout_config['image_dock_path'][index])
        self.add_single_image_dock(self.layout_config['image_dock_path'][-1])
        self.addImageDock.emit(len(self.image_dock) - 1)

    def dynamic_remove_image_dock(self, index):
        if index == 0: return
        del_widget = self.image_dock.pop(index)
        del_widget.deleteLater()
        self.layout_config['image_dock_path'].pop(index)

        for i, val in enumerate(self.image_dock):
            val.set_title(str(i))

        self.removeImageDock.emit(index)


    def link_camera(self, canvas, group):
        key = list(self.canvas_cfg_set.keys())
        if len(key) >= 2:
            canvas.view_panel[group].camera.link(
                    canvas.view_panel['template'].camera)

    def struct_canvas_init(self, canvas, cfg_dict:dict):
        for key, results in cfg_dict.items():
            self.struct_single_canvas(canvas, results, key)

    def struct_single_canvas(self, canvas, results, group):
        if "camera" in results.keys():
            canvas.create_view(results["type"], group, results['camera'])
        else:
            canvas.create_view(results["type"], group)
        for vis_key, vis_res in results["vis"].items():
            if "params" in vis_res.keys():
                canvas.creat_vis(vis_res['type'], group + "_" + vis_key, group, vis_res['params'])
            else:
                canvas.creat_vis(vis_res['type'], group + "_" + vis_key, group)

        if self.dock_global_control_box_layout_dict['global_setting']["checkbox_unlink_3dviz"].isChecked():
            return
        self.link_camera(canvas, group)

    def send_update_vis_flag(self):
        self.dock_range_slide.update_handled = True

    def get_curr_control_box_name(self):
        curr_index = self.dock_element_control_box.tabwidget.currentIndex()
        return self.dock_element_control_box.tabwidget.tabText(curr_index)

    def get_curr_sub_element_index(self, group, key):
        return self.dock_element_control_box.boxes[group][key].tab_widget.currentIndex()

    def get_curr_sub_element_count(self,  group, key):
        return self.dock_element_control_box.boxes[group][key].tab_widget.count()

    def get_remote_api_setting(self):
        curr_widget = self.dock_global_control_box_layout_dict['remote_api_setting']
        port = curr_widget['linetxt_target_port'].text()

        return int(port)

    def get_pointsetting(self, index = 0):
        topic_type = POINTCLOUD
        curr_widget_key = self.get_curr_control_box_name()
        curr_element_dict = self.dock_element_control_box_layout_dict[curr_widget_key]

        pt_dim = int(curr_element_dict[topic_type][index]['linetxt_point_dim'].text())
        pt_type = curr_element_dict[topic_type][index]['linetxt_point_type'].text()
        xyz_dims = list(map(int, curr_element_dict[topic_type][index]['linetxt_xyz_dim'].text().split(',')))
        wlh_dims = list(map(int, curr_element_dict[topic_type][index]['linetxt_wlh_dim'].text().split(',')))
        color_dims = list(map(int, curr_element_dict[topic_type][index]['linetxt_color_dim'].text().split(',')))
        show_voxel = curr_element_dict[topic_type][index]['show_voxel_mode'].isChecked()

        # show_voxel = self.dock_global_control_box_layout_dict['global_setting']['show_voxel_mode'].isChecked()
        return pt_dim, pt_type, xyz_dims, wlh_dims, color_dims, show_voxel

    def get_bbox3dsetting(self, index = 0):
        topic_type = BBOX3D
        curr_widget_key = self.get_curr_control_box_name()
        curr_element_dict = self.dock_element_control_box_layout_dict[curr_widget_key]

        size_dims = list(map(int, curr_element_dict[topic_type][index]['bbox3d_txt_xyzwhlt_dim'].text().split(',')))
        color_dims = list(map(int, curr_element_dict[topic_type][index]['bbox3d_txt_color_dim'].text().split(',')))
        arrow_dims = list(map(int, curr_element_dict[topic_type][index]['bbox3d_txt_arrow_dim'].text().split(',')))
        text_dims = list(map(int, curr_element_dict[topic_type][index]['bbox3d_txt_text_dim'].text().split(',')))
        format_dims = curr_element_dict[topic_type][index]['bbox3d_txt_format_dim'].text()

        return size_dims, color_dims, arrow_dims, text_dims, format_dims

    def rgb_to_hex_numpy(self, rgb_list):
        rgb_array = np.array(rgb_list)
        hex_array = np.zeros((len(rgb_list),), dtype='U7')
        hex_array[:] = '#'
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 0], 16)), 2)
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 1], 16)), 2)
        hex_array += np.char.zfill(np.char.upper(np.base_repr(rgb_array[:, 2], 16)), 2)
        return hex_array

    def color_id_to_color_list(self, id_list):
        try:
            if id_list.shape[-1] == 1:
                id_list = id_list.reshape(-1).astype(np.int32)
                color_dim = 3
                rgb_color_map = {}
                for key, value in self.color_map.items():
                    rgb_color_map[key] = color_str_to_rgb(value)
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
                    rgb_color_map[key] = color_str_to_rgb(value)
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
        dlg.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        item = self.dock_global_control_box_layout_dict['global_setting']['color_id_map_list'].currentItem()
        if dlg.exec_():
            cur_color = dlg.currentColor()
            if item.background().color() != cur_color:
                item.setBackground(cur_color)
                self.update_color_map(item.text(), cur_color.name())
                if (item.text() == "-2"):
                    self.set_canvas_bgcolor()
                self.dock_global_control_box_layout_dict["global_setting"]["color_id_map_list"].clearSelection()
                return True
        self.dock_global_control_box_layout_dict["global_setting"]["color_id_map_list"].clearSelection()
        return False

    def set_data_range(self, listname):
        self.dock_range_slide.set_range(listname)

    def set_voxel_mode(self, mode, group = "template"):
        self.canvas.set_visible(group + "_" +"point_voxel", mode)
        self.canvas.set_visible(group + "_" +"voxel_line", mode)
        self.canvas.set_visible(group + "_" +"point_cloud", not mode)

    def set_car_visible(self, mode):
        for group in self.canvas_cfg_set.keys():
            self.canvas.set_visible(group + "_" + "car_model", mode)
            if mode:
                self.set_car_model_pos(group = group)

    def set_car_model_pos(self, x = 0, y = 0, z = 0,
                    r = 90, s = 1, group="template"):
        mesh = self.canvas.vis_module[group + "_" +'car_model']
        mesh.transform.rotate(r, (0, 0, 1))

    def set_reference_line_visible(self, mode):
        for group in self.canvas_cfg_set.keys():
            self.set_reference_line(group)
            self.canvas.set_visible(group + "_" + "reference_line", mode)

    def set_bbox3d_visible(self, mode, group="template"):
        self.canvas.set_visible(group + "_" + "bbox3d_line", mode)

    def set_bbox3d_text_visible(self, mode, group="template"):
        self.canvas.set_visible(group + "_" + "text", mode)

    def set_point_cloud_visible(self, mode, group="template"):
        self.canvas.set_visible(group + "_" + "point_cloud", mode)

    def set_point_voxel_visible(self, mode, group="template"):
        self.canvas.set_visible(group + "_" + "point_voxel", mode)

    def set_voxel_line_visible(self, mode, group="template"):
        self.canvas.set_visible(group + "_" + "voxel_line", mode)

    def set_point_cloud(self, points, color = "#00ff00", group = "template"):
        self.canvas.draw_point_cloud(group + "_" + "point_cloud", points, color, self.point_size)

    def set_point_voxel(self, points, w, l, h, face, group="template"):
        self.canvas.draw_point_voxel(group + "_" + "point_voxel", points, w, l, h, face, face)
        self.canvas.draw_voxel_line(group + "_" + "voxel_line", points, w, l, h)

    def set_image(self, img, meta_form):
        self.image_dock[meta_form].set_image(img)

    def set_bbox3d(self, bboxes3d, color, arrow, text_info, show_format, group="template"):
        self.canvas.draw_box3d_line(group + "_" + "bbox3d_line", bboxes3d, color)
        # show arrow
        if len(arrow) !=  0:
            self.canvas.set_visible(group + "_" + "obj_arrow", True)
            self.set_bbox3d_arrow(bboxes3d, arrow, color)
        else:
            self.canvas.set_visible(group + "_" + "obj_arrow", False)

        # show text
        if len(text_info) != 0:
            self.canvas.set_visible(group + "_" + "text", True)
            text_pos = bboxes3d[:, 0:3]
            text_pos[:, -1] += 2.0
            text = []
            for i, txt in enumerate(text_info):
                text.append(show_format[i]%tuple(txt))
            self.set_bbox3d_text(text_pos, text, (0.5, 0.5, 0.5, 1))
        else:
            self.canvas.set_visible(group + "_" + "text", False)

    def set_bbox3d_text(self, pos, txt, color, group="template"):
        self.canvas.draw_text(group + "_" + "text", txt, pos, color)

    def set_bbox3d_arrow(self, bboxes, vel_list, color, group="template"):
        self.canvas.draw_bbox3d_arrow(group + "_" + "obj_arrow", bboxes, vel_list, color)

    def set_reference_line(self, group="template"):
        self.canvas.draw_reference_line(group + "_" + "reference_line")

    def set_canvas_bgcolor(self):
        self.canvas.set_vis_bgcolor(value=self.color_map["-2"])
