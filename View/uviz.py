import numpy as np
import math
import yaml
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader as Loader

import vispy.scene
import vispy.app
import trimesh

from vispy import scene
from vispy.scene import visuals
from vispy.color import Color

from vispy.visuals import transforms
from .box_marker import BoxMarkers
from scipy.spatial.transform import Rotation
from Utils.common_utils import *


class Canvas(scene.SceneCanvas):
    """Class that creates and handles a visualizer for a pointcloud"""
    # view相当于是面板，下面可以有好多vis
    # 设计api

    def __init__(self, **kwargs):
        scene.SceneCanvas.__init__(self, keys='interactive')
        self.unfreeze()
        self.grid = self.central_widget.add_grid(spacing=0, bgcolor='black', border_color='k')
        self.view_panel = {}
        self.vis_module = {}
        self.color_map = {}
        self.load_color_map()
        self.curr_col_image_view = 0
        self.label_map = {
                    "0": "car",
                    "1": "car",
                    "2": "truck",
                    "3": "bus",
                    "4": "bicycle",
                    "5": "tricycle",
                    "6": "pedestrian",
                    "7": "barrier",
                    "8": "construction_vehicle",
                    "9": "motorcycle",
                    "10": "traffic_cone",
                    "11": "trailer"
                }

    def create_view(self, view_type, view_name):
        create_method = getattr(self, view_type, None)
        if create_method is None:
            raise RuntimeError('无此类型视图面板')
        else:
            create_method(view_name)

    def creat_vis(self, vis_type, vis_name, parent_view):
        create_method = getattr(self, vis_type, None)
        if create_method is None:
            raise RuntimeError('无此类型视图面板')
        else:
            create_method(vis_name, parent_view)


    def add_3dview(self, view_name = "3d"):
        self.view_panel[view_name] = self.grid.add_view(row=0, col=0, margin=10, border_color=(1, 1, 1))
        self.view_panel[view_name].camera = 'turntable' # arcball
        self.view_panel[view_name].camera.fov = 30
        vispy.scene.visuals.GridLines(color = 'w',parent=self.view_panel[view_name].scene)


    def add_2dview(self, view_name = "2d"):
        self.view_panel[view_name] = self.grid.add_view(row=self.curr_col_image_view, col=0, margin=10,
                                    border_color=(1, 1, 1))
        self.view_panel[view_name].camera = scene.PanZoomCamera(aspect=1)
        self.view_panel[view_name].camera.flip = (0, 1, 0)
        self.view_panel[view_name].camera.set_range() #FIXME: do not work
        self.curr_col_image_view += 1

    def add_image_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = scene.visuals.Image(method = 'auto')
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_axis_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.XYZAxis(parent=self.view_panel[parent_view].scene)

    def add_pointcloud_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Markers(parent=self.view_panel[parent_view].scene)
        self.vis_module[vis_name].set_gl_state('translucent', depth_test=False)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_bbox_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = BoxMarkers(width=0.01, height=0.01, depth=0.01)
        self.vis_module[vis_name].transform = transforms.MatrixTransform()
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_obj_vel_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Arrow(arrow_type='stealth', antialias=True, width=2)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_box_line_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Line(antialias=True)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_text_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Text(font_size=1000, color=(0,1,1))
        self.view_panel[parent_view].add(self.vis_module[vis_name])


    def add_veh_model(self, vis_name, parent_view, stl_path = "config/toyota.stl"):
        car_mesh = trimesh.load(stl_path)
        self.vis_module[vis_name] = visuals.Mesh(vertices=car_mesh.vertices, faces=car_mesh.faces,
                shading='smooth',
                color=self.color_map['car_model'])
        # The size of model from internet is not the actual size of a car
        # and the face direction need adjust
        self.vis_module[vis_name] .transform = transforms.MatrixTransform()
        self.vis_module[vis_name] .transform.scale((0.035, 0.035, 0.035))
        self.vis_module[vis_name] .transform.rotate(-90, (0, 0, 1))
        self.view_panel[parent_view].add(self.vis_module[vis_name] )

    @property
    def visuals(self):
        """List of all 3D visuals on this canvas."""
        return [v for v in self.view.children[0].children if isinstance(v, scene.visuals.VisualNode)]

    def load_color_map(self, color_path = 'Config/color.yml'):
        with open(color_path, 'r') as c:
            color_map = yaml.load(c, Loader=Loader)
        for ke in color_map:
            self.color_map[ke] = Color(color_map[ke])


    def draw_point_cloud(self, vis_name, point_clouds, point_color="#f3f3f3", size = 1):
        face_color = edge_color = Color(point_color)
        self.vis_module[vis_name].set_data(np.array(point_clouds),
                                            edge_color=edge_color,
                                            face_color=face_color,
                                            size=size)
    def draw_image(self, vis_name, img):
        self.vis_module[vis_name].set_data(img)

    def clear_box(self):
        for v in self.visuals:
            if isinstance(v, BoxMarkers):
                v.parent = None

    def draw_velocity(self, vis_name, pos, arrow, width = 4):
        # pos, arrow = self.create_box_vel_arrow(boxes)
        self.vis_module[vis_name].set_data(pos, connect='segments', arrows=arrow, width=width)

    def draw_box_line(self, vis_name, boxes, box_line_lightness_scale=1.2,
                                                box_line_width=2):
        pos, width, length, height, theta = self.prepare_box_data(boxes)
        fc, _ = self.prepare_box_color(boxes,
                lightness_ratio = box_line_lightness_scale)
        fc = np.tile(fc, 8).reshape(-1, 4)
        vertex_point, p_idx = self.create_box_vertex(pos,
                width, length, height, theta)
        self.vis_module[vis_name].set_data(pos=vertex_point, connect=p_idx,
                color=fc, width=box_line_width)

    def draw_box_surface(self, vis_name, boxes, box_surface_opacity = 0.8):
        pos, width, length, height, theta = self.prepare_box_data(boxes)
        fc, ec = self.prepare_box_color(boxes,
                opacity = box_surface_opacity)
        self.vis_module[vis_name].set_data(pos, width=width, height=length, depth=height,
            face_color=fc, edge_color=ec, rotation=theta)

    def draw_id_vel(self, vis_name, box, show_id = 1, show_vel = 0):
        if show_id:
            text, pos, color = self.prepare_box_id_vel(box, show_vel)
            self.draw_text(vis_name, text, pos, color)

    def draw_text(self, vis_name, text, text_pos, text_color):
        self.vis_module[vis_name].text = text
        self.vis_module[vis_name].pos = text_pos
        self.vis_module[vis_name].color = text_color

    def prepare_box_id_vel(self, boxes, draw_box_vel = 0):
        show_text = []
        show_text_pos = []
        show_text_color = []
        for b in boxes:
            if draw_box_vel:
                curr_text =  " [" + str(int(b.id)) + "] " + "v:" + "%.2f"%b.vel + " km/h"
            else:
                curr_text =  " [" + str(int(b.id)) + "]"
            show_text.append(curr_text)
            show_text_pos.append((b.x, b.y, b.z + 1.5))
            rgba = self.color_map[self.label_map[b.kind]].rgba
            show_text_color.append(rgba)
        return show_text, show_text_pos, show_text_color

    def prepare_box_color(self, boxes, lightness_ratio=1.0, opacity=1.0):
        fc = []
        for b in boxes:
            rgba = self.color_map[self.label_map[b.kind]].rgba
            if lightness_ratio != 1.0:
                rgba[:3] = scale_lightness(rgba[:3], lightness_ratio)
            fc.append(rgba)
        fc = np.array(fc)
        ec = np.copy(fc)
        fc[..., 3] = opacity
        return fc, ec

    def prepare_box_data(self, boxes, enlarge_ratio=1.0):
        pos = []
        width = []
        height = []
        depth = []
        theta = []
        for b in boxes:
            pos.append([b.x, b.y, b.z])
            width.append([b.width])
            height.append([b.length])
            depth.append([b.height])
            theta.append([b.dir])

        pos = np.array(pos)
        # enlarge box a little bit
        width = np.array(width) * enlarge_ratio
        height = np.array(height) * enlarge_ratio
        depth = np.array(depth) * enlarge_ratio
        theta = np.array(theta)
        return pos, width, height, depth, theta

    def prepare_box_color(self, boxes, lightness_ratio=1.0, opacity=1.0):
        fc = []
        for b in boxes:
            rgba = self.color_map[self.label_map[str(int(b.kind))]].rgba
            if lightness_ratio != 1.0:
                rgba[:3] = scale_lightness(rgba[:3], lightness_ratio)
            fc.append(rgba)
        fc = np.array(fc)
        ec = np.copy(fc)
        fc[..., 3] = opacity
        return fc, ec


    def create_box_vertex(self, pos, width, length, height,
            rotation):

        rotation_mat = []
        for theta in rotation:
            rotation_mat.append(Rotation.from_euler('xyz', [0., 0., theta]).as_matrix())

        box_vertex = np.array([[-0.5, -0.5, -0.5],
                                [-0.5, -0.5, 0.5],
                                [0.5, -0.5, -0.5],
                                [0.5, -0.5, 0.5],
                                [0.5, 0.5, -0.5],
                                [0.5, 0.5, 0.5],
                                [-0.5, 0.5, -0.5],
                                [-0.5, 0.5, 0.5]])
        nb_v = box_vertex.shape[0]

        scale = np.hstack((width, length, height))

        vertices = np.zeros((nb_v * pos.shape[0], 3))
        p_idx = []
        for i in range(pos.shape[0]):
            idx_v_start  = nb_v*i
            idx_v_end    = nb_v*(i+1)

            vertices[idx_v_start:idx_v_end] = box_vertex*scale[i]
            vertices[idx_v_start:idx_v_end] = \
                np.dot(vertices[idx_v_start:idx_v_end], rotation_mat[i])
            vertices[idx_v_start:idx_v_end] += pos[i]

            for j in range(nb_v):
                p_idx.append((j + idx_v_start, (2 + j) % nb_v + idx_v_start))
            for j in range(int(nb_v / 2)):
                p_idx.append((2 * j + idx_v_start, 2 *j + 1 + idx_v_start))
        return vertices, np.array(p_idx)

    def create_box_vel_arrow(self, boxes):
        pos = []
        arrow = []
        for i, b in enumerate(boxes):
            theta = np.pi * 0.5 - b.dir
            vel = b.vel * 0.5
            x = b.x + vel * math.cos(theta)
            y = b.y + vel * math.sin(theta)
            pos.append([b.x, b.y, b.z])
            pos.append([x, y, b.z])
            arrow.append([b.x, b.y, b.z, x, y, b.z])

        pos = np.array(pos)
        arrow = np.array(arrow)
        return pos, arrow

    def destroy(self):
        # destroy the visualization
        self.close()
        vispy.app.quit()

    def run(self):
        vispy.app.run()
