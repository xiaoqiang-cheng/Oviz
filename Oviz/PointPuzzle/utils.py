import numpy as np
import os
from .pypcd import PointCloud, save_point_cloud_bin
import json
import pickle

class NaviState:
    def __init__(self, t, x, y, z, theta, conf) -> None:
        self.timestamp = t
        self.x = x
        self.y = y
        self.z = z
        self.theta = theta
        self.conf = conf
        cos_ = np.cos(theta - np.pi / 2)
        sin_ = np.sin(theta - np.pi / 2)

        self.mat = np.array([
            [cos_, -sin_, 0, x],
            [sin_, cos_,  0, y],
            [0,     0,    1, z],
            [0,     0,    0, 1],
        ])

INFERENCE_MODE = 0
PARSE_LABEL_MODE = 1


POINTS_CLASS_NAME = [
    'ignore', 'barrier', 'bicycle', 'bus', 'car', 'construction_vehicle', 'motorcycle',
    'pedestrian', 'traffic_cone', 'trailer', 'truck', 'driveable_surface', 'sidewalk',
    'terrain', 'other_flat', 'manmade', 'vegetation', 'pole', 'traffic sign', 'tricycle'
]

BBOX_CLASS_NAME = [
    'car', 'truck', 'bus', 'bicycle', 'triple_wheel', 'human', 'animal', 'traffic_cone', 'other'
]

LABEL_NAME_MAPPING = {
    'ignore'        : 'ignore',
    'car'           : 'car',
    'truck'         : 'truck',
    'bus'           : 'bus',
    'bicycle'       : 'bicycle',
    'triple_wheel'  : 'tricycle',
    'human'         : 'pedestrian',
    'animal'        : 'ignore',
    'traffic_cone'  : 'traffic_cone',
    'other'         : 'ignore',
}

def serialize_data(data:dict, file_path):
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)

def deserialize_data(file_path):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    return data


def point_in_rbbox(pts, bbox, eps=1e-2):
    pts_xyz = pts[:, :3].copy()

    rot = -bbox[-1]

    rot_m = np.array([
        np.cos(rot), -np.sin(rot),
        np.sin(rot), np.cos(rot)
    ]).reshape(2, 2)

    local_xyz = pts_xyz - bbox[np.newaxis, :3]
    local_xyz[:, :2] = np.dot(local_xyz[:, :2], rot_m.T)

    w, l, h = bbox[3:6] + eps
    w += 0.1
    l += 0.1

    in_flag = (local_xyz[:, 0] > -w / 2.) & (local_xyz[:, 0] < w / 2.) &         \
                    (local_xyz[:, 1] > -l / 2.) & (local_xyz[:, 1] < l / 2.) &    \
                        (local_xyz[:, 2] > -h / 2.) & (local_xyz[:, 2] < (h / 2. + 0.15))
    return in_flag



def labeling_point_in_rbbox(pts, gt_bboxes, gt_labels):
    # pts_semantic_mask = np.zeros(pts.shape[0]).astype(np.int32)
    # pts_instance_mask = - np.ones(pts.shape[0]).astype(np.int32)

    pts_semantic_mask = pts[:, -2]
    pts_instance_mask = pts[:, -1]

    num_bbox = gt_bboxes.shape[0]
    for i in range(num_bbox):
        bbox_label = gt_labels[i]
        semantic_label = POINTS_CLASS_NAME.index(LABEL_NAME_MAPPING[BBOX_CLASS_NAME[bbox_label]])

        in_flag = point_in_rbbox(pts, gt_bboxes[i])
        pts_semantic_mask[in_flag] = semantic_label
        pts_instance_mask[in_flag] = i
    return pts_semantic_mask, pts_instance_mask



