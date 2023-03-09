import os
import struct
import numpy as np
# import open3d as o3d
from .navi_state import GPSstate, NaviState, CANstate
from scipy.spatial.transform import Rotation
import pypcd


def crop_cloud_height(points, min=-0.5, max=4, return_idx=False):
    idx = (points[:, 2] > min) & (points[:, 2] < max)
    if return_idx:
        return points[idx], idx
    return points[idx]

def filter_out_veh(points, xmin=-1.5, xmax=1.5, ymin=-1, ymax=3, return_idx=False):
    idx = ((points[:, 1] > ymax) | (points[:, 1] < ymin) | (points[:, 0] > xmax) |
            (points[:, 0] < xmin))
    if return_idx:
        return points[idx], idx
    return points[idx]


def get_metadata(pcd_path):
    framework = {}
    sensor_cnt = 0

    #  pcd_cnt = sum(1 for line in open(os.path.join(pcd_path, 'ml_lidar_state')))

    with open(os.path.join(pcd_path, "lidar_metadata"), "r") as calib_para:
        for line in calib_para:
            if 'sensor' in line:
                sensor = line.strip().split(':')[0]
                framework[sensor] = {}
                sensor_cnt += 1
            elif 'vendor' in line:
                framework[sensor]['vendor'] = int(line.strip().split()[1])
            elif 'alpha' in line:
                line = line.split()
                framework[sensor]['alpha'] = float(line[1])
                framework[sensor]['beta'] = float(line[3])
                framework[sensor]['gamma'] = float(line[5])
            elif 'x_offset' in line:
                line = line.split()
                framework[sensor]['x_offset'] = float(line[1])
                framework[sensor]['y_offset'] = float(line[3])
                framework[sensor]['z_offset'] = float(line[5])
            elif 'calib_fname' in line:
                line = line.strip().split()
                if len(line) > 1:
                    framework[sensor]['calib_fname'] = line[1]
                else:
                    framework[sensor]['calib_fname'] = ""

            if 'vehicle_name' in line:
                line = line.strip().split()
                veh_name = line[0]

        framework['sensor_cnt'] = sensor_cnt
        #  framework['data_source'] = 2
        #  framework['start_frame_idx'] = 0
        #  framework['end_frame_idx'] = pcd_cnt

    return veh_name, framework

def read_pcd(path):
    # pp = o3d.io.read_point_cloud(path)
    # points = np.asarray(pp.points)

    # if pp.has_colors():
    #     colors = np.asarray(pp.colors)
    #     return (points, colors)
    points = pypcd.PointCloud.from_path(path)
    return (points.pc_data, None)

def read_bin(path):
    points = np.fromfile(path, dtype=np.float32).reshape(-1, 5)[..., :3]
    return (points, None)

def read_ml_lidar_state(path):
    with open(path, 'r') as ml:
        ml_lidar_state = ml.readlines()
        return ml_lidar_state

def check_plane_pcd(pcd_path):
    pcd_name = os.path.basename(pcd_path)
    if pcd_name.startswith('plane_') and pcd_name.endswith('.pcd'):
        return True
    return False

def get_plane_pcd_base(pcd_path):
    pcd_name = os.path.basename(pcd_path)
    plane = pcd_name.strip('.pcd').split('_')[-2:]
    plane = [float(i) for i in plane] # x/y
    plane.append(0.0) # add z
    return plane

def write_pcd(path, nparray):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(nparray)
    o3d.io.write_point_cloud(path, pcd)

def rotation_mat(theta):
   """ same as Rotation.from_euler('xyz', rot).as_matrix() """
   rx,ry,rz = theta
   Rx = np.array([[1,0,0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
   Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
   Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0],[0,0,1]])
   return np.dot(Rz, np.dot(Ry, Rx))

def get_rt_mat(metadata):
    r_mat_list = []
    t_mat_list = []
    for i in range(metadata['sensor_cnt']):
        calib = metadata['sensor_' + str(i)]
        rot = np.deg2rad([calib['alpha'], calib['beta'], calib['gamma']])
        t_mat = [calib['x_offset'], calib['y_offset'], calib['z_offset']]
        r_mat = Rotation.from_euler('xyz', rot).as_matrix().T
        r_mat_list.append(r_mat)
        t_mat_list.append(t_mat)
    return r_mat_list, t_mat_list

def transform_point(points, r_mat, t_mat):
    return np.dot(points, r_mat) + t_mat

def cvt_pcd_to_bin_plane(pcd_path):
    """ cvt plane pcd to UISEEToolKit format """
    pcd_path = os.path.abspath(pcd_path)
    out_path = 'plane.bin'

    print("Input Path: ", pcd_path)
    print("Output Path: ", out_path)

    pcd, _ = read_pcd(pcd_path)

    base = [0.0, 0.0, 0.0]
    if check_plane_pcd(pcd_path):
        base = get_plane_pcd_base(pcd_path)
        print("pcd is plane pcd, coordiate base: ", base)

    with open(out_path, 'wb') as out:
        out.write(struct.pack('8s', b'PLINEEEF'))
        out.write(struct.pack('8s', b'1')) # reserved
        out.write(struct.pack('q', pcd.shape[0]))
        out.write(struct.pack('d', base[0]))
        out.write(struct.pack('d', base[1]))

        for pt in pcd:
            out.write(struct.pack('f', pt[0]))
            out.write(struct.pack('f', pt[1]))
            out.write(struct.pack('f', pt[2]))
            out.write(struct.pack('f', 20))

    print("Done!")

def read_bin_plane(file_path):
    """ read plane.bin from UISEEToolKit """
    point_list = []
    if not os.path.isfile(file_path):
        return point_list

    with open(file_path, 'rb') as binfile:
        magic = struct.unpack('8s', binfile.read(8))
        version = struct.unpack('s', binfile.read(1))
        reserved = binfile.read(7)
        cloud_size= struct.unpack('q', binfile.read(8))
        init_x= struct.unpack('d', binfile.read(8))
        init_y= struct.unpack('d', binfile.read(8))

        print('Reading:', file_path)
        print('Magic:', magic)
        print('Version:', version)
        #  print(reserved)
        print('Size:', cloud_size[0])
        print('Base:', init_x[0], init_y[0])
        for count in range(cloud_size[0]):
            cloud_x = struct.unpack('f', binfile.read(4))
            cloud_y = struct.unpack('f', binfile.read(4))
            cloud_z = struct.unpack('f', binfile.read(4))
            cloud_intensity= struct.unpack('f', binfile.read(4))
            #  res_x = cloud_x[0] + init_x[0]
            #  res_y = cloud_y[0] + init_y[0]
            res_x = cloud_x[0]
            res_y = cloud_y[0]
            point_list.append([res_x, res_y, cloud_z[0]])
    return point_list, [init_x[0], init_y[0], 0.0]

if __name__ == '__main__':

    out_path = 'plane.bin'
    points = read_bin_plane(out_path)
