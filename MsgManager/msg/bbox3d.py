
from .size import Size
from .position import Position

class BoundingBox3D(object):
    def __init__(self):
        self.cls = 0

        self.position = Position()
        self.size = Size()

        self.theta = 0.0
        self.conf = 0.0