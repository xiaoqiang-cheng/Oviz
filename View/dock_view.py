# import cv2
import sys
import os
import PySide2
from PySide2.QtCore import Signal

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import *
from Utils.common_utils import *
import time
from PySide2.QtGui import QPixmap



class ImageViewer(QtWidgets.QWidget):
    doubleClicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QtGui.QImage()
        self.label = QLabel("N\A")
        self.scale_factor = 1.0
        # self.setWidget(self.label)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def cvimg_to_qtimg(self, cvimg):
        height, width,_ = cvimg.shape
        qimg = QtGui.QImage(cvimg.data, width, height, QtGui.QImage.Format_BGR888)
        return QtGui.QPixmap(qimg)

    def set_image(self, cvimg):
        # if isinstance(cvimg, str):
        #     if os.path.exists(cvimg):
        #         self.image.load(cvimg)
        # else:
        #     self.image = self.cvimg_to_qtimg(cvimg)
        if isinstance(cvimg, str):
            pixmap = QPixmap(cvimg).scaled(self.label.size(), aspectMode=Qt.KeepAspectRatio)
        else:
            pixmap = self.cvimg_to_qtimg(cvimg).scaled(self.label.size(), aspectMode=Qt.KeepAspectRatio)
        self.label.setPixmap(pixmap)
        self.label.repaint()
        # self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        target_rect = QtCore.QRectF(0.0, 0.0, self.width(), self.height())
        source_rect = QtCore.QRectF(0.0, 0.0, self.image.width(), self.image.height())
        painter.drawImage(target_rect, self.image, source_rect)

    def mouseDoubleClickEvent(self, ev):
        self.doubleClicked.emit()

class ImageDockWidget(QDockWidget):
    SelectDone = Signal(str, str)
    def __init__(self, parent=None, dock_title = "dockview", default_path=""):
        super().__init__(dock_title, parent)
        # self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
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
        self.linetxt.setStyleSheet("background-color: white; border-radius: 5px;")
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
        widget.setLayout(layout)
        self.setWidget(widget)
        self.set_image("./Config/default.png")
        self.setMinimumSize(200, 200)

        self.image_viewer.doubleClicked.connect(self.select_image)
        self.linetxt.returnPressed.connect(self.select_topic_path)


    def select_topic_path(self):
        self.file_path = self.linetxt.text()
        self.SelectDone.emit(self.folder_path, self.dock_title)

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
    def __init__(self, parent=None, titie = "frame"):
        super().__init__(titie, parent)
        # self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widget = QWidget()
        layout = QVBoxLayout()
        layout2 = QHBoxLayout()

        self.range_slider = QSlider()
        self.range_slider.setOrientation(Qt.Horizontal)


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


