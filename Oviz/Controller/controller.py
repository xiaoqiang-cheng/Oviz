
import numpy as np
from Oviz.Utils.point_cloud_utils import *
from Oviz.View.view import View
from Oviz.Model.model import Model
from Oviz.Utils.common_utils import *
from Oviz.log_sys import *
import sys
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette
from Oviz.Controller.core import *
from importlib import reload


class Controller():
    def __init__(self) -> None:
        self.app = QApplication([])
        self.view = View()
        self.model = Model()

        # vis log timer
        self.Timer = QTimer()
        self.Timer.timeout.connect(self.monitor_timer)
        self.Timer.start(50)

        self.global_setting = GlobalSetting()
        self.record_screen_setting = RecordScreenSetting()

        self.magicpipe_setting = MagicPipeSetting()

        self.pointcloud_setting_dict = dict()
        self.bbox3d_setting_dict = dict()

        self.pointcloud_setting = PointCloudSetting()
        self.bbox3d_setting = Bbox3DSetting()

        self.signal_connect()

        self.curr_frame_index = 0
        self.curr_frame_key = ""

        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside2", palette = DarkPalette))
        self.revert_user_config()
        send_log_msg(NORMAL, "Oviz 系統开始运行！")

    def global_box_signal_connect(self):
        self.view.dock_global_control_box_layout_dict['car_model_setting']['checkbox_show_car'].stateChanged.connect(self.show_car_mode)
        self.view.dock_global_control_box_layout_dict['magic_pipeline_setting']['checkbox_enable_magic'].stateChanged.connect(self.check_magic_pipeline)
        self.view.dock_global_control_box_layout_dict['magic_pipeline_setting']['button_open_magic_pipe_editor'].clicked.connect(self.open_magic_pipeline)
        self.magicpipe_setting.magic_params = self.view.dock_global_control_box_layout_dict['magic_pipeline_setting']['text_magic_pipe_paramters'].get_json_data

        self.view.dock_global_control_box_layout_dict['global_setting']['color_id_map_list'].itemDoubleClicked.connect(self.toggle_list_kind_color)
        self.view.dock_global_control_box_layout_dict['global_setting']['checkbox_show_grid'].stateChanged.connect(self.show_global_grid)

        self.view.dock_global_control_box_layout_dict['remote_api_setting']['enable_remote_link'].clicked.connect(self.enable_remote_api)
        self.view.dock_global_control_box_layout_dict['remote_api_setting']['button_remote_key'].clicked.connect(self.model.online_set_control)


        self.view.dock_global_control_box_layout_dict['record_screen_setting']['checkbox_record_screen'].stateChanged.connect(self.change_record_mode)
        self.view.dock_global_control_box_layout_dict['record_screen_setting']['checkbox_mouse_record_screen'].stateChanged.connect(self.change_mouse_record_mode)
        self.view.dock_global_control_box_layout_dict['record_screen_setting']['button_export_record_video'].clicked.connect(self.export_grab_video)


    def sub_element_control_box_connect(self, key_str):
        value = self.view.dock_element_control_box_layout_dict[key_str]
        for sub_module in value['pointcloud']:
            sub_module['folder_path'].SelectDone.connect(self.select_pointcloud)
            sub_module['linetxt_point_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_point_type'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_xyz_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_wlh_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['linetxt_color_dim'].textChanged.connect(self.update_pointsetting_dims)
            sub_module['show_voxel_mode'].stateChanged.connect(self.update_pointsetting_dims)

        for sub_module in value['bbox3d']:
            sub_module['folder_path'].SelectDone.connect(self.select_bbox3d)
            sub_module['bbox3d_txt_xyzwhlt_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_color_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_format_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_text_dim'].textChanged.connect(self.update_bbox3dsetting_dims)
            sub_module['bbox3d_txt_arrow_dim'].textChanged.connect(self.update_bbox3dsetting_dims)

    def element_control_box_connect(self):
        for key in self.view.dock_element_control_box_layout_dict.keys():
            self.sub_element_control_box_connect(key)

    def add_sub_element_control_box(self, ele_key, index):
        self.element_control_box_connect()

    def dynamic_add_image_dock(self, index):
        self.view.image_dock[index].SelectDone.connect(self.select_image)

    def signal_connect(self):
        self.model.hasNewMsg.connect(self.update_buffer_vis)
        self.view.dock_range_slide.frameChanged.connect(self.update_system_vis)
        for val in self.view.image_dock:
            val.SelectDone.connect(self.select_image)

        self.global_box_signal_connect()
        self.element_control_box_connect()
        self.view.addImageDock.connect(self.dynamic_add_image_dock)
        self.view.pointSizeChanged.connect(self.change_point_size)
        self.view.addNewControlTab.connect(self.sub_element_control_box_connect)
        self.view.removeControlTab.connect(self.remove_sub_control_box)
        self.view.addSubControlTab.connect(self.add_sub_element_control_box)
        self.view.removeSubControlTab.connect(self.remove_sub_element_control_box)
        self.view.removeImageDock.connect(self.remove_image_dock)

    def enable_remote_api(self, state):
        if state > 0:
            port = self.view.get_remote_api_setting()
            self.model.update_middleware(port)
        else:
            self.model.update_middleware()

    def remove_image_dock(self, index):
        try:
            self.model.database['template'][IMAGE].pop(index)
            self.model.curr_frame_data['template'][IMAGE].pop(index)
        except:
            pass

    def remove_sub_element_control_box(self, ele_key, index):
        curr_group = self.view.get_curr_control_box_name()
        if index == 0:
            self.view.dock_element_control_box_layout_dict[curr_group][ele_key][0]['folder_path'].reset()
        else:
            eval("self." + ele_key + "_setting_dict")[curr_group].pop(index)
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

    def change_point_size(self, ptsize):
        self.update_buffer_vis()

    def toggle_list_kind_color(self):
        if self.view.set_color_map_list():
            self.update_buffer_vis()

    def select_format(self, group, topic_type, topic_path, ele_index):
        send_log_msg(NORMAL, "亲，你选择了 [%s] topic为: %s"%(topic_type, topic_path))
        eval("self.model.deal_%s_folder"%topic_type)(group, topic_path, ele_index)
        self.select_done_update_range_and_vis()

    def select_image(self, topic_path, meta_form):
        self.select_format("template", IMAGE, topic_path, int(meta_form))


    def select_pointcloud(self, topic_path, topic_type):
        self.update_pointsetting_dims()
        curr_group = self.view.get_curr_control_box_name()
        ele_index = self.view.get_curr_sub_element_index(curr_group, topic_type)
        self.select_format(curr_group, topic_type, topic_path, ele_index)


    def select_bbox3d(self, topic_path, topic_type):
        self.update_bbox3dsetting_dims()
        curr_group = self.view.get_curr_control_box_name()
        ele_index = self.view.get_curr_sub_element_index(curr_group, topic_type)
        self.select_format(curr_group, topic_type, topic_path, ele_index)

    def select_done_update_range_and_vis(self):
        self.view.set_data_range(self.model.data_frame_list)
        if self.model.offline_frame_cnt:
            self.update_system_vis(self.curr_frame_index)

    def update_pointsetting_dims(self):
        try:
            curr_tab_key = self.view.get_curr_control_box_name()
            curr_sub_ele_index = self.view.get_curr_sub_element_index(curr_tab_key, POINTCLOUD)
            count = self.view.get_curr_sub_element_count(curr_tab_key, POINTCLOUD)
            if curr_tab_key not in self.pointcloud_setting_dict.keys():
                self.pointcloud_setting_dict[curr_tab_key] = {}
            for ele_index in range(count):
                self.pointcloud_setting_dict[curr_tab_key].update(
                        {ele_index : PointCloudSetting(*self.view.get_pointsetting(index=ele_index))}
                )
            self.pointcloud_setting = self.pointcloud_setting_dict[curr_tab_key][curr_sub_ele_index]

            if not check_setting_dims(self.pointcloud_setting.xyz_dims, [2, 3]): return
            self.update_buffer_vis()
        except:
            print(self.pointcloud_setting.__dict__)


    def update_bbox3dsetting_dims(self):
        try:
            curr_tab_key = self.view.get_curr_control_box_name()
            count = self.view.get_curr_sub_element_count(curr_tab_key, BBOX3D)
            curr_sub_ele_index = self.view.get_curr_sub_element_index(curr_tab_key, BBOX3D)
            if curr_tab_key not in self.bbox3d_setting_dict.keys():
                self.bbox3d_setting_dict[curr_tab_key] = {}
            for ele_index in range(count):
                self.bbox3d_setting_dict[curr_tab_key].update(
                    {ele_index: Bbox3DSetting(*self.view.get_bbox3dsetting(index=ele_index))}
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
        modules = __import__("Oviz.MagicPipe.pipeline", fromlist=[""])
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

    def update_buffer_vis(self, timestamp = None):

        data_dict = self.model.curr_frame_data
        if timestamp:
            print("msg delay [%.2f] ms"%((time.time() - timestamp) * 1000))

        if self.magicpipe_setting.enable:
            data_dict = self.exec_magic_pipeline(data_dict)
        for group, value in data_dict.items():
            collect_frame_data = {}
            self.clear_buffer_vis(group)
            for topic_type, data_list in value.items():
                for ele_index, data in enumerate(data_list):
                    fun_name = topic_type + "_callback"
                    callback_fun = getattr(self, fun_name, None)
                    ret = callback_fun(data, topic_type, ele_index, group)
                    if ret is None: continue
                    if topic_type not in collect_frame_data.keys():
                        collect_frame_data[topic_type] = {}
                    collect_frame_data[topic_type].update({ele_index: ret})

            for topic_type, topic_data in collect_frame_data.items():
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
        print("Close Windows 退出程序")
        self.model.free()
        print("进程完全退出！")
        sys.exit(0)


    def monitor_timer(self):
        get_msg = ret_log_msg()
        if get_msg != []:
            self.view.dock_log_info.display_append_msg_list(get_msg)

    def sigint_handler(self, signum = None, frame = None):
        print("Ctrl + C 退出程序")
        self.Timer.stop()
        self.model.free()
        sys.exit(0)
        # sys.exit(self.app.exec_())



    def image_callback(self, msg, topic_type, ele_index, group):
        self.view.set_image(msg, ele_index)

    def bbox3d_callback(self, msg, topic, ele_index, group):

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
            text_info = np.array([]).reshape(-1, len(bbox3d_setting.text_dims))
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

    def pointcloud_callback(self, msg, topic, ele_index, group):
        pointcloud_setting = self.pointcloud_setting_dict[group][ele_index]

        if len(msg.shape) == 1:
            try:
                surplus = msg.shape[-1] % pointcloud_setting.points_dim
                if surplus == 0:
                    msg = np.frombuffer(msg.data, dtype = np.dtype(pointcloud_setting.points_type)).reshape(-1, pointcloud_setting.points_dim)
                else:
                    msg = np.frombuffer(msg.data, dtype = np.dtype(pointcloud_setting.points_type))[:-surplus].reshape(-1, pointcloud_setting.points_dim)
                    send_log_msg(ERROR, "your point dim [%d] is error, please check it"%pointcloud_setting.points_dim)
            except:
                return
        max_dim = msg.shape[-1]
        if max(pointcloud_setting.xyz_dims) >= max_dim:
            send_log_msg(ERROR, "xyz维度无效:%s,最大维度为%d"%(str(pointcloud_setting.xyz_dims), max_dim))
            return
        points = msg[...,pointcloud_setting.xyz_dims]

        if len(pointcloud_setting.color_dims) <= 0 or min(pointcloud_setting.color_dims) < 0 or max(pointcloud_setting.color_dims) >= max_dim:
            # send_log_msg(ERROR, "color维度无效:%s,最大维度为%d"%(str(self.pointcloud_setting.color_dims), max_dim))
            color_id_list = -1
        else:
            color_id_list = msg[..., pointcloud_setting.color_dims]

        real_color, state = self.view.color_id_to_color_list(color_id_list)

        # if not state:
        #     send_log_msg(ERROR, "获取颜色维度失败，使用默认颜色")
        w, l, h = np.array([]), np.array([]), np.array([])
        if pointcloud_setting.show_voxel:
            if len(pointcloud_setting.color_dims) <= 0 or min(pointcloud_setting.wlh_dims) < 0 or max(pointcloud_setting.wlh_dims) > max_dim:
                w = np.ones((len(points), 1)) * 0.4
                l = np.ones((len(points), 1)) * 0.4
                h = np.ones((len(points), 1)) * 0.4
            else:
                w = msg[..., pointcloud_setting.wlh_dims[0]]
                l = msg[..., pointcloud_setting.wlh_dims[1]]
                h = msg[..., pointcloud_setting.wlh_dims[2]]
        if isinstance(real_color, str):
            real_color = np.array([color_str_to_rgb(real_color)] * len(points))
        return points, real_color, w, l, h, pointcloud_setting.show_voxel, group

    def clear_buffer_vis(self, group):
        self.view.set_bbox3d_visible(False, group)
        self.view.set_point_cloud_visible(False, group)
        self.view.set_point_voxel_visible(False, group)
        self.view.set_voxel_line_visible(False, group)

    def update_pointcloud_vis(self, data, group):
        points = []
        real_color = []
        w = []
        l = []
        h = []
        show_voxel = False
        for sub_data in data.values():
            points.append(sub_data[0])
            real_color.append(sub_data[1])
            w.append(sub_data[2])
            l.append(sub_data[3])
            h.append(sub_data[4])
            show_voxel |= sub_data[5]

        points = np.concatenate(points)

        if len(data) > 1:
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
            self.view.set_point_cloud(points, color = real_color, group=group)
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
            text_info += sub_data[3].tolist()
            text_format += [sub_data[4]] * len(sub_data[3])
        bboxes = np.concatenate(bboxes)

        if len(data) > 1:
            tmp_color = []
            for i, curr_color in enumerate(real_color):
                color_mask = np.array([i] * len(curr_color)).reshape(-1, 1)
                tmp_color.append(self.view.color_id_to_color_list(color_mask)[0])
            real_color = np.concatenate(tmp_color)

        else:
            real_color = np.concatenate(real_color)
        arrow = np.concatenate(arrow)

        self.view.set_bbox3d_visible(True)
        self.view.set_bbox3d(bboxes, real_color, arrow, text_info, text_format, group)
        self.view.set_bbox3d_visible(True, group)
