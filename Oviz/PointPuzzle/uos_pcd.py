from Oviz.Utils.common_utils import *
from .utils import *
from tqdm import tqdm
import math
# import PySimpleGUI as sg
import Oviz.View.custom_progress as sg

import matplotlib.pyplot as plt
from .points_icp import CustomKissICP

class UOSLidarData:
    def __init__(self, pcd_path, image_path = []):

        self.pcd_path = pcd_path
        self.image_path = image_path
        self.image_fname_list = []
        self.image_timestamp_list = []

        for f in self.image_path:
            image_list, timestamp_list = find_files_with_extension(f)
            self.image_fname_list.append(image_list)
            self.image_timestamp_list.append(timestamp_list)

        self.veh_name, self.lidar_metadata = get_metadata(pcd_path)
        self.sensor2ego_mat = get_sensor2ego_mat(self.lidar_metadata)
        self.navi_list = get_navi_state(pcd_path)
        self.framecnt = len(self.navi_list)
        self.sensor_cnt = len(self.lidar_metadata.keys())


    def get_pcd_filepath(self, sensor_id, frame_id):
        fname = "ml_lidar_raw_%d_%s.pcd"%(sensor_id + 1, str(frame_id).zfill(6))

        return os.path.join(self.pcd_path, fname)

    def get_image_filepath(self, camera_id = 0, frame_id = 0):
        if len(self.image_path) <= camera_id:
            return None
        lidar_t = self.navi_list[frame_id][0]
        best_image_path = None
        curr_camera_timestamp_list = self.image_timestamp_list[camera_id]
        min_time_difference = float('inf')

        for j, img_t in enumerate(curr_camera_timestamp_list):
            time_difference = abs(img_t - lidar_t)
            if time_difference < min_time_difference:
                min_time_difference = time_difference
                best_image_path = self.image_fname_list[camera_id][j]
                if time_difference < 0.05:
                    break
        return best_image_path

    def trans_coord(self, mat, points, dim=[0, 1, 2]):
        pts_length, pts_dims= points.shape
        pc_xyz = np.hstack((points[:, dim], np.ones((pts_length, 1), dtype=np.float32)))
        pc_trans_xyz = np.dot(mat, pc_xyz.T).T[:, :3]
        points[:, dim] = pc_trans_xyz

        return points

    def get_frame_image(self, frame_id, camera_id = [0]):
        image_fpath = []
        for i in camera_id:
            fpath = self.get_image_filepath(i, frame_id)
            image_fpath.append(fpath)
        return image_fpath


    def get_frame_pcd(self, frame_id):
        multi_pcd_list = []
        for i, sensor_key in enumerate(self.sensor2ego_mat.keys()):
            pcd_file = self.get_pcd_filepath(i, frame_id)
            sensor_pcd = read_pcd(pcd_file)
            sensor2ego = self.sensor2ego_mat[sensor_key]
            ego_pcd = self.trans_coord(sensor2ego, sensor_pcd)
            multi_pcd_list.append(ego_pcd)

        curr_frame_ego_pcd = np.concatenate(multi_pcd_list)
        return curr_frame_ego_pcd.astype(np.float32)



