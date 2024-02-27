import os
# try:
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import PySide2 as GuiCoreLib
__GUICOREVERSION__ = "pyside2"
    # print("use pyside2 as gui core")
# except:
#     from PySide2.QtUiTools import QUiLoader
#     from PySide2.QtWidgets import *
#     from PySide2.QtCore import *
#     from PySide2.QtGui import *
#     import PySide2 as GuiCoreLib
#     __GUICOREVERSION__ = "pyside2"
#     # print("use pyside2 as gui core")



import json
import re
from vispy.color import Color
import colorsys
import numpy as np
import pickle
import time
import sys
import Oviz
from enum import Enum

try:
    from matplotlib import path
except ImportError:
    import warnings
    warnings.warn("Lasso example requires matplotlib for more accurate selection. Falling back to numpy based selection.")
    path = None

np.seterr(divide='ignore',invalid='ignore')

GUICOREVERSION = __GUICOREVERSION__
OVIZ_CONFIG_DIR = os.path.join(os.path.dirname(Oviz.__file__), "Config")
OVIZ_HOME_DIR = os.path.join(os.path.expanduser("~"), ".oviz")
USER_CONFIG_DIR = os.path.join(OVIZ_HOME_DIR, "user")
DUMP_HISTORY_DIR = os.path.join(OVIZ_HOME_DIR, "history")
# MAGIC_PIPELINE_DIR = "MagicPipe"
# MAGIC_PIPELINE_SCRIPT = os.path.join(MAGIC_PIPELINE_DIR, "pipeline.py")
MAGIC_USER_PIPELINE_DIR = os.path.join(OVIZ_HOME_DIR, "pipeline")
MAGIC_USER_PIPELINE_SCRIPT = os.path.join(MAGIC_USER_PIPELINE_DIR, "user_pipeline.py")


# sys.path.append(os.path.join(os.getcwd(), MAGIC_PIPELINE_DIR))
sys.path.append(os.path.join(os.getcwd(), MAGIC_USER_PIPELINE_DIR))


POINTCLOUD = "pointcloud"
IMAGE = "image"
BBOX3D = "bbox3d"

ERROR = 0
NORMAL = 1
WARNING = 2

info_color_list = [
    "#ff0000",
    "#00ff00",
]

white = Color("#ecf0f1")
gray = Color("#121212")
red = Color("#e74c3c")
blue = Color("#2980b9")
orange = Color("#e88834")

KEYPRIVATE = "w09f*1l.kl~7tl-t0hmc-eizlsk3jo*+b72wjz*!"

# Regular expression for comments
comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)


class CanvasMouseEvent(Enum):
    NormalMove              = 0
    LeftPressMove           = 1
    RightPressMove          = 2
    LeftPress               = 3
    LeftRelease             = 4
    RightPress              = 5
    RightRelease            = 6
    MiddlePress             = 7
    CtrlLeftPress           = 8
    CtrlMove                = 9
    CtrlLeftPressMove       = 10
    CtrlRelease             = 11
    CtrlRightPress          = 12
    CtrlRightRelease        = 13
    CtrlRightPressMove      = 14


