from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QSplitter, QTreeWidgetItem, QCheckBox
from PySide2.QtCore import QTimer, Qt, QModelIndex
import time
from Utils.common_utils import *
from View.uviz import Canvas
from log_sys import send_log_msg
from .mov_obj import LabelObj
from PySide2.QtCharts import QtCharts


class View():
    '''
        mvc模式中的视图部分，本身不包含任何逻辑，仅作界面显示使用
    '''
    def __init__(self):
        self.ui = QUiLoader().load('Config/main.ui')
        self.canvas_cfg = parse_json("Config/init_canvas_cfg3d.json")
        self.canvas2d_cfg = parse_json("Config/init_canvas_cfg2d.json")


        self.canvas = Canvas()
        self.struct_canvas_init(self.canvas_cfg)

        self.canvas2d = Canvas()
        # self.struct_canvas2d_init(self.canvas2d_cfg)

        self.ui.groupbox_vis3d.layout().addWidget(self.canvas.native)
        self.ui.horizontalLayout_img.addWidget(self.canvas2d.native)
        self.spliter_dict = {}
        self.set_qspilter("main_form",
                            Qt.Horizontal,
                            [self.ui.groupbox_displays,
                                self.ui.groupbox_mainwindow,
                                self.ui.tabwidget_setting],
                            [2, 4, 2],
                            self.ui.centralwidget.layout())
        self.set_qspilter("main_win",
                            Qt.Vertical,
                            [self.ui.groupbox_vis3d,
                                self.ui.tabwidget_main],
                            [4, 2],
                            self.ui.groupbox_mainwindow.layout())
        self.set_qspilter("setting",
                            Qt.Vertical,
                            [self.ui.timeCurveFrame,
                                self.ui.XyCurveFrame,
                                self.ui.control_frame],
                            [5, 5, 1],
                            self.ui.tab_setting_1.layout())
        self.child_tree_item = {}
        self.child2_tree_item = {}
        self.charts_lines = {}
        self.chart_view = {}
        self.axis_x = {}
        self.axis_y = {}
        self.chart = {}
        self.chart_x_min = {}
        self.chart_x_max = {}
        self.chart_y_min = {}
        self.chart_y_max = {}
        self.chart_check_box = {}
        self.ui.tree_widget_for_display.setColumnWidth(0,150)
        self.add_chart_view("TimeCurve", self.ui.timeCurveFrame.layout())
        self.add_chart_view("XYCurve", self.ui.XyCurveFrame.layout())
        self.add_chart_lines("_", "TimeCurve")
        self.add_chart_lines("_", "XYCurve")
        self.frame_index = 0


    def add_chart_view(self, chart_name, layout):
        self.chart[chart_name] = QtCharts.QChart()
        self.chart[chart_name].setTitle(chart_name)
        self.axis_x[chart_name] = QtCharts.QValueAxis()
        # self.axis_x[chart_name].setLabelFormat('%.1f')
        self.axis_x[chart_name].setTitleText('X')
        # self.axis_x[chart_name].setTickCount(11)
        # self.axis_x[chart_name].setMinorTickCount(4)
        self.chart[chart_name].addAxis(self.axis_x[chart_name], Qt.AlignBottom)
        self.axis_y[chart_name] = QtCharts.QValueAxis()
        # self.axis_y[chart_name].setLabelFormat('%.1f')
        self.axis_y[chart_name].setTitleText('Y')
        self.chart[chart_name].addAxis(self.axis_y[chart_name], Qt.AlignLeft)

        self.chart_x_min[chart_name] = 0
        self.chart_x_max[chart_name] = 1
        self.chart_y_min[chart_name] = 0
        self.chart_y_max[chart_name] = 1
        self.set_chart_scale(chart_name)
        self.chart_view[chart_name] = QtCharts.QChartView(self.chart[chart_name], self.ui)
        layout.addWidget(self.chart_view[chart_name])

    def set_chart_scale(self, chart_name):
        self.chart[chart_name].axisX().setRange(self.chart_x_min[chart_name] - 0.5,
                                                    self.chart_x_max[chart_name] + 0.5)
        self.chart[chart_name].axisY().setRange(self.chart_y_min[chart_name] - 0.5,
                                                    self.chart_y_max[chart_name] + 0.5)

    def add_chart_lines(self, line_name, parent_name):
        self.charts_lines[line_name] = QtCharts.QLineSeries()
        self.charts_lines[line_name].setName(line_name)
        self.chart[parent_name].addSeries(self.charts_lines[line_name])
        self.charts_lines[line_name].attachAxis(self.axis_x[parent_name])
        self.charts_lines[line_name].attachAxis(self.axis_y[parent_name])

    def add_chart_checkbox(self, box_name, chart_type):
        self.chart_check_box[box_name] = QCheckBox(box_name)
        self.chart_check_box[box_name].setCheckState(Qt.Checked)
        if chart_type == "XYCurve":
            self.ui.xy_checkbox_area.layout().addWidget(self.chart_check_box[box_name])
        else:
            self.ui.time_checkbox_area.layout().addWidget(self.chart_check_box[box_name])

    def add_value_for_timecurve(self, line_name, value, data_type = "TimeCurve"):
        if self.frame_index < self.chart_x_min[data_type]:
            self.chart_x_min[data_type] = self.frame_index

        if self.frame_index > self.chart_x_max[data_type]:
            self.chart_x_max[data_type] = self.frame_index

        if value < self.chart_y_min[data_type]:
            self.chart_y_min[data_type] = value

        if value > self.chart_y_max[data_type]:
            self.chart_y_max[data_type] = value
        self.set_chart_scale(data_type)
        self.charts_lines[line_name].append(self.frame_index, value)
        self.frame_index += 1


    def add_value_for_xycurve(self, line_name, value, data_type = "XYCurve"):
        if value[0] < self.chart_x_min[data_type]:
            self.chart_x_min[data_type] = value[0]

        if value[0] > self.chart_x_max[data_type]:
            self.chart_x_max[data_type] = value[0]

        if  value[1] < self.chart_y_min[data_type]:
            self.chart_y_min[data_type] =  value[1]

        if  value[1] > self.chart_y_max[data_type]:
            self.chart_y_max[data_type] =  value[1]
        self.set_chart_scale(data_type)
        self.charts_lines[line_name].append(value[0], value[1])


    def struct_canvas_init(self, cfg_dict:dict):
        for key, results in cfg_dict.items():
            self.canvas.create_view(results["type"], key)
            for vis_key, vis_res in results["vis"].items():
                self.canvas.creat_vis(vis_res['type'], vis_key, key)


    def struct_canvas2d_init(self, cfg_dict:dict):
        for key, results in cfg_dict.items():
            self.canvas2d.create_view(results["type"], key)
            for vis_key, vis_res in results["vis"].items():
                self.canvas2d.creat_vis(vis_res['type'], vis_key, key)

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

    def add_topic_type(self, type_list):
        self.ui.combox_topic_type.clear()
        for i in type_list:
            self.ui.combox_topic_type.addItem(i)


    def display_append_msg_list(self, msg):
        self.ui.textedit_log_info.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        for m in msg:
            self.ui.textedit_log_info.append(
                '<span style=\" color: %s;\">%s</span>'%(info_color_list[m[0]],m[1])
                )
        self.ui.textedit_log_info.verticalScrollBar().setValue(
                self.ui.textedit_log_info.verticalScrollBar().maximum()
            )

    def get_sub_topic_text(self):
        return self.ui.need_sub_text.text()

    def get_data_type_text(self):
        return self.ui.combox_topic_type.currentText()

    def add_tree_widget(self, data_dict : dict, data_type, topic):
        if topic in self.child_tree_item.keys():
            send_log_msg(ERROR, "该话题已经订阅过")
        else:
            self.child_tree_item[topic] = QTreeWidgetItem(self.ui.tree_widget_for_display)
            self.child_tree_item[topic].setText(0, topic)
            # self.child_tree_item[topic].setIcon(0,QIcon("../image/cj2.png"))
            self.child_tree_item[topic].setText(1, data_type)
            for key, result in data_dict.items():
                self.child2_tree_item[topic] = QTreeWidgetItem(self.child_tree_item[topic])
                self.child2_tree_item[topic].setText(0, key)
                # self.child2.setIcon(0,QIcon("../image/image_fajiao.png"))
                self.child2_tree_item[topic].setText(1, str(result))
                # self.child2_tree_item[topic].setCheckState(0, Qt.Checked)
                if result in [0, 1]:
                    if result == 0:
                        self.child2_tree_item[topic].setCheckState(0, Qt.Unchecked)
                    else:
                        self.child2_tree_item[topic].setCheckState(0, Qt.Checked)
                elif isinstance(result, int):
                    self.child2_tree_item[topic].setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)
                # 需要默认展开
                # tree_widget_for_display
            self.ui.tree_widget_for_display.expandAll()

    def set_point_cloud(self, points, show, color = "#00ff00", size = 1):
        if show:
            self.canvas.draw_point_cloud("point_cloud", points, color, size)

    def set_bboxes(self, bboxes, show, show_box_surface = 1, show_id = 0, show_vel = 0):
        # 输入的box是列表形式，下面需要转成box对象
        if len(bboxes) == 0:
            self.canvas.update()
            return
        boxes = []
        for b in bboxes:
            boxes.append(LabelObj(b))
        if show:
            self.canvas.draw_box_line("bbox_line", boxes)
            if show_box_surface:
                self.canvas.draw_box_surface("bbox_surface", boxes)
            if show_id:
                self.canvas.draw_id_vel("text", boxes, show_id, show_vel)
        self.canvas.update()

    def set_images(self, img, show, topic):
        if show:
            self.canvas2d.draw_image(topic, img)
            self.canvas2d.update()

    def add_img_view(self, topic):
        self.canvas2d.create_view("add_2dview", topic)
        self.canvas2d.creat_vis("add_image_vis", topic, topic)

    def get_text_cycle_term(self):
        hz = self.ui.text_cycle_term.text()
        return int(hz)

    def set_show_text(self, text):
        self.ui.textBrowser.setText(text)

    def show(self):
        self.ui.show()





if __name__ == "__main__":
    from qt_material import apply_stylesheet

    app = QApplication([])
    apply_stylesheet(app, theme='dark_teal.xml')
    obj = View()
    obj.show()
    app.exec_()



    app = QApplication([])
    apply_stylesheet(app, theme='dark_teal.xml')
    obj = View()
    obj.show()
    app.exec_()

