import numpy as np

class MovObj:
    def __init__(self):
        self.index = 0
        self.id = 0
        self.is_valid = 0
        self.x = 0
        self.y = 0
        self.height = 0
        self.theta = 0
        self.vel = 0
        self.vel_theta = 0
        self.acc = 0
        self.radius = 0
        self.occ_area = 0
        self.height = 0
        self.total_point_num = 0
        self.vertex_point = 0
        self.kind = 0
        self.motion_conf = 0
        self.position_conf = 0
        self.kind_conf = 0
        self.string = None

    def set_str(self, line):
        self.string = line

    def to_str(self):
        if self.string is not None:
            return self.string

        out_str = str(self.index)
        out_str = ' '.join(str(self.id))
        out_str = ' '.join([out_str, str(self.is_valid), str(self.x), str(self.y),
            str(self.theta)])
        out_str = ' '.join([out_str, str(self.vel), str(self.vel_theta), str(self.acc),
            str(self.radius)])
        out_str = ' '.join([out_str, str(self.height)])
        out_str = ' '.join([out_str, str(self.total_point_num)])
        for i in range(self.total_point_num):
            point = self.vertex_point[i]
            out_str = ' '.join([out_str, str(2*i), str(point[0]), str(point[1]), str(point[2])])

        out_str = ' '.join([out_str, str(self.kind), str(self.motion_conf), str(self.position_conf),
            str(self.kind_conf)])

        return out_str

    def from_str(self, line=None):
        if line is None and self.string is not None:
            line = self.string

        line = line.strip().split()

        self.index, self.id, self.is_valid = [int(i) for i in line[:3]]
        self.x, self.y, self.theta = [float(i) for i in line[3:6]]
        self.vel, self.vel_theta, self.acc, self.radius = [float(i) for i in line[6:10]]
        self.height = float(line[10])
        self.total_point_num = int(line[11])

        self.vertex_point = []
        for i in range(self.total_point_num):
            self.vertex_point.append([float(j) for j in line[12+4*i: 16+4*i][1:]])

        idx = 12 + 4 * self.total_point_num
        self.kind = int(line[idx])
        self.motion_conf, self.position_conf, self.kind_conf = [float(i) for  i in line[idx+1:]]

class LabelObj:
    def __init__(self, line=None):
        self.kind = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.height = 0
        self.width  = 0
        self.length = 0
        self.dir = 0
        self.id = 0
        self.conf = 0
        self.vx = 0
        self.vy = 0

        if line is not None:
            self.from_list(line)

    def to_str(self):
        out_str = str(self.kind)
        out_str = ' '.join([out_str, str(round(self.x, 3)), str(round(self.y, 3)), str(self.z)])
        out_str = ' '.join([out_str, str(self.height), str(self.width), str(self.length)])
        out_str = ' '.join([out_str, str(round(self.dir, 3)), str(self.id)])
        return out_str

    def from_list(self, line):
        self.kind = int(line[0])
        self.x = float(line[1])
        self.y = float(line[2])
        self.z = float(line[3])

        self.width  = float(line[4])
        self.length = float(line[5])
        self.height = float(line[6])
        self.dir = float(line[7])
        self.conf = float(line[8])

        self.vx = float(line[9])
        self.vy = float(line[10])
        #  self.id = int(line[8])
        # if (len(line) > 11):
        #     self.id = float(line[11])
        # if (len(line) > 12):
        #     self.vel = float(line[9])
        # if (len(line) > 13):
        #     self.acc = float(line[13])
        # else:
        #     self.acc = 0

    def from_str(self, line):
        line = line.strip().split()

        self.kind = int(line[0])
        self.x = float(line[1])
        self.y = float(line[2])
        self.z = float(line[3])
        self.height = float(line[4])
        self.width  = float(line[5])
        self.length = float(line[6])
        self.dir = float(line[7])
        #  self.id = int(line[8])
        self.id = float(line[8])

        if (len(line) > 9):
            self.vel = float(line[10])
        if (len(line) > 13):
            self.acc = float(line[13])
        else:
            self.acc = 0

