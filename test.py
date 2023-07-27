import argparse

import numpy as np
from vispy import app, scene
from vispy.io import imread, load_data_file, read_mesh
from vispy.scene.visuals import Mesh
from vispy.scene import transforms
from vispy.visuals.filters import TextureFilter


parser = argparse.ArgumentParser()
parser.add_argument('--shading', default='flat',
                    choices=['none', 'flat', 'smooth'],
                    help="shading mode")
args, _ = parser.parse_known_args()


canvas = scene.SceneCanvas(keys='interactive', bgcolor='white',
                           size=(800, 600))
view = canvas.central_widget.add_view()

view.camera = 'arcball'
# Adapt the depth to the scale of the mesh to avoid rendering artefacts.
# view.camera.depth_value = 10 * (vertices.max() - vertices.min())

mesh_path = load_data_file("Config/colorful_car/car.obj", directory=".")
texture_path = load_data_file('Config/colorful_car/00008.BMP',  directory=".")
vertices, faces, normals, texcoords = read_mesh(mesh_path)
texture = np.flipud(imread(texture_path))

mesh = Mesh(vertices, faces, shading="smooth", color=(1, 1, 1, 0.9))
mesh.transform = transforms.MatrixTransform()
mesh.transform.rotate(90, (1, 0, 0))
# mesh.transform.rotate(135, (0, 0, 1))
mesh.shading_filter.shininess = 1e+1
view.add(mesh)

texture_filter = TextureFilter(texture, texcoords)
mesh.attach(texture_filter)


# @canvas.events.key_press.connect
# def on_key_press(event):
#     if event.key == "t":
#         texture_filter.enabled = not texture_filter.enabled
#         mesh.update()


def attach_headlight(mesh, view, canvas):
    light_dir = (0, 1, 0, 0)
    mesh.shading_filter.light_dir = light_dir[:3]
    initial_light_dir = view.camera.transform.imap(light_dir)

    @view.scene.transform.changed.connect
    def on_transform_change(event):
        transform = view.camera.transform
        mesh.shading_filter.light_dir = transform.map(initial_light_dir)[:3]


attach_headlight(mesh, view, canvas)


canvas.show()


if __name__ == "__main__":
    app.run()