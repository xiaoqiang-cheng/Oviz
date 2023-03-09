
class PointCloud(object):
    def __init__(self):
        self.timestamp = 0.0
        self.frame_cnt = 0
        self.data = []



if __name__ == "__main__":
    obj = PointCloud()
    print(obj.__dict__)