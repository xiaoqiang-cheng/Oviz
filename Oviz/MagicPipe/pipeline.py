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
    for group, subdata in data_dict.items():
        if 'pointcloud' in subdata.keys():
            for i, single_pc in enumerate(subdata['pointcloud']):
                if len(single_pc.shape) == 1:
                    single_pc = np.frombuffer(single_pc.data,
                            dtype = np.dtype(self.pointcloud_setting_dict[group][i].points_type)).reshape(-1,
                                        self.pointcloud_setting_dict[group][i].points_dim)
                    subdata['pointcloud'][i] = single_pc
    return data_dict

def append_seg_dim_for_pcd(self, key, data_dict, **kargs):
    '''
        apend seg to pcd, need supply params:
        {
            "seg_path" : "",
            "seg_dim" : 1 (yourself)
        }
    '''
    for group, subdata in data_dict.items():
        if "pointcloud" in subdata.keys() and 'seg_path' in kargs.keys():
            seg_path =  os.path.join(kargs['seg_path'], key + ".bin")
            if os.path.exists(seg_path):
                seg_bin = np.fromfile(seg_path, dtype=np.int32).reshape(-1, kargs['seg_dim']).astype(np.float32)
                for i, single_pc in enumerate(subdata['pointcloud']):
                    single_pc = np.concatenate((single_pc, seg_bin), axis=1)
                    subdata['pointcloud'][i] = single_pc
    return data_dict

def append_ins_dim_for_pcd(self, key, data_dict, **kargs):
    '''
        apend seg to pcd, need supply params:
        {
            "ins_path" : "",
            "ins_dim" : 1 (yourself)
        }
    '''
    for group, subdata in data_dict.items():
        if "pointcloud" in subdata.keys() and 'ins_path' in kargs.keys():
            ins_path =  os.path.join(kargs['ins_path'], key + ".bin")

            if os.path.exists(ins_path):
                ins_bin = np.fromfile(ins_path, dtype=np.int32).reshape(-1, kargs['ins_dim']).astype(np.float32)
                for i, single_pc in enumerate(subdata['pointcloud']):
                    single_pc = np.concatenate((single_pc, ins_bin), axis=1)
                    subdata['pointcloud'][i] = single_pc

    return data_dict

def vel2rgb_flow_for_pcd(self, key, data_dict, **kargs):

    if 'vel2rgb_flag' not in kargs.keys():
        return data_dict

    def flow_uv_to_colors(u, v, convert_to_bgr=False):

        def make_colorwheel():
            """
            Generates a color wheel for optical flow visualization as presented in:
                Baker et al. "A Database and Evaluation Methodology for Optical Flow" (ICCV, 2007)
                URL: http://vision.middlebury.edu/flow/flowEval-iccv07.pdf

            Code follows the original C++ source code of Daniel Scharstein.
            Code follows the the Matlab source code of Deqing Sun.

            Returns:
                np.ndarray: Color wheel
            """

            RY = 15
            YG = 6
            GC = 4
            CB = 11
            BM = 13
            MR = 6

            ncols = RY + YG + GC + CB + BM + MR
            colorwheel = np.zeros((ncols, 3))
            col = 0

            # RY
            colorwheel[0:RY, 0] = 255
            colorwheel[0:RY, 1] = np.floor(255*np.arange(0,RY)/RY)
            col = col+RY
            # YG
            colorwheel[col:col+YG, 0] = 255 - np.floor(255*np.arange(0,YG)/YG)
            colorwheel[col:col+YG, 1] = 255
            col = col+YG
            # GC
            colorwheel[col:col+GC, 1] = 255
            colorwheel[col:col+GC, 2] = np.floor(255*np.arange(0,GC)/GC)
            col = col+GC
            # CB
            colorwheel[col:col+CB, 1] = 255 - np.floor(255*np.arange(CB)/CB)
            colorwheel[col:col+CB, 2] = 255
            col = col+CB
            # BM
            colorwheel[col:col+BM, 2] = 255
            colorwheel[col:col+BM, 0] = np.floor(255*np.arange(0,BM)/BM)
            col = col+BM
            # MR
            colorwheel[col:col+MR, 2] = 255 - np.floor(255*np.arange(MR)/MR)
            colorwheel[col:col+MR, 0] = 255
            return colorwheel


        """
        Applies the flow color wheel to (possibly clipped) flow components u and v.

        According to the C++ source code of Daniel Scharstein
        According to the Matlab source code of Deqing Sun

        Args:
            u (np.ndarray): Input horizontal flow of shape [H,W]
            v (np.ndarray): Input vertical flow of shape [H,W]
            convert_to_bgr (bool, optional): Convert output image to BGR. Defaults to False.

        Returns:
            np.ndarray: Flow visualization image of shape [H,W,3]
        """
        flow_image = np.zeros((u.shape[0], u.shape[1], 3), np.uint8)
        colorwheel = make_colorwheel()  # shape [55x3]
        ncols = colorwheel.shape[0]
        rad = np.sqrt(np.square(u) + np.square(v))
        a = np.arctan2(-v, -u)/np.pi
        fk = (a+1) / 2*(ncols-1)
        k0 = np.floor(fk).astype(np.int32)
        k1 = k0 + 1
        k1[k1 == ncols] = 0
        f = fk - k0
        for i in range(colorwheel.shape[1]):
            tmp = colorwheel[:,i]
            col0 = tmp[k0] / 255.0
            col1 = tmp[k1] / 255.0
            col = (1-f)*col0 + f*col1
            idx = (rad <= 1)
            col[idx]  = 1 - rad[idx] * (1-col[idx])
            col[~idx] = col[~idx] * 0.75   # out of range
            # Note the 2-i => BGR instead of RGB
            ch_idx = 2-i if convert_to_bgr else i
            flow_image[:,:,ch_idx] = np.floor(255 * col)
        return flow_image

    for group, subdatase in data_dict.items():
        for i, single_pc in enumerate(subdatase['pointcloud']):
            pts = single_pc.reshape(-1, 6)
            pts_vel = pts[:, -2:]

            max_norm = np.linalg.norm(pts_vel, axis=-1).max()
            pts_vel = pts_vel / (max_norm + 1e-5)
            pts_vel = pts_vel[np.newaxis, ...]
            color = flow_uv_to_colors(pts_vel[..., 0], pts_vel[..., 1])
            color = color[0] / 255.

            # set background
            mask = color.sum(-1) == 3.0
            color[mask] = color[mask] * 0.5

            pts = np.concatenate((pts[:, :4], color), axis=-1)

            subdatase['pointcloud'][i] = pts
    return data_dict