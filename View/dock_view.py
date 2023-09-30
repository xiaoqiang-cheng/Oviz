# import cv2
import sys
import os
from Utils.common_utils import *
import time
import copy
class ImageViewer(QWidget):
    doubleClicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border:0px;")
        self.cvimg = None
        self.image = QImage()



    def cvimg_to_qtimg(self, cvimg):
        height, width, _ = cvimg.shape
        self.image = QImage(cvimg.data, width, height, width * 3, QImage.Format_BGR888)
        # self.image = QPixmap(cvimg)

    def set_image(self, cvimg):
        self.cvimg = copy.deepcopy(cvimg)
        if isinstance(cvimg, str):
            if os.path.exists(cvimg):
                self.image.load(cvimg)
        else:
            self.cvimg_to_qtimg(self.cvimg)
        self.update()

    def paintEvent(self, event):
        self.painter = QPainter(self)
        self.painter.setRenderHint(QPainter.SmoothPixmapTransform)
        target_rect = QRectF(0.0, 0.0, self.width(), self.height())
        source_rect = QRectF(0.0, 0.0, self.image.width(), self.image.height())
        self.painter.drawImage(target_rect, self.image, source_rect)
        self.painter.end()

    def mouseDoubleClickEvent(self, ev):
        self.doubleClicked.emit()


class ImageDockWidget(QDockWidget):
    SelectDone = Signal(str, str)
    def __init__(self, parent=None, dock_title = "dockview", default_path=""):
        super().__init__(dock_title, parent)
        # self.setStyleSheet("QDockWidget::separator{ width: 0px; height: 0px; }")
        # self.setStyleSheet("QDockWidget:separator {width: 1px; height: 1px; }")
        self.setObjectName(dock_title)
        self.dock_title = dock_title
        self.folder_path = default_path
        # Create the custom title bar widget
        self.title_bar_widget = QWidget(self)
        self.show_title = True
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Add the title label to the title bar
        title_label = QLabel(dock_title)
        title_bar_layout.addWidget(title_label)

        # Add the line edit to the title bar
        self.linetxt = QLineEdit()
        self.linetxt.setMaximumWidth(100)
        self.linetxt.setMinimumHeight(20)
        self.linetxt.setFrame(False)
        self.linetxt.setPlaceholderText("Enter text")
        self.linetxt.setStyleSheet("border-radius: 5;")
        title_bar_layout.addWidget(self.linetxt)

        # Add a separator line between the title bar and the content area
        separator_line = QFrame(self)
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        separator_line.setStyleSheet("background-color: rgb(224, 224, 224);")
        title_bar_layout.addWidget(separator_line)

        # Set the custom title bar widget as the title bar for the dock widget
        self.title_bar_widget.setLayout(title_bar_layout)
        self.set_image_title_bar()

        self.image_viewer = ImageViewer(self)
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.image_viewer)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        self.setWidget(widget)
        self.setContentsMargins(0, 0, 0, 0)
        self.set_image("Config/default.png")
        self.setMinimumSize(100, 100)
        self.image_viewer.doubleClicked.connect(self.select_image)
        self.linetxt.returnPressed.connect(self.select_topic_path)


    def set_image_title_bar(self):
        if self.show_title:
            self.setTitleBarWidget(self.title_bar_widget)
        else:
            self.setTitleBarWidget(QWidget())
        self.show_title = not self.show_title

    def select_topic_path(self):
        self.folder_path = self.linetxt.text()
        self.SelectDone.emit(self.folder_path, self.dock_title)

    def set_topic_path(self, txt_path):
        if not os.path.exists(txt_path):
            return
        self.linetxt.setText(txt_path)
        self.select_topic_path()

    def select_image(self):
        self.folder_path = choose_folder(self, self.dock_title, self.folder_path)
        if not self.folder_path:
            return
        self.linetxt.setText(self.folder_path)
        self.SelectDone.emit(self.folder_path, self.dock_title)

    def set_image(self, image_path):
        self.image_viewer.set_image(image_path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 强制进行重新绘制
        self.update()

class LogDockWidget(QDockWidget):
    def __init__(self, parent=None, titie = "Qlog"):
        super().__init__(titie, parent)
        # self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setObjectName(titie)

        widget = QWidget()
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)
        widget.setLayout(layout)
        self.setWidget(widget)

    def display_append_msg_list(self, msg):
        self.text_edit.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        for m in msg:
            self.text_edit.append(
                '<span style=\" color: %s;\">%s</span>'%(info_color_list[m[0]],m[1])
                )
        self.text_edit.verticalScrollBar().setValue(
                self.text_edit.verticalScrollBar().maximum()
            )
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 强制进行重新绘制
        self.update()

