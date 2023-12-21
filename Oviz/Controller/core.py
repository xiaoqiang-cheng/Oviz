

class CloudmapSetting:
    def __init__(self,
        pcd_path = "",
        bbox3d_path = "",
        seg_path = "",
        cloudedmap_labeled_path = "",
        sample_frame_step = 5,
        scene_frame_step = 20,
        roi_range = [],
        pc_range = [],
        veh_range = [],
        ground_range = []
        ) -> None:
        self.pcd_path = pcd_path
        self.bbox3d_path = bbox3d_path
        self.seg_path = seg_path
        self.cloudedmap_labeled_path = cloudedmap_labeled_path
        self.sample_frame_step = sample_frame_step
        self.scene_frame_step = scene_frame_step
        self.roi_range = roi_range
        self.pc_range = pc_range
        self.veh_range = veh_range
        self.ground_range = ground_range


class PointCloudSetting:
    def __init__(self,
        points_dim = -1,
        points_type = "float32",
        xyz_dims = -1,
        wlh_dims = -1,
        color_dims = -1,
        show_voxel = False,
        ) -> None:
        self.points_dim = points_dim
        self.points_type = points_type
        self.xyz_dims = xyz_dims
        self.wlh_dims = wlh_dims
        self.color_dims = color_dims
        self.show_voxel = show_voxel


class Bbox3DSetting:
    def __init__(self,
            bbox_dims = -1,
            color_dims = -1,
            arrow_dims = -1,
            text_dims = -1,
            text_format = "",
            clock_offset = -1
        ):
        self.bbox_dims = bbox_dims
        self.color_dims = color_dims
        self.arrow_dims = arrow_dims
        self.text_dims = text_dims
        self.text_format = text_format
        self.clock_offset = clock_offset


class GlobalSetting:
    def __init__(self,
        record_screen = False) -> None:
        self.record_screen = record_screen

class RecordScreenSetting:
    def __init__(self,
        record_screen = False,
        mouse_record_screen = False):

        self.record_screen = record_screen
        self.mouse_record_screen = mouse_record_screen

class MagicPipeSetting:
    def __init__(self,
        enable = False,
        magic_params = None):
        self.enable = enable
        self.magic_params = magic_params