def if_not_exist_create(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def get_metadata(pcd_path):
    metadata = {}
    sensor_cnt = 0
    veh_name = None
    with open(os.path.join(pcd_path, "lidar_metadata"), "r") as calib_para:
        for line in calib_para:
            if 'sensor' in line:
                sensor = line.strip().split(':')[0]
                metadata[sensor] = {}
                sensor_cnt += 1
            elif 'vendor' in line:
                metadata[sensor]['vendor'] = int(line.strip().split()[1])
            elif 'alpha' in line:
                line = line.split()
                metadata[sensor]['alpha'] = np.deg2rad(float(line[1]))
                metadata[sensor]['beta']  = np.deg2rad(float(line[3]))
                metadata[sensor]['gamma'] = np.deg2rad(float(line[5]))
            elif 'x_offset' in line:
                line = line.split()
                metadata[sensor]['x_offset'] = float(line[1])
                metadata[sensor]['y_offset'] = float(line[3])
                metadata[sensor]['z_offset'] = float(line[5])
            elif 'calib_fname' in line:
                line = line.strip().split()
                if len(line) > 1:
                    metadata[sensor]['calib_fname'] = line[1]
                else:
                    metadata[sensor]['calib_fname'] = ""

            if 'vehicle_name' in line:
                line = line.strip().split()
                veh_name = line[0]

    return veh_name, metadata

def get_sensor2ego_mat(metadata):
    def create_transformation_matrix(x_offset, y_offset, z_offset, alpha, beta, gamma):
        Rx = np.array([[1, 0, 0],
                    [0, np.cos(alpha), -np.sin(alpha)],
                    [0, np.sin(alpha), np.cos(alpha)]])
        Ry = np.array([[np.cos(beta), 0, np.sin(beta)],
                    [0, 1, 0],
                    [-np.sin(beta), 0, np.cos(beta)]])

        Rz = np.array([[np.cos(gamma), -np.sin(gamma), 0],
                    [np.sin(gamma), np.cos(gamma), 0],
                    [0, 0, 1]])

        R = Rz.dot(Ry.dot(Rx))

        T = np.array([x_offset, y_offset, z_offset]).reshape(-1, 1)
        transformation_matrix = np.vstack((np.hstack((R, T)), [0, 0, 0, 1]))
        return transformation_matrix.astype(np.float32)

    metadata_rt_mat = {}

    for sensor, calib in metadata.items():
        metadata_rt_mat[sensor] = create_transformation_matrix(
                calib['x_offset'], calib['y_offset'], calib['z_offset'],
                calib['alpha'], calib['beta'], calib['gamma'])
    return metadata_rt_mat

def get_navi_state(pcd_path):
    lidar_state_path = os.path.join(pcd_path, "ml_lidar_state")
    ret = []
    low_percision_frame = []
    with open(lidar_state_path, 'r') as ml:
        lines = ml.readlines()
        for i, line in enumerate(lines):
            segments = line.split()
            if len(segments) < 12: continue
            state = int(segments[12])
            if state == 3:
                conf = 1.0
            else:
                conf = 0.1
                low_percision_frame.append(i)
            # timestamp x y z yaw conf
            ret.append([float(segments[0]), float(segments[8]), float(segments[9]), float(segments[14]), float(segments[10]), conf])
    print(low_percision_frame)
    return np.array(ret).astype(np.float64)


def read_pcd(path):
    points = PointCloud.from_path(path)
    return np.array(points.pc_data.tolist(), dtype=np.float32)

def write_pcd(path, nparray,
        filed = [('x', np.float32) ,
                    ('y', np.float32),
                    ('z', np.float32),
                    ('i', np.uint32)]):
    dtype = np.dtype(filed)

    new_bin = []
    for i, dt in enumerate(filed):
        new_bin.append(nparray[:, i].astype(dt[-1]))
    out = np.rec.fromarrays(new_bin, dtype=dtype)

    pc = PointCloud.from_array(out)
    save_point_cloud_bin(pc, path)


def write_json(json_data, json_name):
    # Writing JSON data
    with open(json_name, 'w', encoding="utf-8") as f:
        json.dump(json_data, f, indent=4)