def points_in_polygon(polygon, pts):
    """Get boolean mask of points in a polygon reusing matplotlib implementation.

    The fallback code is based from StackOverflow answer by ``Ta946`` in this question:
    https://stackoverflow.com/questions/36399381/whats-the-fastest-way-of-checking-if-a-point-is-inside-a-polygon-in-python

    This is a proof of concept and depending on your use case, willingness
    to add other dependencies, and your performance needs one of the other answers
    on the above question would serve you better (ex. shapely, etc).
    """
    # Filter vertices out of the polygon's bounding box, this serve as an early optimization whenever number of vertices
    # to filter out is huge.
    x1, x2, y1, y2 = min(polygon[:, 0]), max(polygon[:, 0]), min(polygon[:, 1]), max(polygon[:, 1])
    selection_mask = (x1 < pts[:, 0]) & (pts[:, 0] < x2) & (y1 < pts[:, 1]) & (pts[:, 1] < y2)
    pts_in_bbox = pts[selection_mask]

    # Select vertices inside the polygon.
    if path is not None:
        polygon = path.Path(polygon[:, :2], closed = True)
        polygon_mask = polygon.contains_points(pts_in_bbox[:, :2])
    else:
        contour2 = np.vstack((polygon[1:], polygon[:1]))
        test_diff = contour2-polygon
        m1 = (polygon[:,1] > pts_in_bbox[:,None,1]) != (contour2[:,1] > pts_in_bbox[:,None,1])
        slope = ((pts_in_bbox[:,None,0]-polygon[:,0])*test_diff[:,1])-(test_diff[:,0]*(pts_in_bbox[:,None,1]-polygon[:,1]))
        m2 = slope == 0
        mask2 = (m1 & m2).any(-1)
        m3 = (slope < 0) != (contour2[:,1] < polygon[:,1])
        m4 = m1 & m3
        count = np.count_nonzero(m4, axis=-1)
        mask3 = ~(count%2==0)
        polygon_mask = mask2 | mask3

    # Return the full selection mask based on bounding box & polygon selection.
    selection_mask[np.where(selection_mask == True)] &= polygon_mask

    return selection_mask


def find_files_with_extension(directory, extension = [".jpg", ".png"]):
    file_list = []
    timestamp = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            key, ext = os.path.splitext(file)
            if ext in extension:
                file_list.append(os.path.join(root, file))
                timestamp.append(float(file[:17]))

    return file_list, timestamp


def parse_json(filename):
    # start = time.time()
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    with open(filename, encoding="utf-8") as f:
        content = ''.join(f.readlines())
        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)
        # Return json file
    # print(filename, time.time()-start)
    return json.loads(content)




def check_setting_dims(val, dims):
    if not isinstance(dims, list):
        dims = [dims]
    if len(val) in dims:
        return True
    return False


def write_json(json_data,json_name):
    # Writing JSON data
    with open(json_name, 'w', encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii = False)


def serialize_data(data:dict, file_path):
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)

def deserialize_data(file_path):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    return data


def get_wall_time_str():
    return time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())

def get_mac_address():
    import uuid
    node = uuid.getnode()
    mac = uuid.UUID(int = node).hex[-12:]
    return mac

def choose_file(ui_,info,ename,file_path = "./"):
    selected_file_path, _ = QFileDialog.getOpenFileName(ui_,
                                        info,
                                        file_path,
                                        ename)
    return selected_file_path

def choose_folder(ui_, info, file_path='/'):
    selected_file_path = QFileDialog.getExistingDirectory(ui_,
                                        info,
                                        file_path)
    return selected_file_path


def choose_folder2(parent, title, initial_dir='/'):
    folder_dialog = QFileDialog(parent)
    folder_dialog.setWindowTitle(title)  # 设置标题
    folder_dialog.setFileMode(QFileDialog.Directory)
    folder_dialog.setViewMode(QFileDialog.List)
    folder_dialog.setOption(QFileDialog.ShowDirsOnly, False)
    folder_dialog.setOption(QFileDialog.DontUseNativeDialog, False)
    folder_dialog.setDirectory(initial_dir)

    if folder_dialog.exec_():
        selected_folder = folder_dialog.selectedFiles()
        if selected_folder:
            return selected_folder[0]
    return None

# 将列表递归创建成字典
def creat_dic_from_list(veh,key_value):
    dic = {}
    if veh == []:
        return key_value
    else:
        key = veh[0]
        veh.pop(0)
        dic[key] = creat_dic_from_list(veh,key_value)
    return dic

def unify_theta(theta, base=0):
    if theta + base > 0:
        return (theta + base) % (2*np.pi) - base
    else:
        if (theta + base) % (2*np.pi) != 0:
            return (theta + base) % (2*np.pi) - base
        else:
            return (theta + base) % (2*np.pi) - base + 2*np.pi

