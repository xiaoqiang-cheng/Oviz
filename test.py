from PySide2.QtCore import Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMainWindow, QApplication, QDockWidget, QLabel
import PySide2
import os
dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建 Dock Widget
        self.dock = QDockWidget("Image Viewer", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        # 创建标签控件，并将其设置为 Dock Widget 的中央部件
        self.label = QLabel(self.dock)
        self.dock.setWidget(self.label)

        # 加载图像文件并显示在标签控件中
        pixmap = QPixmap("D:\\test_data\\camera0\\000000.jpg")

        print(pixmap)
        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignCenter)

        # 设置主窗口的标题和大小
        self.setWindowTitle("Image Viewer")
        self.setGeometry(100, 100, 800, 600)


if __name__ == '__main__':
    app = QApplication([])
    window = ImageViewer()
    window.show()
    app.exec_()

    import cv2
    img = cv2.imread("D:\\test_data\\camera0\\000000.jpg")
    cv2.imshow('1', img)
    cv2.waitKey(0)

