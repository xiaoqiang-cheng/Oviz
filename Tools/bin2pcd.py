import sys
sys.path.append(".")
import numpy as np
from Utils.pypcd import PointCloud
from Utils.point_cloud_utils import read_bin, write_pcd
import os

bin_root_dir = "/home/uisee/Downloads/qviz_data"
pcd_root_dir = "/home/uisee/Downloads/qviz_data"

name_list = os.listdir(bin_root_dir)

for n in name_list:
    if not n.endswith(".bin"): continue
    pcd_name = n.replace("bin", "pcd")
    bin_name = os.path.join(bin_root_dir, n)
    outfile = os.path.join(pcd_root_dir, pcd_name)
    bin = read_bin(bin_name, dim=4)
    write_pcd(outfile, bin)

    print(bin_name, "->", pcd_name)