#  def cvt_pos_local_to_global(pos_local, pos_base):
    #  theta = pos_base[2]
    #  trans_mat = np.array([[np.sin(theta), np.cos(np.cos(theta))],
                          #  [-np.cos(theta), np.sin(theta)]])
    #  pos_global = trans_mat.dot(pos_local.transpose())
    #  pos_global.transpose()
    #  return pos_global + pos_base[:2]

def cvt_pos_local_to_global(pos_local, pos_base):
    theta = pos_base[2]
    trans_mat = np.array([[np.sin(theta), -np.cos(theta)],
                          [np.cos(theta), np.sin(theta)]])
    pos_global = pos_local.dot(trans_mat)
    return pos_global + pos_base[:2]


def cvt_pos_global_to_local(pos_global, pos_base):

    pos_local = pos_global - pos_base[:2]

    theta = pos_base[2]
    l_x = np.sin(theta) * pos_local[0] - np.cos(theta) * pos_local[1]
    l_y = np.cos(theta) * pos_local[0] + np.sin(theta) * pos_local[1]
    return np.array([l_x, l_y])


def cvt_theta_global_to_local(theta_global, pos_base):
    theta_local = np.pi / 2.0 + theta_global - pos_base[2]
    theta_local = unify_theta(theta_local, 0.0)
    return theta_local

def cvt_theta_local_to_global(theta_local, pos_base):
    theta_global = theta_local + pos_base[2] - np.pi * 0.5
    theta_global = unify_theta(theta_global, 0.0)
    return theta_global

def scale_lightness(rgb, scale_l):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, min(1, l * scale_l), s = s)

def rec_merge(d1, d2):
    for key, value in d2.items():
        if isinstance(value, dict):
            d1[key] = rec_merge(d1.get(key, {}), value)
        else:
            d1[key] = value
    return d1


def rec_exsit_merge(d1, d2):
    for key, value in d2.items():
        if isinstance(d1, dict):
            if (key not in d1.keys()): continue
            d1[key] = rec_exsit_merge(d1.get(key, {}), value)
        else:
            try:
                d1[key] = value
            except:
                pass
    return d1

def rec_merge_map_list(d1, d2):
    for key, value in d2.items():
        if isinstance(value, (list, dict)) and isinstance(d1.get(key), (list, dict)):
            if isinstance(value, dict) and isinstance(d1.get(key), dict):
                d1[key] = rec_merge_map_list(d1.get(key, {}), value)  # 递归合并字典
            elif isinstance(value, list) and isinstance(d1.get(key), list):
                # 合并同索引下的列表
                merged_list = []
                max_len = max(len(d1[key]), len(value))
                for i in range(max_len):
                    if i < len(d1[key]) and i < len(value):
                        merged_list.append(rec_merge_map_list(d1[key][i], value[i]))
                    elif i < len(d1[key]):
                        merged_list.append(d1[key][i])
                    elif i < len(value):
                        merged_list.append(value[i])
                d1[key] = merged_list
        else:
            try:
                d1[key] = value
            except:
                pass
    return d1


def color_str_to_rgb(color_str, alpha = 1.0):
    color_int = int(color_str[1:], 16)
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return np.array([r / 255.0, g / 255.0, b / 255.0, alpha])

def if_not_exist_create(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

if_not_exist_create(USER_CONFIG_DIR)
if_not_exist_create(DUMP_HISTORY_DIR)
if_not_exist_create(MAGIC_USER_PIPELINE_DIR)

magic_pipe_demo_script = \
'''
from Oviz.MagicPipe.core import magic_pipeline_iterate

def test(self, key, data_dict, **kargs):
    print("user_pipeline working")
    return data_dict

@magic_pipeline_iterate(group_keys = [], element_keys=[], switch_key="test")
def decorator_test(self, key, group, ele, index, data, **kwargs):
    return data
'''

if not os.path.exists(MAGIC_USER_PIPELINE_SCRIPT):
    # os.system("echo '%s' > %s"%(magic_pipe_demo_script, MAGIC_USER_PIPELINE_SCRIPT))
    with open(MAGIC_USER_PIPELINE_SCRIPT, 'w') as file:
        file.write(magic_pipe_demo_script)
