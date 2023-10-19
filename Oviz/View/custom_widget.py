# import cv2
import sys
import os
from Oviz.Utils.common_utils import *
import time


class JSONWidgetEditor(QTextEdit):
    def __init__(self, parent = None, widget_titie="json", default_value = [{}]):
        super().__init__(parent)
        self.widget_title = widget_titie
        self.initUI()
        self.setMaximumHeight(200)
        self.default_value = default_value
        self.set_json_data(default_value[0])

    def initUI(self):
        self.setStyleSheet("font-family: Courier Bold; font: 15px;")  # 使用等宽字体以更好地显示 JSON

    def get_json_data(self):
        json_str = self.toPlainText()
        try:
            self.default_value[0] = eval(json_str)
            return self.default_value[0]
        except Exception as e:
            print("Json input ERROR: [%s]"%e)
            return {"info": "input json parse error [%s]"%e}

    def set_json_data(self, json_data):
        # 将 JSON 数据转换为格式化的文本并设置为文本编辑控件的内容
        formatted_json = json.dumps(json_data, indent=4)
        self.setPlainText(formatted_json)

    def revert(self):
        self.set_json_data(self.default_value[0])



class FolderSelectWidget(QWidget):
    SelectDone = Signal(str, str)
    def __init__(self, parent=None, widget_titie="选择", default_value = {}):
        super().__init__(parent)
        self.widget_title = widget_titie
        self.folder_path = os.path.expanduser(default_value['value'])
        layout = QHBoxLayout()
        self.button = QPushButton(widget_titie)
        self.linetxt = QLineEdit(default_value['value'])

        layout.addWidget(self.button)
        layout.addWidget(self.linetxt)
        self.setLayout(layout)

        self.button.clicked.connect(self.select_folder)
        self.linetxt.returnPressed.connect(self.select_topic_path)
        self.default_value = default_value

    def revert(self):
        self.set_topic_path(self.default_value['value'])

    def reset(self):
        self.default_value['value'] = ""
        self.set_topic_path(self.default_value['value'])

    def select_topic_path(self):
        self.folder_path = os.path.expanduser(self.linetxt.text())
        if not os.path.exists(self.folder_path):
            return
        self.default_value['value'] = self.folder_path
        self.SelectDone.emit(self.folder_path, self.widget_title)

    def set_topic_path(self, txt_path):
        self.linetxt.setText(txt_path)
        if not os.path.exists(txt_path):
            return
        self.select_topic_path()

    def select_folder(self):
        self.folder_path = choose_folder(self.window(), self.widget_title, self.folder_path)
        if not self.folder_path:
            return
        self.linetxt.setText(self.folder_path)
        self.default_value['value'] = self.folder_path
        self.SelectDone.emit(self.folder_path, self.widget_title)

    def get_folder_path(self):
        return self.folder_path


class LineTextWithLabelWidget(QWidget):
    textChanged = Signal(str)
    def __init__(self, parent=None, widget_titie="", default_value = {}):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.label = QLabel(widget_titie)
        self.linetxt = QLineEdit(default_value['value'])
        layout.addWidget(self.label)
        layout.addWidget(self.linetxt)
        self.setLayout(layout)
        self.linetxt.textChanged.connect(self.txtchange)
        self.default_value = default_value


    def txtchange(self, cstr):
        self.textChanged.emit(cstr)
        self.default_value['value'] = cstr

    def text(self):
        return self.linetxt.text()

    def setText(self, cstr):
        self.linetxt.setText(cstr)

    def revert(self):
        self.setText(self.default_value['value'])




class FileSelectWidget(QWidget):
    SelectDone = Signal(str, str)
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


