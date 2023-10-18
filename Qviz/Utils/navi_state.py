
class NaviState:

    def __init__(self):
        self.east   = 0
        self.north  = 0
        self.height = 0
        self.alpha  = 0
        self.beta   = 0
        self.theta  = 0
        self.position_state = 0
        self.lng = 0
        self.lat = 0
        self.ax  = 0
        self.ay  = 0
        self.az  = 0
        self.angular_speed_pitch = 0
        self.angular_speed_roll  = 0
        self.angular_speed_yaw   = 0
        self.ts = 0
        self.process_time = 0

    def set_from_rcs(self, line):
        line = line.strip().split(':')[-1]
        self.num = [float(i) for i in line.split()]

        self.east   = self.num[0]
        self.north  = self.num[1]
        self.height = self.num[2]
        self.alpha  = self.num[3]
        self.beta   = self.num[4]
        self.theta  = self.num[5]
        self.position_state = int(self.num[6])
        self.lng = self.num[7]
        self.lat = self.num[8]
        self.ax  = self.num[9]
        self.ay  = self.num[10]
        self.az  = self.num[11]
        self.angular_speed_pitch = self.num[12]
        self.angular_speed_roll  = self.num[13]
        self.angular_speed_yaw   = self.num[14]
        self.ts = self.num[15]
        self.process_time = self.num[16]

    def set_from_lidar_state(self, lidar_state):

        line = lidar_state.strip().split()

        self.east  = float(line[8])
        self.north = float(line[9])
        self.theta = float(line[10])
        self.position_state = int(line[12])
        self.height = float(line[17])
        self.alpha  = float(line[18])
        self.beta   = float(line[19])
        self.ts     = float(line[22])


class CANstate:
    def __init__(self):
        self.ts = 0
        self.vel = 0
        self.steer = 0

    def set_from_rcs(self, line):
        line = line.strip().split(':')[-1]
        self.num = [float(i) for i in line.split()]

        self.vel = self.num[0]
        self.steer = self.num[1]

    def set_from_lidar_state(self, line):
        line = line.strip().split()

        self.ts = float(line[0])
        self.vel = float(line[1])
        self.steer = float(line[2])

class GPSstate:
    def __init__(self):
        self.lng    = 0
        self.lat    = 0
        self.east   = 0
        self.north  = 0
        self.height = 0
        self.alpha  = 0
        self.beta   = 0
        self.theta  = 0
        self.state  = 0
        self.is_gps_pos_valid = 0
        self.is_gps_height_valid = 0
        self.ts = 0
        self.process_time = 0

    def set_from_rcs(self, line):
        line = line.strip().split(':')[-1]
        self.num = [float(i) for i in line.split()]

        self.lng    = self.num[0]
        self.lat    = self.num[1]
        self.east   = self.num[2]
        self.north  = self.num[3]
        self.height = self.num[4]
        self.alpha  = self.num[5]
        self.beta   = self.num[6]
        self.theta  = self.num[7]
        self.state  = self.num[8]
        self.is_gps_pos_valid = self.num[9]
        self.is_gps_height_valid = self.num[10]
        self.ts = self.num[11]
        self.process_time = self.num[12]

    def set_from_lidar_state(self, lidar_state):
        line = lidar_state.strip().split()

        self.lng   = float(line[3])
        self.lat   = float(line[4])
        self.east  = float(line[5])
        self.north = float(line[6])
        self.theta = float(line[7])
        self.state = int(line[11])
        self.height = float(line[15])
        self.alpha  = float(line[16])
        self.beta   = float(line[17])
        self.ts     = float(line[21])


class Date_time:
    def __init__(self, line):
        line = line.strip().split(',')
        line = [int(i.split(':')[-1].strip()) for i in line]

        self.year    = line[0]
        self.month   = line[1]
        self.day     = line[2]
        self.hour    = line[3]
        self.minute  = line[4]
        self.second  = line[5]
        self.usecond = line[6]
        self.ts      = line[7] / 100000.0


def rcs_to_lidar_state(can_state, gps_state, navi_state, date_time, frame_idx):

    ts_str = str(date_time.year) + str(date_time.month) + str(date_time.day) + "_" + ":".join([str(date_time.hour), str(date_time.minute), str(date_time.second)]) + "." + str(int(date_time.usecond/1000.0))

    state = str(date_time.ts)
    state = " ".join([state, str(can_state.vel), str(can_state.steer)])
    state = " ".join([state, str(gps_state.lng), str(gps_state.lat), str(gps_state.east),
            str(gps_state.north), str(gps_state.theta)])
    state = " ".join([state, str(navi_state.east), str(navi_state.north), str(navi_state.theta)])
    state = " ".join([state, str(gps_state.state), str(navi_state.position_state), str(frame_idx)])
    state = " ".join([state, str(gps_state.height), str(gps_state.alpha), str(gps_state.beta)])
    state = " ".join([state, str(navi_state.height), str(navi_state.alpha), str(navi_state.beta)])
    state = " ".join([state, ts_str])
    #  state = " ".join([state, str(gps_state.ts), str(navi_state.ts)])
    state = " ".join([state, str(round(date_time.ts, 3)), str(round(date_time.ts, 3))])

    # TODO: what but cloud ts
    return state


if __name__ == '__main__':

    rcs_dump_file = 'navi.txt'
    lidar_state_file = 'ml_lidar_state'

    with open(lidar_state_file, 'w') as lidar_state:

        with open(rcs_dump_file, 'r') as rcs:
            frame_end = False
            frame_idx = 0
            for line in rcs:
                if '====================' in line:
                    frame_end = False
                    frame_idx = int(line.strip().split('[')[1].split(']')[0])

                if frame_end: continue

                if 'date & time' == line.split(':')[0].strip():
                    date_time = Date_time(line)

                gps_state = GPSstate()
                if 'gps_state' == line.split(':')[0].strip():
                    gps_state.set_from_rcs(line)

                if 'navi_state' == line.split(':')[0].strip():
                    navi_state = NaviState()
                    navi_state.set_from_rcs(line)

                if 'can_state' == line.split(':')[0].strip():
                    can_state = CANstate()
                    can_state.set_from_rcs(line)
                    frame_end = True

                if frame_end:
                    state_line = rcs_to_lidar_state(can_state, gps_state, navi_state, date_time,
                            frame_idx)

                    lidar_state.write(state_line + '\n')
