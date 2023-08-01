# import cv2
import sys
import os
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QTextEdit, QDockWidget, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QFrame, QLabel, QPushButton
from Utils.common_utils import *
import time

class FolderSelectWidget(QtWidgets.QWidget):
    SelectDone = QtCore.Signal(str, str)
    def __init__(self, parent=None, widget_titie="选择", default_path = ""):
        super().__init__(parent)
        self.widget_title = widget_titie
        self.folder_path = default_path
        layout = QHBoxLayout()
        self.button = QPushButton(widget_titie)
        self.linetxt = QLineEdit()

        layout.addWidget(self.button)
        layout.addWidget(self.linetxt)
        self.setLayout(layout)

        self.button.clicked.connect(self.select_folder)
        self.linetxt.returnPressed.connect(self.select_topic_path)

    def select_topic_path(self):
        self.folder_path = self.linetxt.text()
        if not os.path.exists(self.folder_path):
            return
        self.SelectDone.emit(self.folder_path, self.widget_title)

    def set_topic_path(self, txt_path):
        if not os.path.exists(txt_path):
            return
        self.linetxt.setText(txt_path)
        self.select_topic_path()

    def select_folder(self):
        self.folder_path = choose_folder(self, self.widget_title, self.folder_path)
        if not self.folder_path:
            return
        self.linetxt.setText(self.folder_path)
        self.SelectDone.emit(self.folder_path, self.widget_title)

    def get_folder_path(self):
        return self.folder_path


class LineTextWithLabelWidget(QtWidgets.QWidget):
    textChanged = QtCore.Signal(str)
    def __init__(self, parent=None,  widget_titie="", default_value = ""):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.label = QLabel(widget_titie)
        self.linetxt = QLineEdit(default_value)
        layout.addWidget(self.label)
        layout.addWidget(self.linetxt)
        self.setLayout(layout)

        self.linetxt.textChanged.connect(self.txtchange)

    def txtchange(self, cstr):
        self.textChanged.emit(cstr)

    def text(self):
        return self.linetxt.text()

    def setText(self, cstr):
        self.linetxt.setText(cstr)



class FileSelectWidget(QtWidgets.QWidget):
    SelectDone = QtCore.Signal(str, str)
    def __init__(self, parent=None, widget_titie="选择", default_path = ""):
        super().__init__(parent)
        self.widget_title = widget_titie
        self.file_path = default_path
        layout = QHBoxLayout()
        self.button = QPushButton(widget_titie)
        self.linetxt = QLineEdit()

        layout.addWidget(self.button)
        layout.addWidget(self.linetxt)
        self.setLayout(layout)

        self.button.clicked.connect(self.select_file)
        self.linetxt.returnPressed.connect(self.select_topic_path)

    def select_topic_path(self):
        self.file_path = self.linetxt.text()
        self.SelectDone.emit(self.file_path, self.widget_title)

    def select_file(self):
        self.file_path = choose_file(self, self.widget_title, "file (*.*)", self.file_path)
        if not self.file_path:
            return
        self.linetxt.setText(self.file_path)
        self.SelectDone.emit(self.file_path, self.widget_title)


    def get_file_path(self):
        return self.file_path


