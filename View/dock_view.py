# import cv2
import sys
import os
import PySide2
from PySide2.QtCore import Signal

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from Utils.common_utils import *
import time
import copy
class ImageViewer(QtWidgets.QWidget):
    doubleClicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border:0px;")
        self.cvimg = None
        self.image = QtGui.QImage()



    def cvimg_to_qtimg(self, cvimg):
        height, width, _ = cvimg.shape
        self.image = QtGui.QImage(cvimg.data, width, height, width * 3, QtGui.QImage.Format_BGR888)
        # self.image = QtGui.QPixmap(cvimg)

    def set_image(self, cvimg):
        self.cvimg = copy.deepcopy(cvimg)
        if isinstance(cvimg, str):
            if os.path.exists(cvimg):
                self.image.load(cvimg)
        else:
            self.cvimg_to_qtimg(self.cvimg)
        self.update()

    def paintEvent(self, event):
        self.painter = QtGui.QPainter(self)
        self.painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        target_rect = QtCore.QRectF(0.0, 0.0, self.width(), self.height())
        source_rect = QtCore.QRectF(0.0, 0.0, self.image.width(), self.image.height())
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
        self.dock_title = dock_title
        self.folder_path = default_path
        # Create the custom title bar widget
        title_bar_widget = QWidget(self)
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
        title_bar_widget.setLayout(title_bar_layout)
        self.setTitleBarWidget(title_bar_widget)
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


class LogDockWidget(QDockWidget):
    def __init__(self, parent=None, titie = "Qlog"):
        super().__init__(titie, parent)
        # self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

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

class RangeSlideDockWidget(QDockWidget):
    frameChanged = Signal(int)
    def __init__(self, parent=None, titie = "frame"):
        super().__init__(titie, parent)
        # self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widget = QWidget()
        layout = QVBoxLayout()
        layout2 = QHBoxLayout()

        self.range_slider = QSlider()
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

        layout2.addWidget(self.last)
        layout2.addWidget(self.auto)

        layout2.addWidget(self.next)
        layout2.addWidget(self.range_slider)
        layout2.addWidget(self.frame)
        layout2.addWidget(self.frame_cnt)
        layout2.addWidget(self.curr_filename)

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
        self.auto_timer.stop()
        self.next_frame()
        self.auto_timer.start(10)

    def auto_ctrl(self, state):
        if state == 0:
            self.auto_timer.stop()
        else:
            self.auto_timer.start(50)

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



# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle("Custom Dock Widget Example")
#         self.setGeometry(100, 100, 800, 600)
#         self.dock_widget = ImageDockWidget(self)
#         self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget )

#         self.show()

#     def set_image(self, image_path):
#         self.dock_widget.set_image(image_path)


