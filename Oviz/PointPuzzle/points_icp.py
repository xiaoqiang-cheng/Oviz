
from kiss_icp.config import load_config
from kiss_icp.kiss_icp import KissICP
import numpy as np
class CustomKissICP(object):

    def __init__(self) -> None:
        self.config = load_config(None, deskew=False, max_range=None)
        self.odometry = KissICP(config=self.config)

    def run_icp(self, raw_points, timestamp):
        timestamps = np.array([timestamp] * raw_points.shape[0])
        source, keypoints = self.odometry.register_frame(raw_points[:, 0:3], timestamps)
        realtive_pos = self.odometry.poses[-1]
        return realtive_pos
