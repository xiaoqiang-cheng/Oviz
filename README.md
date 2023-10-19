<div align="center">
  <img src="Resources/homepage.png" width="600"/>
  <div>&nbsp;</div>
  <div align="center">
    <b><font size="6">Xiaoqiang Studio</font></b>
    <sup>
      <a href="https://github.com/xiaoqiang-cheng">
        <i><font size="4">SUB1</font></i>
      </a>
    </sup>
    &nbsp;&nbsp;&nbsp;&nbsp;
    <b><font size="6">Oviz</font></b>
    <sup>
      <a href="https://github.com/xiaoqiang-cheng/Oviz">
        <i><font size="4">TRY IT OUT</font></i>
      </a>
    </sup>
  </div>
  <div>&nbsp;</div>
</div>

---
## 简介
一个正经的可视化工具，Xiaoqiang Studio三件套之一，Do Nothing, Show Anything。

**当前已有**的功能：
- 显示图像（多个相机）
- 显示点云（一个雷达）
- 显示体素（自定义格子）
- 显示一个简单的车体模型
- 录屏

**计划增加**的功能：
- 显示2D/3D 车道线
- 显示2D/3D bounding box
- 显示多传感器之间的标定/投影
- 显示拓扑关系
- 显示曲线
- 显示文字
- 在线模式


## 开发说明

### 依赖
| 建议使用conda管理Python虚拟环境
- Python 3.8+
- pip install -r requirements

### 使用发布环境
1. 下载打包好的oviz_env
2. 安装 ./install.sh
3. 激活虚拟环境 source /usr/local/oviz_env/bin/activate

### 开始
```
python main.py
```


## 使用说明

### 1. 点云可视化
1）修改 point_setting
- dim 点云维度
- xyz维度
- wlh维度 （体素显示用，-1 表示不关心，采用默认格子大小 0.4m）
- color维度 （可以用于显示分割数据）

2）选择点云路径

3）更改对应颜色
- -1表示默认颜色
- 其他数字以点云数据中的ID决定

4）点击voxel模式，以体素显示点云

![选择点云](Resources/show_pointcloud.png)

### 2. 图像可视化
1）点击工具上方 “视图”，选择 显示图片
- 双击任意图片窗体选择路径
- 拖拉窗体到喜欢的位置

2）鼠标选中图片标题栏，右键 任意控制显示/取消显示某一图片窗体

![](Resources/show_image.jpg)

### 3. 录屏
1）显示滑块
- 视图->显示滑块
- 拖出点云设置栏
- 点击保存录屏

2）自动播放数据
- 点击滑块栏中的 auto 自动播放数据
- 播放完成之后，在当前目录下 Output 文件夹下查找录屏图片

### 4. 恢复出厂设置
- rm -r .user


## 最后
如果您觉得本项目有用，不要吝啬您的star~