

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
        ):
        self.bbox_dims = bbox_dims
        self.color_dims = color_dims
        self.arrow_dims = arrow_dims
        self.text_dims = text_dims
        self.text_format = text_format


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

