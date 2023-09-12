'''
note:
    1, if you need to add a new pipeline to repo, please add swith for it
    2, do not push you temporary pipe to repo
    3, add params instructions for your pipeline to easily apply
    4, all pipeline will be executed in sequence, so switch is very very important
    5, do not remember return data_dict
'''

import os
import numpy as np

def magic_debug(self, key, data_dict, **kargs):
    '''
        print kargs when use magic pipeline
        {
            "magic_debug" : 1
        }
    '''
    if ("magic_debug" in kargs.keys()) and (kargs['magic_debug'] == 1):
        print(kargs)
    return data_dict

def point_cloud_reshape(self, key, data_dict, **kargs):
    if 'Point Cloud' in data_dict.keys():
        data_dict['Point Cloud'] = np.frombuffer(data_dict['Point Cloud'].data,
                dtype = np.dtype(self.points_setting.points_type)).reshape(-1, self.points_setting.points_dim)
    return data_dict

def append_seg_dim_for_pcd(self, key, data_dict, **kargs):
    '''
        apend seg to pcd, need supply params:
        {
            "seg_path" : "",
            "seg_dim" : 1 (yourself)
        }
    '''
    if "Point Cloud" in data_dict.keys() and 'seg_path' in kargs.keys():
        length = len(data_dict['Point Cloud'])
        seg_path =  os.path.join(kargs['seg_path'], key + ".bin")
        if os.path.exists(seg_path):
            seg_bin = np.fromfile(seg_path, dtype=np.int32).reshape(-1, kargs['seg_dim']).astype(np.float32)
        else:
            seg_bin = np.array([-1] * length).reshape(length, kargs['seg_dim']).astype(np.float32)
        data_dict['Point Cloud'] = np.concatenate((data_dict['Point Cloud'], seg_bin), axis=1)
    return data_dict

def append_ins_dim_for_pcd(self, key, data_dict, **kargs):
    '''
        apend seg to pcd, need supply params:
        {
            "ins_path" : "",
            "ins_dim" : 1 (yourself)
        }
    '''
    if "Point Cloud" in data_dict.keys() and 'ins_path' in kargs.keys():
        ins_path =  os.path.join(kargs['ins_path'], key + ".bin")

        length = len(data_dict['Point Cloud'])
        if os.path.exists(ins_path):
            ins_bin = np.fromfile(ins_path, dtype=np.int32).reshape(-1, kargs['ins_dim']).astype(np.float32)
        else:
            ins_bin = np.array([-1] * length).reshape(length, kargs['ins_dim']).astype(np.float32)
        data_dict['Point Cloud'] = np.concatenate((data_dict['Point Cloud'], ins_bin), axis=1)
    return data_dict

