from .utils import *
from tqdm import tqdm

class UosPCD:
    def __init__(self, pcd_path,
            sample_frame_step = 5,
            scene_frame_step = 20,
            roi_range = [-1, -1],
            pc_range = [-32.0, -50.0, -3.0, 32.0, 70.0, 10.0],
            veh_range = [-2, -2, -1, 2, 5, 3]) -> None:
        self.pcd_path = pcd_path
        if not os.path.exists(pcd_path):
            print("ERROR PCD path not exist!")
            return
        self.veh_name, self.lidar_metadata = get_metadata(pcd_path)
        self.sensor2ego_mat = get_sensor2ego_mat(self.lidar_metadata)
        self.navi_list = get_navi_state(pcd_path)
        self.framecnt = len(self.navi_list)
        self.sensor_cnt = len(self.lidar_metadata.keys())

        self.info_ego_pos_list = []
        self.info_sample_list = []

        self.pc_range = pc_range
        self.veh_range = veh_range
        self.key_frame_step = sample_frame_step
        self.scene_step = scene_frame_step
        self.roi_frame_range = roi_range

        self.ready_labeling_workspace(pcd_path)

        print("find sensor:", self.sensor_cnt, "find pcd:", self.framecnt, "step:", self.key_frame_step)
        # maybe add a pipeline meta to record per step

    def ready_labeling_workspace(self, save_dir):
        self.labeling_cloudmap_dir = os.path.join(save_dir, "cloudmap")
        self.labeling_cloudmap_fidx_dir = os.path.join(save_dir, "cloudmap_fidx")
        # self.labeling_cloud_filter = os.path.join(save_dir, "cloud_filter")
        self.labeling_key_frame_sample = os.path.join(save_dir, "sample")
        self.labeling_sweep_frame_sample = os.path.join(save_dir, "sweep")
        self.labeling_info_dir = os.path.join(save_dir, "info")

        self.labeled_ground_truth_dir = os.path.join(save_dir, "cloudmap_labeled")

        self.ego_pos_list_fname = os.path.join(save_dir, "info", "ego_pos_list.json")
        self.sample_fname = os.path.join(save_dir, "info", "sample.json")
        self.revert_seg_ins_label_dir = os.path.join(save_dir, "sample_labeled")


        if_not_exist_create(self.labeling_cloudmap_dir)
        if_not_exist_create(self.labeling_cloudmap_fidx_dir)
        if_not_exist_create(self.labeling_key_frame_sample)
        if_not_exist_create(self.labeling_sweep_frame_sample)
        if_not_exist_create(self.labeling_info_dir)
        if_not_exist_create(self.labeled_ground_truth_dir)

        if_not_exist_create(self.revert_seg_ins_label_dir)


    def get_pcd_filepath(self, sensor_id, frame_id):
        fname = "ml_lidar_raw_%d_%s.pcd"%(sensor_id + 1, str(frame_id).zfill(6))

        return os.path.join(self.pcd_path, fname)

    def trans_coord(self, mat, points, dim=[0, 1, 2]):
        pts_length, pts_dims= points.shape
        pc_xyz = np.hstack((points[:, dim], np.ones((pts_length, 1), dtype=np.float32)))
        pc_trans_xyz = np.dot(mat, pc_xyz.T).T[:, :3]
        points[:, dim] = pc_trans_xyz

        return points


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

    def mark(self, points, bboxes_path = "", seg_path = ""):
        if os.path.exists(seg_path):
            points = self.mark_points_by_seg(points)
        else:
            points = self.mark_points_by_height(points)

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


    def mapping(self, frame_range = [0, 200], bbox_root_path = "", seg_root_path = ""):
        world_pcd_list = []
        world_pcd_frame_list = []
        init_navi = self.navi_list[frame_range[0]].copy()

        for i in tqdm(range(*frame_range)):
            ego_pcd = self.get_frame_pcd(i)
            curr_navi_state = self.navi_list[i].copy()
            self.info_ego_pos_list.append(
                {
                    "token": i,
                    "timestamp": curr_navi_state[0],
                    "translation": curr_navi_state[[1, 2, 3]].tolist(),
                    "yaw": curr_navi_state[4],
                },
            )

            # is key frame
            if (i - frame_range[0]) % self.key_frame_step == 0:
                ego_pcd, filter_pcd = self.filter(ego_pcd)

                key_frame_sample_fname = os.path.join(self.labeling_key_frame_sample,
                                                str(i).zfill(6) + ".bin")

                resort_ego_pcd = np.concatenate((ego_pcd, filter_pcd))
                resort_ego_pcd.tofile(key_frame_sample_fname)

                self.info_sample_list.append(
                    {
                        "token": i,
                        "timestamp": curr_navi_state[0],
                        "format": "bin",
                        "filename": os.path.basename(key_frame_sample_fname),
                        "ego_pose_token": i
                    },
                )

                # ego pcd from x y z i to x y z label object
                ego_pcd_for_label = np.hstack((ego_pcd[:, :3],
                                            np.zeros((ego_pcd.shape[0], 1), dtype=np.float32),
                                            np.ones((ego_pcd.shape[0], 1), dtype=np.float32) * -1))
                bboxes_path = os.path.join(bbox_root_path, str(i).zfill(6) + ".txt")
                # mark ego pcd
                ego_pcd_for_label = self.mark(ego_pcd_for_label, bboxes_path=bboxes_path)



                curr_navi_state[[1,2,3]] -= init_navi[[1,2,3]]
                world_pcd = self.trans_coord(NaviState(*curr_navi_state).mat, ego_pcd_for_label)
                world_pcd_list.append(world_pcd)
                world_pcd_frame_list.append(np.ones(len(world_pcd), dtype=np.int32) * i)
            else:
                sweep_frame_fname = os.path.join(self.labeling_sweep_frame_sample,
                                            str(i).zfill(6) + ".bin")
                ego_pcd.tofile(sweep_frame_fname)
        mapping_pcd = np.concatenate(world_pcd_list)
        frame_idx_bin = np.concatenate(world_pcd_frame_list)
        # mapping_pcd = self.voxelize(mapping_pcd)
        return mapping_pcd, frame_idx_bin

    def revert(self):
        labeled_cloudmaps = os.listdir(self.labeled_ground_truth_dir)
        for gts_cloudmap in tqdm(labeled_cloudmaps):
            gts_cloudmap_path = os.path.join(self.labeled_ground_truth_dir, gts_cloudmap)
            gts_cloudmap_frame_idx_path = os.path.join(self.labeling_cloudmap_fidx_dir,
                        gts_cloudmap.replace(".pcd", ".bin"))

            ground_truth_pcd = read_pcd(gts_cloudmap_path)
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
                ins_temp = ground_truth_pcd[:, -2][mask].astype(np.int32)

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

    def run(self, bbox_root_path = "", seg_root_path = ""):
        scene_frame_num = self.scene_step * self.key_frame_step
        roi_frame_range = [
            min(self.framecnt, max(0, self.roi_frame_range[0])),
            max(0, min(self.framecnt, self.roi_frame_range[1])),
        ]
        print("roi range is: %s"%str(roi_frame_range))
        for frame in range(*roi_frame_range, scene_frame_num):
            end_frame = frame + scene_frame_num
            # when scene frame < scene_frame_num break
            if end_frame > roi_frame_range[-1]: break

            scene_frame_range = [frame, end_frame]
            scene_range_name = "_".join(map(str, scene_frame_range))
            cloudmap_fname = os.path.join(self.labeling_cloudmap_dir,
                        scene_range_name + ".pcd")
            cloudmap_idx_fname = os.path.join(self.labeling_cloudmap_fidx_dir,
                        scene_range_name + ".bin")

            cloudmap, cloudmap_frame = self.mapping(scene_frame_range)

            write_pcd(cloudmap_fname, cloudmap,
                    filed = [('x', np.float32) ,
                            ('y', np.float32),
                            ('z', np.float32),
                            ('label', np.int32),
                            ('object', np.int32)])

            cloudmap_frame.tofile(cloudmap_idx_fname)

        write_json(self.info_ego_pos_list, self.ego_pos_list_fname)
        write_json(self.info_sample_list, self.sample_fname)




if __name__=="__main__":
    pcd_root_dir = "/home/uisee/lidar_20231106141855"
    uos_pcd = UosPCD(pcd_root_dir)
    # uos_pcd.revert()
    uos_pcd.run()
