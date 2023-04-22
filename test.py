import sys
import PySide2
import os
from PySide2.QtWidgets import QApplication, QMainWindow, QDockWidget, QTextEdit, QSplitter
from PySide2.QtCore import QTimer, Qt, QModelIndex

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建两个 QDockWidget
        dock1 = QDockWidget("Dock 1", self)
        dock1.setWidget(QTextEdit(self))
        self.addDockWidget(Qt.LeftDockWidgetArea, dock1)

        dock2 = QDockWidget("Dock 2", self)
        dock2.setWidget(QTextEdit(self))
        self.addDockWidget(Qt.RightDockWidgetArea, dock2)

        # 设置 QSS
        qss = '''
            QMainWindow::separator {
                background-color: #A0A0A0;
                width: 0px; /* 设置分隔条宽度 */
                height: 0px; /* 设置分隔条高度 */
            }
        '''

        self.setStyleSheet(qss)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
