

def enable_pointcloud_supply(self, key, data_dict):
    import os
    import numpy as np
    seg_label_path = "/home/uisee/MainDisk/Detect3dDatatset/seg_labeled_data_box/labs"
    curr_label = os.path.join(seg_label_path, key + ".bin")
    seg_bin = np.fromfile(curr_label, np.int32).reshape(-1, 2)
    data_dict['Point Cloud'] = data_dict['Point Cloud'].reshape(-1, 4)
    data_dict['Point Cloud'] = np.concatenate((data_dict['Point Cloud'], seg_bin), axis=-1)
    return data_dict