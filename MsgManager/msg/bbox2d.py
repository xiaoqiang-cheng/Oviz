
from .size import Size
from .position import Position


class BoundingBox2D(object):
    def __init__(self):
        self.cls = 0

        self.position = Position()
        self.size = Size()

        self.theta = 0.0
        self.conf = 0.0


if __name__ == "__main__":
    obj = BoundingBox2D()
    print(obj.__dict__)