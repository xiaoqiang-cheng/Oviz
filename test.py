import numpy as np
from vispy.scene import visuals
from vispy import app, scene

# 生成随机点云数据
pos = np.random.normal(size=(100000, 3), scale=5)
color = np.random.uniform(size=(100000, 3), low=0.0, high=1.0)

# 创建一个视图窗口
canvas = scene.SceneCanvas(keys='interactive')
view = canvas.central_widget.add_view()

# 创建一个Mark对象并设置数据和颜色
mark = visuals.Markers()
import ipdb
ipdb.set_trace()
mark.set_data(pos=pos, face_color=color, size=10)

# 将Mark对象添加到视图中并显示
view.add(mark)
canvas.show()
app.run()
