
import numpy as np
from Utils.point_cloud_utils import *
from View.view import View
from Model.model import Model
from Utils.common_utils import *
from log_sys import *
import sys
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette
from Controller.core import *
from importlib import reload


class Controller():
    def __init__(self) -> None:
        self.app = QApplication([])
        self.view = View()
        self.model = Model()
        self.system_online_mode = False

        # vis log timer
        self.Timer = QTimer()
        self.Timer.timeout.connect(self.monitor_timer)
        self.Timer.start(50)

        self.global_setting = GlobalSetting()
        self.record_screen_setting = RecordScreenSetting()

        self.magicpipe_setting = MagicPipeSetting()

        self.point_setting_dict = dict()
        self.bbox3d_setting_dict = dict()

        self.point_setting = PointCloudSetting()
        self.bbox3d_setting = Bbox3DSetting()

        self.signal_connect()

        self.curr_frame_index = 0
        self.curr_frame_key = ""
        self.view.set_spilter_style()

        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside2", palette = DarkPalette))
        self.revert_user_config()
        send_log_msg(NORMAL, "Qviz 系統开始运行！")

    def global_box_signal_connect(self):

        self.view.global_control_box_layout_dict['car_model_setting']['checkbox_show_car'].stateChanged.connect(self.show_car_mode)

        self.view.global_control_box_layout_dict['magic_pipeline_setting']['checkbox_enable_magic'].stateChanged.connect(self.check_magic_pipeline)
        self.view.global_control_box_layout_dict['magic_pipeline_setting']['button_open_magic_pipe_editor'].clicked.connect(self.open_magic_pipeline)
        self.magicpipe_setting.magic_params = self.view.global_control_box_layout_dict['magic_pipeline_setting']['text_magic_pipe_paramters'].get_json_data

        self.view.global_control_box_layout_dict['global_setting']['color_id_map_list'].itemDoubleClicked.connect(self.toggle_list_kind_color)
        self.view.global_control_box_layout_dict['global_setting']['checkbox_show_grid'].stateChanged.connect(self.show_global_grid)
        self.view.global_control_box_layout_dict['global_setting']['show_voxel_mode'].stateChanged.connect(self.update_pointsetting_dims)

        self.view.global_control_box_layout_dict['record_screen_setting']['checkbox_record_screen'].stateChanged.connect(self.change_record_mode)
        self.view.global_control_box_layout_dict['record_screen_setting']['checkbox_mouse_record_screen'].stateChanged.connect(self.change_mouse_record_mode)
        self.view.global_control_box_layout_dict['record_screen_setting']['button_export_record_video'].clicked.connect(self.export_grab_video)

    def sub_element_control_box_connect(self, key_str):
        value = self.view.control_box_layout_dict[key_str]
        for sub_module in value['point_setting']:
            sub_module['button_select_pointcloud'].SelectDone.connect(self.select_pointcloud)
            sub_module['linetxt_point_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_point_type'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_xyz_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_wlh_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_color_dim'].textChanged.connect(self.update_pointsetting_dims)
            # sub_module['show_voxel_mode'].stateChanged.connect(self.update_pointsetting_dims)
        for sub_module in value['bbox3d_setting']:
            sub_module['button_select_bbox3d'].SelectDone.connect(self.select_bbox3d)
            sub_module['bbox3d_txt_xyzwhlt_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_color_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_format_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_text_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_arrow_dim'].textChanged.connect(self.update_bbox3dsetting_dims)

    def element_control_box_connect(self):
        for key in self.view.control_box_layout_dict.keys():
            self.sub_element_control_box_connect(key)

    def add_sub_element_control_box(self, ele_key, index):
        self.element_control_box_connect()

    def signal_connect(self):
        self.view.dock_range_slide.frameChanged.connect(self.update_system_vis)
        for key in self.view.image_dock.keys():
            self.view.image_dock[key].SelectDone.connect(self.select_image)
        self.global_box_signal_connect()
        self.element_control_box_connect()

        self.view.load_history_menu_triggered.connect(self.reload_database)
        self.view.operation_menu_triggered.connect(self.operation_menu_triggered)
        self.view.pointSizeChanged.connect(self.change_point_size)
        self.view.addNewControlTab.connect(self.sub_element_control_box_connect)
        self.view.removeControlTab.connect(self.remove_sub_control_box)
        self.view.addSubControlTab.connect(self.add_sub_element_control_box)
        self.view.removeSubControlTab.connect(self.remove_sub_element_control_box)

    def remove_sub_element_control_box(self, ele_key, index):
        curr_group = self.view.get_curr_control_box_name()
        if index == 0:
            if ele_key == "point_setting":
                self.view.control_box_layout_dict[curr_group][ele_key][0]['button_select_pointcloud'].reset()
            elif ele_key == "bbox3d_setting":
                self.view.control_box_layout_dict[curr_group][ele_key][0]['button_select_bbox3d'].reset()
        else:
            eval("self." + ele_key + "_dict")[curr_group].pop(index)
        # need remove database and update vis
        self.model.remove_sub_element_database(curr_group, ele_key, index)

        self.update_buffer_vis()


    def remove_sub_control_box(self, key):
        self.model.remove_sub_database(key)
        self.update_buffer_vis()

    def revert_user_config(self):
        try:
            self.update_pointsetting_dims()
            self.update_bbox3dsetting_dims()
            self.view.revet_layout_config()
            self.update_system_vis(self.view.layout_config["last_slide_num"])
        except:
            print("ERROR REVERT")
            pass
        send_log_msg(NORMAL, "加载配置结束，如果未能显示上一次数据，请检查文件路径或本地资源是否正常")

    def dump_database(self, target_path):
        serialize_data(self.view.layout_config, target_path)

    def operation_menu_triggered(self, q):
        if q.text() == "保存":
            name, ok = self.view.create_input_dialog("提示", "请输入数据名称")
            if ok:
                self.view.save_last_frame_num(self.curr_frame_index)
                self.dump_database(os.path.join(DUMP_HISTORY_DIR, name))

    def reload_database(self, q):
        target_pkl_path = os.path.join(DUMP_HISTORY_DIR, q.text())
        history_config = deserialize_data(target_pkl_path)
        rec_exsit_merge(self.view.layout_config, history_config)
        self.revert_user_config()

    def show_car_mode(self, state):
        flag = state > 0
        self.view.set_car_visible(flag)

    def check_magic_pipeline(self, state):
        self.magicpipe_setting.enable = state > 0
        self.update_buffer_vis()

    def open_magic_pipeline(self):
        os.system("code %s"%MAGIC_USER_PIPELINE_SCRIPT)

    def show_global_grid(self, state):
        flag = state > 0
        self.view.set_reference_line_visible(flag)

    def change_mouse_record_mode(self, state):
        if state > 0:
            self.record_screen_setting.mouse_record_screen = True
            self.view.mouse_record_screen = True
            if len(self.view.record_screen_image_list) == 0:
                self.view.record_image_start_time = get_wall_time_str()
            send_log_msg(NORMAL, "开始录屏")
        else:
            self.record_screen_setting.mouse_record_screen = False
            self.view.mouse_record_screen = False
            send_log_msg(NORMAL, "关闭录屏")

    def change_record_mode(self, state):
        if state > 0:
            self.record_screen_setting.record_screen = True
            if len(self.view.record_screen_image_list) == 0:
                self.view.record_image_start_time = get_wall_time_str()
            send_log_msg(NORMAL, "开始录屏")
        else:
            self.record_screen_setting.record_screen = False
            send_log_msg(NORMAL, "关闭录屏")

    def export_grab_video(self):
        self.view.export_grab_video()

    # def change_voxel_mode(self, state):
    #     if state > 0:
    #         self.point_setting.show_voxel = True
    #         send_log_msg(NORMAL, "当前是体素模式")
    #     else:
    #         self.point_setting.show_voxel = False
    #         send_log_msg(NORMAL, "当前是点云模式")
    #     self.update_buffer_vis()

    def change_point_size(self, ptsize):
        self.update_buffer_vis()

    def toggle_list_kind_color(self):
        if self.view.set_color_map_list():
            self.update_buffer_vis()

    def select_format(self, group, format, topic_path, meta_form):
        send_log_msg(NORMAL, "亲，你选择了 [%s] topic为: %s"%(format, topic_path))
        if self.system_online_mode:
            pass
        else:
            eval("self.model.deal_%s_folder"%format)(group, topic_path, meta_form)
            self.select_done_update_range_and_vis()

    def select_image(self, topic_path, meta_form):
        group = meta_form
        self.select_format(group, IMAGE, topic_path, meta_form)


    def select_pointcloud(self, topic_path, meta_form):
        self.update_pointsetting_dims()
        curr_group = self.view.get_curr_control_box_name()
        index = self.view.get_curr_sub_element_index(curr_group, "point_setting")
        if index > 0:
            meta_form += str(index)
        self.select_format(curr_group, POINTCLOUD, topic_path, meta_form)


    def select_bbox3d(self, topic_path, meta_form):
        self.update_bbox3dsetting_dims()
        curr_group = self.view.get_curr_control_box_name()
        index = self.view.get_curr_sub_element_index(curr_group, "bbox3d_setting")
        if index > 0:
            meta_form += str(index)
        self.select_format(curr_group, BBOX3D, topic_path, meta_form)

    def select_done_update_range_and_vis(self):
        self.view.set_data_range(self.model.data_frame_list)
        if self.model.offline_frame_cnt:
            self.update_system_vis(0)

    def update_pointsetting_dims(self):
        try:
            curr_tab_key = self.view.get_curr_control_box_name()
            curr_sub_ele_index = self.view.get_curr_sub_element_index(curr_tab_key, "point_setting")
            count = self.view.get_curr_sub_element_count(curr_tab_key, "point_setting")
            if curr_tab_key not in self.point_setting_dict.keys():
                self.point_setting_dict[curr_tab_key] = {}
            for ele_index in range(count):
                self.point_setting_dict[curr_tab_key].update(
                        {ele_index : PointCloudSetting(*self.view.get_pointsetting(index=ele_index))}
                )
            self.point_setting = self.point_setting_dict[curr_tab_key][curr_sub_ele_index]
            if not check_setting_dims(self.point_setting.xyz_dims, [2, 3]): return
            self.update_buffer_vis()
        except:
            print(self.point_setting.__dict__)


    def update_bbox3dsetting_dims(self):
        try:
            curr_tab_key = self.view.get_curr_control_box_name()
            count = self.view.get_curr_sub_element_count(curr_tab_key, "bbox3d_setting")
            curr_sub_ele_index = self.view.get_curr_sub_element_index(curr_tab_key, "bbox3d_setting")
            if curr_tab_key not in self.bbox3d_setting_dict.keys():
                self.bbox3d_setting_dict[curr_tab_key] = {}
            for ele_index in range(count):
                self.bbox3d_setting_dict[curr_tab_key].update(
                    {ele_index:Bbox3DSetting(*self.view.get_bbox3dsetting(index=ele_index))}
                )
            self.bbox3d_setting = self.bbox3d_setting_dict[curr_tab_key][curr_sub_ele_index]
            if not check_setting_dims(self.bbox3d_setting.bbox_dims, 7): return
            self.update_buffer_vis()
        except:
            print(self.bbox3d_setting.__dict__)


    def exec_user_magic_pipeline(self, data_dict, kargs):
        # execute user pipeline
        modules = __import__("user_pipeline", fromlist=[""])
        reload(modules)
        functions = [getattr(modules, func) for func in dir(modules) if callable(getattr(modules, func))]
        for func in functions[::-1]:
            try:
                data_dict = func(self, self.curr_frame_key, data_dict, **kargs)
            except Exception as e:
                print("[Magic pipeline ERROR] ", func, e)
        return data_dict

    def exec_offical_magic_pipeline(self, data_dict, kargs):
        # execute offical pipeline
        modules = __import__("pipeline", fromlist=[""])
        reload(modules)
        functions = [getattr(modules, func) for func in dir(modules) if callable(getattr(modules, func))]
        for func in functions[::-1]:
            try:
                data_dict = func(self, self.curr_frame_key, data_dict, **kargs)
            except Exception as e:
                print("[Magic pipeline ERROR] ", func, e)
        return data_dict

    def exec_magic_pipeline(self, data_dict):
        kargs = self.magicpipe_setting.magic_params()
        # first exec offical
        data_dict = self.exec_offical_magic_pipeline(data_dict, kargs)
        # and then exec user
        data_dict = self.exec_user_magic_pipeline(data_dict, kargs)
        return data_dict

    def update_buffer_vis(self):
        data_dict = self.model.curr_frame_data
        if self.magicpipe_setting.enable:
            data_dict = self.exec_magic_pipeline(data_dict)
        for group, value in data_dict.items():
            curr_frame_data = {}
            self.clear_buffer_vis(group)
            for meta_form, data in value.items():
                topic_type = self.model.topic_path_meta[meta_form]
                fun_name = topic_type + "_callback"
                callback_fun = getattr(self, fun_name, None)
                ret = callback_fun(data, meta_form, meta_form, group)
                if ret is None: continue
                if topic_type not in curr_frame_data.keys():
                    curr_frame_data[topic_type] = {}
                curr_frame_data[topic_type].update({meta_form: ret})

            for topic_type, topic_data in curr_frame_data.items():
                eval("self.update_" + topic_type + "_vis")(topic_data, group)

    def update_system_vis(self, index):
        print(index)
        self.curr_frame_index = index
        self.curr_frame_key = self.model.get_curr_frame_data(index)
        self.update_buffer_vis()
        self.view.send_update_vis_flag()
        if self.record_screen_setting.record_screen:
            self.view.grab_form(self.model.data_frame_list[index], ".png")

    def run(self):
        self.view.show()
        self.app.exec_()
        self.view.save_last_frame_num(self.curr_frame_index)
        self.view.save_layout_config()

    def monitor_timer(self):
        get_msg = ret_log_msg()
        if get_msg != []:
            self.view.dock_log_info.display_append_msg_list(get_msg)

    def sigint_handler(self, signum = None, frame = None):
        self.Timer.stop
        self.view.save_last_frame_num(self.curr_frame_index)
        self.view.save_layout_config()
        sys.exit(self.app.exec_())

    def image_callback(self, msg, topic, meta_form, group):
        self.view.set_image(msg, meta_form)

    def bbox3d_callback(self, msg, topic, meta_form, group):
        try:
            ele_index = int(meta_form[-1])
        except:
            ele_index = 0
        bbox3d_setting = self.bbox3d_setting_dict[group][ele_index]

        max_dim = msg.shape[-1]

        if max_dim == 0:
            return

        msg = msg.reshape(-1, max_dim)
        if max(bbox3d_setting.bbox_dims) >= max_dim:
            send_log_msg(ERROR, "bbox_dims维度无效:%s,最大维度为%d"%(str(bbox3d_setting.bbox_dims), max_dim))
            return

        bboxes = msg[..., bbox3d_setting.bbox_dims]

        if max(bbox3d_setting.arrow_dims) >= max_dim:
            send_log_msg(ERROR, "arrow_dims维度无效:%s,最大维度为%d"%(str(bbox3d_setting.arrow_dims, max_dim)))
            return

        if max(bbox3d_setting.arrow_dims) == -1:
            arrow = []
        else:
            arrow = msg[..., bbox3d_setting.arrow_dims]

        if max(bbox3d_setting.text_dims) >= max_dim:
            send_log_msg(ERROR, "text_dims维度无效:%s,最大维度为%d"%(str(bbox3d_setting.text_dims), max_dim))
            return

        if max(bbox3d_setting.text_dims) == -1:
            text_info = []
        else:
            text_info = msg[..., bbox3d_setting.text_dims]


        if len(bbox3d_setting.color_dims) <= 0 or min(bbox3d_setting.color_dims) < 0 or max(bbox3d_setting.color_dims) >= max_dim:
            # send_log_msg(ERROR, "color维度无效:%s,最大维度为%d"%(str(self.bbox3d_setting.color_dims), max_dim))
            color_id_list = -1
        else:
            color_id_list = msg[..., bbox3d_setting.color_dims]

        real_color, state = self.view.color_id_to_color_list(color_id_list)

        # if not state:
        #     send_log_msg(ERROR, "获取颜色维度失败，使用默认颜色")

        # self.view.set_bbox3d_visible(True, group=group)
        # self.view.set_bbox3d(bboxes, real_color, arrow, text_info, bbox3d_setting.text_format, group=group)
        return bboxes, real_color, arrow, text_info, bbox3d_setting.text_format, group

    def pointcloud_callback(self, msg, topic, meta_form, group):
        try:
            ele_index = int(meta_form[-1])
        except:
            ele_index = 0
        point_setting = self.point_setting_dict[group][ele_index]

        if len(msg.shape) == 1:
            try:
                msg = np.frombuffer(msg.data, dtype = np.dtype(point_setting.points_type)).reshape(-1, point_setting.points_dim)
            except:
                return
        max_dim = msg.shape[-1]
        if max(point_setting.xyz_dims) >= max_dim:
            send_log_msg(ERROR, "xyz维度无效:%s,最大维度为%d"%(str(point_setting.xyz_dims), max_dim))
            return
        points = msg[...,point_setting.xyz_dims]

        if len(point_setting.color_dims) <= 0 or min(point_setting.color_dims) < 0 or max(point_setting.color_dims) >= max_dim:
            # send_log_msg(ERROR, "color维度无效:%s,最大维度为%d"%(str(self.point_setting.color_dims), max_dim))
            color_id_list = -1
        else:
            color_id_list = msg[..., point_setting.color_dims]

        real_color, state = self.view.color_id_to_color_list(color_id_list)

        # if not state:
        #     send_log_msg(ERROR, "获取颜色维度失败，使用默认颜色")
        w, l, h = np.array([]), np.array([]), np.array([])
        if point_setting.show_voxel:
            if len(point_setting.color_dims) <= 0 or min(point_setting.wlh_dims) < 0 or max(point_setting.wlh_dims) > max_dim:
                w = np.ones((len(points), 1)) * 0.4
                l = np.ones((len(points), 1)) * 0.4
                h = np.ones((len(points), 1)) * 0.4
            else:
                w = msg[..., point_setting.wlh_dims[0]]
                l = msg[..., point_setting.wlh_dims[1]]
                h = msg[..., point_setting.wlh_dims[2]]
        if isinstance(real_color, str):
            real_color = np.array([self.view.color_str_to_rgb(real_color)] * len(points))
            # self.view.set_point_voxel(points, w, l, h, real_color, group)
        # else:
            # self.view.set_point_cloud(points, color = real_color, size=self.view.point_size, group=group)
        return points, real_color, self.view.point_size, w, l, h, point_setting.show_voxel, group

    def clear_buffer_vis(self, group):
        self.view.set_bbox3d_visible(False, group)
        self.view.set_point_cloud_visible(False, group)
        self.view.set_point_voxel_visible(False, group)
        self.view.set_voxel_line_visible(False, group)

    def update_pointcloud_vis(self, data, group):
        points = []
        real_color = []
        point_size = 1
        w = []
        l = []
        h = []
        show_voxel = False
        for sub_data in data.values():
            points.append(sub_data[0])
            real_color.append(sub_data[1])
            point_size = sub_data[2]
            w.append(sub_data[3])
            l.append(sub_data[4])
            h.append(sub_data[5])
            show_voxel |= sub_data[6]

        points = np.concatenate(points)

        if len(data.keys()) > 1:
            tmp_color = []
            for i, curr_color in enumerate(real_color):
                color_mask = np.array([i] * len(curr_color)).reshape(-1, 1)
                tmp_color.append(self.view.color_id_to_color_list(color_mask)[0])
            real_color = np.concatenate(tmp_color)

        else:
            real_color = np.concatenate(real_color)

        try:
            w = np.concatenate(w)
            l = np.concatenate(l)
            h = np.concatenate(h)
        except:
            pass

        if show_voxel:
            self.view.set_point_voxel(points, w, l, h, real_color, group)
        else:
            self.view.set_point_cloud(points, color = real_color, size=self.view.point_size, group=group)
        self.view.set_voxel_mode(show_voxel, group)


    def update_bbox3d_vis(self, data, group):
        bboxes = []
        real_color = []
        arrow = []
        text_info = []
        text_format = []
        for sub_data in data.values():
            bboxes.append(sub_data[0])
            real_color.append(sub_data[1])
            arrow.append(sub_data[2])
            text_info.append(sub_data[3])
            text_format += sub_data[4] * len(sub_data[3])
        bboxes = np.concatenate(bboxes)
        if len(data.keys()) > 1:
            tmp_color = []
            for i, curr_color in enumerate(real_color):
                color_mask = np.array([i] * len(curr_color)).reshape(-1, 1)
                tmp_color.append(self.view.color_id_to_color_list(color_mask)[0])
            real_color = np.concatenate(tmp_color)

        else:
            real_color = np.concatenate(real_color)
        arrow = np.concatenate(arrow)
        text_info = np.concatenate(text_info)
        self.view.set_bbox3d_visible(True)
        self.view.set_bbox3d(bboxes, real_color, arrow, text_info, text_format, group)
        self.view.set_bbox3d_visible(True, group)
