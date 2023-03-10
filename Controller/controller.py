
import numpy as np
from Utils.point_cloud_utils import *
from View.view import View
from qt_material import apply_stylesheet
from PySide2.QtWidgets import QApplication
import os.path as osp
from Utils.common_utils import *
from log_sys import *
from PySide2.QtCore import QTimer, Qt
import PySide2
import sys
import qdarkstyle
from qdarkstyle.dark.palette import DarkPalette


dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path


class   Controller():
    def __init__(self) -> None:
        self.app = QApplication([])
        # apply_stylesheet(self.app, theme='dark_teal.xml')
        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside2", palette = DarkPalette))


        self.view = View()


    def run(self):
        self.view.show()
        self.app.exec_()


    def sigint_handler(self, signum = None, frame = None):
        sys.exit(self.app.exec_())