class RangeSlideDockWidget(QDockWidget):
    frameChanged = Signal(int)
    def __init__(self, parent=None, titie = "frame"):
        super().__init__(titie, parent)
        # self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setObjectName(titie)
        self.setWindowFlags(Qt.FramelessWindowHint)

        widget = QWidget()
        layout = QVBoxLayout()
        layout2 = QHBoxLayout()

        self.range_slider = QSlider()
        # self.range_slider.setTracking(False)
        self.range_slider.setOrientation(Qt.Horizontal)

        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.auto_play)
        self.update_handled = True

        self.last = QPushButton("<")
        self.auto = QCheckBox("auto")
        self.next = QPushButton(">")
        self.frame = QLineEdit()
        self.frame.setMaximumWidth(50)

        self.frame_cnt = QLabel("\\N")
        self.curr_filename = QLabel("filename")
        self.curr_filename.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.fps = QLineEdit("20")
        self.fps.setMaximumWidth(50)

        self.fps_label = QLabel("HZ")

        layout2.addWidget(self.last)
        layout2.addWidget(self.auto)

        layout2.addWidget(self.next)
        layout2.addWidget(self.range_slider)
        layout2.addWidget(self.frame)
        layout2.addWidget(self.frame_cnt)
        layout2.addWidget(self.curr_filename)
        layout2.addWidget(self.fps)
        layout2.addWidget(self.fps_label)

        widget.setLayout(layout2)
        self.setWidget(widget)

        self.curr_index = 0
        self.frame_range = 100
        self.listname = list(range(100))
        self.set_range(self.listname)

        self.last.clicked.connect(self.last_frame)
        self.next.clicked.connect(self.next_frame)

        self.frame.textChanged.connect(self.set_bar)
        self.range_slider.valueChanged.connect(self.change_bar)
        self.auto.stateChanged.connect(self.auto_ctrl)

    def auto_play(self):
        # if self.update_handled:
        # self.auto_timer.stop()
        self.next_frame()

        # self.auto_timer.start(100)

    def auto_ctrl(self, state):
        hz = int(self.fps.text())
        if state == 0:
            self.auto_timer.stop()
        else:
            self.auto_timer.start(int(1000.0 / hz))

    def change_bar(self):
        self.curr_index = self.range_slider.value()
        self.set_frmae_text(self.curr_index)

    def set_filename(self, name):
        self.curr_filename.setText(str(name))

    def set_frame_cnt(self, cnt):
        self.frame_cnt.setText("/" + str(cnt))

    def set_bar(self):
        try:
            self.curr_index = int(self.frame.text())
            if self.curr_index < 0:
                self.curr_index = 0
                self.set_frmae_text(self.curr_index)
            elif self.curr_index >= self.frame_range:
                self.curr_index = self.frame_range - 1
                self.set_frmae_text(self.curr_index)
            # 如果频繁的按下 next 或者 拖动，可视化会很卡，然后会停不下来
            # 可视化和这些东西还是放入异步线程比较好
            if self.update_handled:
                self.update_handled = False
                self.frameChanged.emit(self.curr_index)
        except:
            print("输入不合法")
        self.range_slider.setValue(self.curr_index)
        self.set_filename(self.listname[self.curr_index])

    def set_frmae_text(self, index):
        self.frame.setText(str(index))

    def next_frame(self):
        self.curr_index += 1
        if self.curr_index >= self.frame_range:
            self.curr_index = 0
        self.set_frmae_text(self.curr_index)

    def last_frame(self):
        self.curr_index -= 1
        if self.curr_index < 0:
            self.curr_index = self.frame_range - 1
        self.set_frmae_text(self.curr_index)

    def get_curr_index(self):
        return self.curr_index

    def set_range(self, list_name):
        self.listname = list_name
        self.frame_range = len(self.listname)
        self.range_slider.setRange(0, self.frame_range - 1)
        self.set_frame_cnt(self.frame_range - 1)
        self.set_frmae_text(0)

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     # 强制进行重新绘制
    #     self.update()


