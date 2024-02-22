import copy
import open3d as o3d
import numpy as np

def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.paint_uniform_color([1, 0.706, 0])
    target_temp.paint_uniform_color([0, 0.651, 0.929])
    source_temp.transform(transformation)
    o3d.visualization.draw_geometries([source_temp, target_temp],
                                      zoom=0.4459,
                                      front=[0.9288, -0.2951, -0.2242],
                                      lookat=[1.6784, 2.0612, 1.4451],
                                      up=[-0.3402, -0.9189, -0.1996])


source = o3d.io.read_point_cloud("/home/uisee/Develop/lidar_uos/install/data/labelseg_demo/lidar_20240126141421/useg_labeling/sample_labeled/000120.pcd")
target = o3d.io.read_point_cloud("/home/uisee/Develop/lidar_uos/install/data/labelseg_demo/lidar_20240126141421/useg_labeling/sample_labeled/000125.pcd")
threshold = 0.02

trans_init = np.asarray([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
    ])

draw_registration_result(source, target, trans_init)

import ipdb
ipdb.set_trace()
reg_p2p = o3d.pipelines.registration.registration_icp(
    source, target, threshold, trans_init,
    o3d.pipelines.registration.TransformationEstimationPointToPoint(),
    o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000))

print(reg_p2p)
print("Transformation is:")
print(reg_p2p.transformation)
draw_registration_result(source, target, reg_p2p.transformation)