class UosPCD:
    def __init__(self, pcd_path,
            image_path = [],
            sample_frame_step = 5,
            scene_frame_step = 20,
            roi_range = [-1, -1],
            pc_range = [-32.0, -50.0, -3.0, 32.0, 70.0, 10.0],
            veh_range = [-2, -2, -1, 2, 5, 3],
            mode = "build") -> None:
        self.pcd_path = pcd_path
        if not os.path.exists(pcd_path):
            print("ERROR PCD path not exist!")
            return

        if mode == "build":
            self.uos_lidar_data = UOSLidarData(self.pcd_path, image_path)
            self.navi_list = self.uos_lidar_data.navi_list
            self.framecnt = self.uos_lidar_data.framecnt
            self.sensor_cnt = self.uos_lidar_data.sensor_cnt
            self.enable_icp = True

        self.info_ego_pos_list = []
        self.info_sample_list = []

        self.pc_range = pc_range
        self.veh_range = veh_range
        self.key_frame_step = sample_frame_step
        self.scene_step = scene_frame_step
        self.roi_frame_range = roi_range

        self.ready_labeling_workspace(os.path.join(pcd_path, "useg_labeling"))
        # maybe add a pipeline meta to record per step

    def ready_labeling_workspace(self, save_dir):
        self.labeling_cloudmap_dir = os.path.join(save_dir, "cloudmap")
        self.labeling_cloudmap_fidx_dir = os.path.join(save_dir, "cloudmap_fidx")
        self.labeling_cloudmap_patch_dir = os.path.join(save_dir, "patch_for_anno", "cloudmap")
        self.labeling_image_patch_dir = os.path.join(save_dir, "patch_for_anno", "image_align")
        # self.labeling_cloud_filter = os.path.join(save_dir, "cloud_filter")
        self.labeling_key_frame_sample = os.path.join(save_dir, "sample", "lidar")
        self.labeling_sweep_frame_sample = os.path.join(save_dir, "sweep", "lidar")
        self.labeling_key_frame_sample_camera = os.path.join(save_dir, "sample", "camera")
        self.labeling_sweep_frame_sample_camera = os.path.join(save_dir, "sweep", "camera")

        self.labeling_info_dir = os.path.join(save_dir, "info")

        self.labeled_ground_truth_dir = os.path.join(save_dir, "cloudmap_labeled")

        self.ego_pos_list_fname = os.path.join(save_dir, "info", "ego_pos_list.json")
        self.sample_fname = os.path.join(save_dir, "info", "sample.json")
        self.revert_seg_ins_label_dir = os.path.join(save_dir, "sample_labeled")


        if_not_exist_create(self.labeling_cloudmap_dir)
        if_not_exist_create(self.labeling_cloudmap_fidx_dir)
        if_not_exist_create(self.labeling_cloudmap_patch_dir)
        if_not_exist_create(self.labeling_image_patch_dir)

        if_not_exist_create(self.labeling_key_frame_sample)
        if_not_exist_create(self.labeling_key_frame_sample_camera)
        if_not_exist_create(self.labeling_sweep_frame_sample)
        if_not_exist_create(self.labeling_sweep_frame_sample_camera)

        if_not_exist_create(self.labeling_info_dir)
        if_not_exist_create(self.labeled_ground_truth_dir)

        if_not_exist_create(self.revert_seg_ins_label_dir)

    def get_frame_pcd(self, frame_id):
        return self.uos_lidar_data.get_frame_pcd(frame_id=frame_id)

    def get_frame_image(self, frame_id, camera_id = [0]):
        return self.uos_lidar_data.get_frame_image(frame_id=frame_id, camera_id=camera_id)

    def only_pcd2bin(self):
        for i in tqdm(range(self.framecnt)):
            ego_pcd = self.get_frame_pcd(i)
            ego_pcd_fname = os.path.join(self.labeling_key_frame_sample, str(i).zfill(6) + ".bin")
            ego_pcd.tofile(ego_pcd_fname)
            self.update_progress("pcd2bin", i, self.framecnt)


    def filter_points_by_range(self, points,
                veh_range = [-2, -2, -1, 2, 5, 3],
                pc_range = [-50.0, -50.0, -3.0, 50.0, 50.0, 5.0]):

        v_min_x, v_min_y, v_min_z, v_max_x, v_max_y, v_max_z = veh_range
        min_x, min_y, min_z, max_x, max_y, max_z = pc_range

        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]

        vel_mask = ~(
            (x >= v_min_x) & (x <= v_max_x) &
            (y >= v_min_y) & (y <= v_max_y) &
            (z >= v_min_z) & (z <= v_max_z)
        )
        within_range = (
            (x >= min_x) & (x <= max_x) &
            (y >= min_y) & (y <= max_y) &
            (z >= min_z) & (z <= max_z)
        ) & vel_mask

        # 根据布尔索引过滤点
        filtered_points = points[within_range]

        return filtered_points, ~within_range

    def mark_points_by_bboxes(self, points, bboxes_path = ""):
        gt_bboxes = np.loadtxt(bboxes_path, dtype=np.float32)
        if len(gt_bboxes.shape) == 1:
            gt_bboxes = gt_bboxes.reshape(1, -1)

        gt_labels = gt_bboxes[:, 0].astype(np.int32)
        gt_bboxes = gt_bboxes[:, 1:-1]

        pts_semantic_label, pts_instance_label = labeling_point_in_rbbox(points, gt_bboxes, gt_labels)
        points[:, -2] = pts_semantic_label
        points[:, -1] = pts_instance_label
        return points

    def mark_points_by_seg(self, points, seg_path = ""):
        return points

    def mark_points_by_height(self, points, height_range = [-0.6, 0.2], cls_id = 11):
        mask = (points[:, 2] > height_range[0]) & (points[:, 2] <  height_range[1])
        points[:, -2][mask] = cls_id

        return points

    def mark(self, points, bboxes_path = "", seg_path = "", height_range=[-0.6, 0.2]):
        if os.path.exists(seg_path):
            points = self.mark_points_by_seg(points)
        else:
            points = self.mark_points_by_height(points, height_range)

        if os.path.exists(bboxes_path):
            points = self.mark_points_by_bboxes(points, bboxes_path)

        return points

    def filter(self, points):
        range_points, out_range_mask = self.filter_points_by_range(points, self.veh_range, self.pc_range)

        return range_points, points[out_range_mask]

    def voxelize(self, points, voxel_size=0.1):
        pc_range = np.array(self.pc_range)
        res_coors = np.floor((points[:, :3] - pc_range[None, :3]) / voxel_size).astype(np.int32)
        unique_val, uni_index, uni_inv = np.unique(res_coors, return_index = True, return_inverse=True, axis=0)
        points[uni_index, :3] = (unique_val + 0.5) * voxel_size + pc_range[None, :3]

        return points[uni_index]

    def update_progress(self, title, idx, length):
        return sg.one_line_progress_meter(title , idx + 1, length, orientation='h')

    def trans_coord(self, mat, points, dim=[0, 1, 2]):
        return self.uos_lidar_data.trans_coord(mat, points, dim)


    def mapping(self, frame_range = [0, 200], max_frame = -1,
                bbox_root_path = "", seg_root_path = "", height_range=[-0.6, 0.2],
                split_dist = 10):
        world_pcd_list = []
        world_pcd_frame_list = []

        if self.enable_icp:
            roi_navi_state = [np.eye(4)]
            last_split_navi = np.zeros(4, dtype=np.float32)
        else:
            init_navi = self.navi_list[frame_range[0]].copy()
            first_navi = init_navi.copy()
            first_navi[[1,2,3]] = 0
            roi_navi_state = [first_navi]
            last_split_navi = first_navi.copy()

        camera_id_list = list(range(len(self.uos_lidar_data.image_path)))
        roi_image_state = [self.get_frame_image(frame_range[0], camera_id_list)]

        for i in tqdm(range(*frame_range)):
            ego_pcd = self.get_frame_pcd(i)
            curr_navi_state = self.navi_list[i].copy()

            if self.enable_icp:
                icp_pose_mat = self.odometry.run_icp(ego_pcd, curr_navi_state[0])

            self.info_ego_pos_list.append(
                {
                    "token": i,
                    "timestamp": curr_navi_state[0],
                    "translation": curr_navi_state[[1, 2, 3]].tolist(),
                    "yaw": curr_navi_state[4],
                },
            )

            curr_camera_list = self.get_frame_image(i, camera_id=camera_id_list)

            # is key frame
            if (i - frame_range[0]) % self.key_frame_step == 0:
                ego_pcd, filter_pcd = self.filter(ego_pcd)

                key_frame_sample_fname = os.path.join(self.labeling_key_frame_sample,
                                                str(i).zfill(6) + ".bin")

                for im_idx, img_path in enumerate(curr_camera_list):
                    target_img_dir = os.path.join(self.labeling_key_frame_sample_camera, str(im_idx))
                    if_not_exist_create(target_img_dir)
                    dst_img_name = os.path.join(target_img_dir, str(i).zfill(6) + img_path[-4:])
                    os.system("cp -r %s %s"%(img_path, dst_img_name))

                resort_ego_pcd = np.concatenate((ego_pcd, filter_pcd))
                resort_ego_pcd.tofile(key_frame_sample_fname)

                self.info_sample_list.append(
                    {
                        "token"         : i,
                        "timestamp"     : curr_navi_state[0],
                        "format"        : "bin",
                        "filename"      : os.path.basename(key_frame_sample_fname),
                        "ego_pose_token": i
                    },
                )

                # ego pcd from x y z i to x y z label object
                ego_pcd_for_label = np.hstack((ego_pcd[:, :3],
                                            np.zeros((ego_pcd.shape[0], 1), dtype=np.float32),
                                            np.ones((ego_pcd.shape[0], 1), dtype=np.float32) * -1))
                bboxes_path = os.path.join(bbox_root_path, str(i).zfill(6) + ".txt")
                # mark ego pcd
                ego_pcd_for_label = self.mark(ego_pcd_for_label, bboxes_path=bboxes_path, height_range=height_range)

                if self.enable_icp:
                    world_pcd = self.trans_coord(icp_pose_mat, ego_pcd_for_label)
                    curr_navi_state = icp_pose_mat[:, -1]
                    if self.calc_eular_dist(last_split_navi - curr_navi_state) >= split_dist:
                        roi_navi_state.append(icp_pose_mat)
                        roi_image_state.append(curr_camera_list)
                        last_split_navi = curr_navi_state.copy()
                else:
                    curr_navi_state[[1, 2, 3]] -= init_navi[[1, 2, 3]]
                    world_pcd = self.trans_coord(NaviState(*curr_navi_state).mat, ego_pcd_for_label)
                    if self.calc_eular_dist(last_split_navi - curr_navi_state) >= split_dist:
                        roi_navi_state.append(curr_navi_state)
                        roi_image_state.append(curr_camera_list)
                        last_split_navi = curr_navi_state.copy()

                world_pcd_list.append(world_pcd)
                world_pcd_frame_list.append(np.ones(len(world_pcd), dtype=np.int32) * i)
            else:
                sweep_frame_fname = os.path.join(self.labeling_sweep_frame_sample,
                                            str(i).zfill(6) + ".bin")
                ego_pcd.tofile(sweep_frame_fname)

                for im_idx, img_path in enumerate(curr_camera_list):
                    target_img_dir = os.path.join(self.labeling_sweep_frame_sample_camera, str(im_idx))
                    if_not_exist_create(target_img_dir)
                    dst_img_name = os.path.join(target_img_dir, str(i).zfill(6) + img_path[-4:])
                    os.system("cp -r %s %s"%(img_path, dst_img_name))
            if not self.update_progress("build", i, max_frame):
                break
        mapping_pcd = np.concatenate(world_pcd_list)
        frame_idx_bin = np.concatenate(world_pcd_frame_list)

        return mapping_pcd, frame_idx_bin, roi_navi_state, roi_image_state

    def calc_eular_dist(self, pos):
        return math.sqrt((pos[1] ** 2 + pos[2] ** 2))

    def split_cloud_map(self, cloud_map,
                        cloud_map_frame_id = None,
                        scene_name = "",
                        roi_navi_state = None, roi_image_state = None,
                        split_dist = None):
        patch_mask_metadata_fname = os.path.join(self.labeling_cloudmap_patch_dir, "cloud_mask_metadata.pkl")
        patch_mask = {}
        mask_any = np.ones(len(cloud_map), dtype=bool)

        for i, navi in enumerate(roi_navi_state):
            if self.enable_icp:
                inv_mat = np.linalg.inv(navi)
            else:
                inv_mat = np.linalg.inv(NaviState(*navi).mat)
            local_pcd = self.trans_coord(inv_mat, cloud_map.copy())
            if i == len(roi_navi_state) - 1:
                mask = mask_any
            else:
                # inv_mat = np.linalg.inv(NaviState(*navi).mat)
                # local_pcd = self.trans_coord(inv_mat, cloud_map.copy())
                mask = (local_pcd[:, 1] < (split_dist / 2.0)) & mask_any
                mask_any = ~mask & mask_any
                # cloud = local_pcd[mask]

            cloud = local_pcd[mask]
            if len(cloud) == 0:
                # import ipdb
                # ipdb.set_trace()
                continue

            # cloud[:, [0,1,2]] -= navi[[1,2,3]]
            scene_patch_name = scene_name + "_" + str(i).zfill(4)

            patch_pcd_fname = os.path.join(self.labeling_cloudmap_patch_dir, scene_patch_name + ".pcd")
            if scene_name not in patch_mask.keys():
                patch_mask[scene_name] = {}

            patch_mask[scene_name][scene_patch_name] = mask

            if cloud_map_frame_id is None:
                write_pcd(patch_pcd_fname, cloud,
                                filed = [('x', np.float32) ,
                                ('y', np.float32),
                                ('z', np.float32),
                                ('label', np.int32),
                                ('object', np.int32)])
            else:
                cloud_idx = cloud_map_frame_id[mask].reshape(-1, 1)
                cloud_with_frame = np.concatenate([cloud, cloud_idx], axis=1)
                write_pcd(patch_pcd_fname, cloud_with_frame,
                                filed = [('x', np.float32) ,
                                ('y', np.float32),
                                ('z', np.float32),
                                ('label', np.int32),
                                ('object', np.int32),
                                ('frame', np.int32),])
                # copy img
            image_list = roi_image_state[i]
            for ix, fi in enumerate(image_list):
                if fi is not None:
                    target_img_dir = os.path.join(self.labeling_image_patch_dir, str(ix))
                    if_not_exist_create(target_img_dir)
                    dst_img_name = os.path.join(target_img_dir, scene_patch_name + fi[-4:])
                    os.system("cp -r %s %s"%(fi, dst_img_name))
            # self.update_progress("split", i,  int(curr_dist_max / split_dist) + 1)
        serialize_data(patch_mask, patch_mask_metadata_fname)


    def revert(self):
        patch_mask_metadata_fname = os.path.join(self.labeling_cloudmap_patch_dir, "cloud_mask_metadata.pkl")
        patch_mask_metadata = deserialize_data(patch_mask_metadata_fname)

        for scene_name in tqdm(patch_mask_metadata.keys()):
            gts_cloudmap = scene_name + ".pcd"
            gts_cloudmap_path = os.path.join(self.labeling_cloudmap_dir, gts_cloudmap)
            gts_cloudmap_frame_idx_path = os.path.join(self.labeling_cloudmap_fidx_dir,
                        gts_cloudmap.replace(".pcd", ".bin"))

            ground_truth_pcd = read_pcd(gts_cloudmap_path)

            for gt_patch_name in tqdm(patch_mask_metadata[scene_name].keys()):
                mask = patch_mask_metadata[scene_name][gt_patch_name]
                gt_patch_pcd_fname = os.path.join(self.labeled_ground_truth_dir, gt_patch_name + ".pcd")
                ground_truth_patch_pcd = read_pcd(gt_patch_pcd_fname)
                ground_truth_pcd[mask] = ground_truth_patch_pcd

            frame_idx_array = np.fromfile(gts_cloudmap_frame_idx_path, dtype=np.int32)

            frame_list = np.unique(frame_idx_array)
            for f in frame_list:
                sample_name = str(f).zfill(6)
                sample_path = os.path.join(self.labeling_key_frame_sample, sample_name  + ".bin")
                sampe_pts = np.fromfile(sample_path, dtype=np.float32).reshape(-1, 4)
                seg_label = np.zeros(len(sampe_pts), dtype=np.int32)
                ins_label = np.zeros(len(sampe_pts), dtype=np.int32)

                mask = (frame_idx_array == f)

                seg_temp = ground_truth_pcd[:, -2][mask].astype(np.int32)
                ins_temp = ground_truth_pcd[:, -1][mask].astype(np.int32)

                seg_label[:len(seg_temp)] = seg_temp
                ins_label[:len(ins_temp)] = ins_temp

                label_pcd_path = os.path.join(self.revert_seg_ins_label_dir, sample_name  + ".pcd")
                label_pcd = np.concatenate([sampe_pts[:, :3],
                            seg_label.reshape(-1, 1).astype(np.float32),
                            ins_label.reshape(-1, 1).astype(np.float32)], axis=-1)
                write_pcd(label_pcd_path, label_pcd,
                            filed = [('x', np.float32) ,
                            ('y', np.float32),
                            ('z', np.float32),
                            ('label', np.int32),
                            ('object', np.int32)])



    def run(self, bbox_root_path = "", seg_root_path = "", height_range=[-0.6, 0.2], split_dist = 30):
        scene_frame_num = self.scene_step * self.key_frame_step
        if self.roi_frame_range[0] == -1 and self.roi_frame_range[1] == -1:
            self.roi_frame_range = [0, self.framecnt]
        roi_frame_range = [
            min(self.framecnt, max(0, self.roi_frame_range[0])),
            max(0, min(self.framecnt, self.roi_frame_range[1])),
        ]
        print("roi range is: %s"%str(roi_frame_range))
        for frame in range(*roi_frame_range, scene_frame_num):
            end_frame = frame + scene_frame_num
            # when scene frame < scene_frame_num break
            if end_frame > roi_frame_range[-1]: end_frame = roi_frame_range[-1]

            scene_frame_range = [frame, end_frame]
            scene_range_name = str(scene_frame_range[0]).zfill(6) + "_" + str(scene_frame_range[1]).zfill(6)
            cloudmap_fname = os.path.join(self.labeling_cloudmap_dir,
                        scene_range_name + ".pcd")
            cloudmap_idx_fname = os.path.join(self.labeling_cloudmap_fidx_dir,
                        scene_range_name + ".bin")

            if self.enable_icp:
                self.odometry = CustomKissICP()
            cloudmap, cloudmap_frame, roi_navi_state, roi_image_state = self.mapping(scene_frame_range, roi_frame_range[-1],
                        bbox_root_path, height_range=height_range, split_dist = split_dist)
            import ipdb
            ipdb.set_trace()
            write_pcd(cloudmap_fname, cloudmap,
                    filed = [('x', np.float32) ,
                            ('y', np.float32),
                            ('z', np.float32),
                            ('label', np.int32),
                            ('object', np.int32)])

            cloudmap_frame.tofile(cloudmap_idx_fname)
            self.split_cloud_map(cloudmap, cloudmap_frame,
                    scene_range_name, roi_navi_state, roi_image_state, split_dist)

        write_json(self.info_ego_pos_list, self.ego_pos_list_fname)
        write_json(self.info_sample_list, self.sample_fname)

    def show_3d_trajectory(self):
        fig = plt.figure()
        ax = fig.add_subplot(projection = '3d')


        ax.set_title("3D_navi")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.plot(self.navi_list[:, 1], self.navi_list[:, 2], self.navi_list[:, 3],
                c='b',marker='^',linestyle='-')
        plt.show()


if __name__=="__main__":
    pcd_root_dir = "/home/uisee/lidar_20231106141855"
    uos_pcd = UosPCD(pcd_root_dir)
    # uos_pcd.revert()
    uos_pcd.run()
