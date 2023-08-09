import sys
import numpy as np

from vispy import app, scene

canvas = scene.SceneCanvas(size=(800, 600), keys='interactive')

N = 1000
pos = np.empty((N, 3), np.float32)
pos[:, 0] = np.linspace(50., 750., N)
#
color = np.ones((N, 4), dtype=np.float32)
color[:, 0] = np.linspace(0, 1, N)
color[:, 1] = color[::-1, 0]

lines = []

print('Generating points...')
for i in range(20):
    pos = pos.copy()
    pos[:, 1] = np.random.normal(scale=5, loc=(i+1)*30, size=N)
    line = scene.visuals.Line(pos=pos, color=color, parent=canvas.scene)
    lines.append(line)
    line.transform = scene.transforms.STTransform()

import ipdb
ipdb.set_trace()
print('Done')


# def update(event):
#     for line in lines:
#         scale = [np.sin(np.pi * event.elapsed)+2,
#                  np.cos(np.pi * event.elapsed)+2]
#         line.transform.scale = scale

# timer = app.Timer('auto', connect=update, start=True)

if __name__ == '__main__':
    canvas.show()
    if sys.flags.interactive == 0:
        app.run()