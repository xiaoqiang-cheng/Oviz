import sys
sys.path.append("..")

# -----------pub demo code -------------
from manager import NodeRegister
from msg.pointcloud import PointCloud
from msg.bboxes3d import BoundingBoxes3D
from msg.bbox2d import BoundingBox2D
import time
msg = {
    "author" : "yuangao",
    "version" : 1.0
}

msg2 = {
    "author" : "chengxiaoqiang",
    "version" : 1.2
}



node = NodeRegister()
obj = BoundingBoxes3D()
obj.bboxes3d[0] = BoundingBox2D()
obj.bboxes3d[1] = BoundingBox2D()

while True:
    print("timestamp1:", time.time())
    print("pub msg:", obj)
    node.pub("test1", obj)

    time.sleep(1)
    print("pub msg2:", msg2)
    print("timestamp2:", time.time())
    node.pub("test2", msg2)
    time.sleep(1)