class CollapsibleBox(QWidget):
    # addNewModule = Signal(str)
    # removeCurrentModule = Signal(str)
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        # self.menu = QMenu()
        # self.menu.addAction("增加此模组")
        # self.menu.addAction("删除此模组")
        # self.menu.triggered.connect(self.operation_menu_triggered)

        self.title = title
        self.toggle_button = QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)
        self.toggle_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.toggle_button.customContextMenuRequested.connect(self.right_clicked)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = QWidget(
            maximumHeight=0,
            minimumHeight=0
        )

        # self.content_area = QTabWidget(
        #     maximumHeight=0,
        #     minimumHeight=0
        # )

        # self.content_area.setSizePolicy(
        #     QSizePolicy.Expanding, QSizePolicy.Fixed
        # )

        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    # def operation_menu_triggered(self, q):
    #     if q.text() == "增加此模组":
    #         self.addNewModule.emit(self.title)
    #     elif q.text() == "删除此模组":
    #         self.removeCurrentModule.emit(self.title)

    def right_clicked(self,  pos):
        self.menu.exec_(self.toggle_button.mapToGlobal(pos))

    def unfold(self):
        self.on_pressed()
        self.toggle_button.setChecked(not self.toggle_button.isChecked())
        # self.toggle_animation.start()

    @Slot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            Qt.DownArrow if not checked else Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QAbstractAnimation.Forward
            if not checked
            else QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(200)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(200)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class ControlTabBoxDockWidget(QDockWidget):
    def __init__(self, parent=None, title="控制台", layout_dict=dict()):
        super().__init__(title, parent)
        self.setObjectName(title)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 设置为可调整大小
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 仅当需要时显示垂直滚动条

        # widget = QWidget()
        self.tabwidget = QTabWidget()
        scroll_area.setWidget(self.tabwidget)
        self.boxes = {}
        self.boxes_layout = {}
        self.layout_dict = layout_dict
        for ckey, cvalue in layout_dict.items():
            self.add_tab_widget(ckey, cvalue)
        self.setWidget(scroll_area)  # 将QScrollArea作为QDockWidget的widget

    def add_tab_widget(self, ckey, cvalue):
        subwidget = QWidget()
        self.boxes_layout[ckey] = QVBoxLayout(subwidget)
        self.boxes[ckey] = {}
        for key, val in cvalue.items():
            self.add_single_cbox(ckey, key, val)
        self.boxes_layout[ckey].addStretch()
        self.tabwidget.addTab(subwidget, ckey)

    def add_single_cbox(self, tabkey, box_key, box_content):
        box = CollapsibleBox(box_key)
        self.boxes[tabkey][box_key] = box
        self.boxes_layout[tabkey].addWidget(box)
        box.setContentLayout(box_content['layout'])

    def get_curr_control_box_name(self):
        curr_index = self.tabwidget.currentIndex()
        return self.tabwidget.tabText(curr_index)

    def add_box(self, box_name):
        self.addControlBox.emit(box_name)

    def remove_box(self, box_name):
        self.addControlBox.emit(box_name)

    def remove_tab_widget(self, index):
        self.tabwidget.removeTab(index)

    def unfold(self):
        for key, val in self.boxes.items():
            for subkey, subval in val.items():
                subval.unfold()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 强制进行重新绘制
        self.update()


class ControlBoxDockWidget(QDockWidget):
    def __init__(self, parent=None, title="控制台", layout_dict=dict()):
        super().__init__(title, parent)
        self.setObjectName(title)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 设置为可调整大小
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 仅当需要时显示垂直滚动条

        widget = QWidget()
        scroll_area.setWidget(widget)

        vlay = QVBoxLayout(widget)  # 在widget上使用垂直布局
        self.boxes = {}
        for key, val in layout_dict.items():
            box = CollapsibleBox(key)
            self.boxes[key] = box
            vlay.addWidget(box)
            box.setContentLayout(val['layout'])
        vlay.addStretch()
        self.setWidget(scroll_area)  # 将QScrollArea作为QDockWidget的widget

    def unfold(self):
        for key, val in self.boxes.items():
            val.unfold()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 强制进行重新绘制
        self.update()
