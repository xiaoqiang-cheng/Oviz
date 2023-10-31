import numpy as np
import math

import vispy.scene
import vispy.app

from vispy import scene
from vispy.scene import visuals
from vispy.color import Color

from vispy.visuals import transforms
from .box_marker import BoxMarkers
from scipy.spatial.transform import Rotation
from Oviz.Utils.common_utils import *

from vispy.io import imread, load_data_file, read_mesh
from vispy.scene.visuals import Mesh
from vispy.visuals.filters import TextureFilter

VIEW3D_COL_MAX_NUM = 3

class Canvas(scene.SceneCanvas):
    """Class that creates and handles a visualizer for a pointcloud"""
    # view相当于是面板，下面可以有好多vis
    # 设计api

    capturerKey = Signal(str)

    def __init__(self, background=(1,1,1,1)):
        scene.SceneCanvas.__init__(self, keys='interactive')
        self.unfreeze()
        self.grid = self.central_widget.add_grid(spacing=1, bgcolor=background, border_color='w')
        # Bind the escape key to a custom function
        # vispy.app.use_app().bind_key("Escape", self.on_escape)
        self.view_panel = {}
        self.vis_module = {}
        self.curr_col_image_view = 0
        self.curr_col_3d_view = 0

    def create_view(self, view_type, view_name, camera = None):
        create_method = getattr(self, view_type, None)
        if create_method is None:
            raise RuntimeError('无此类型视图面板')
        else:
            create_method(view_name, camera)

    def creat_vis(self, vis_type, vis_name, parent_view, params = {}):
        create_method = getattr(self, vis_type, None)
        if create_method is None:
            raise RuntimeError('无此类型视图面板')
        else:
            create_method(vis_name, parent_view, **params)

    def pop_view(self, view_name):
        self.curr_col_3d_view -= 1
        self.grid.remove_widget(self.view_panel[view_name])
        self.view_panel[view_name].parent = None
        for key in list(self.vis_module.keys())[:]:
            if view_name in key:
                self.vis_module[key].parent = None
                self.vis_module.pop(key)
        self.view_panel.pop(view_name)

    def add_3dview(self, view_name = "3d", camera = None):
        row_idx = int(self.curr_col_3d_view / VIEW3D_COL_MAX_NUM)
        col_idx = int(self.curr_col_3d_view % VIEW3D_COL_MAX_NUM)
        self.view_panel[view_name] = self.grid.add_view(row=row_idx,
                                    col=col_idx,
                                    border_color=(69/255.0, 83/255.0, 100/255.0))
        self.curr_col_3d_view += 1
        # self.view_panel[view_name].camera = 'turntable' # arcball
        # self.view_panel[view_name].camera.fov = 30
        # print(self.view_panel[view_name].camera.__dict__)

        # fov: float = 45.0,
        # elevation: float = 30.0,
        # azimuth: float = 30.0,
        # roll: float = 0.0,
        # distance: None | float = None,
        # translate_speed: float = 1.0,
        if camera is None:
            self.view_panel[view_name].camera  = scene.TurntableCamera()
        else:
            self.view_panel[view_name].camera  = scene.TurntableCamera(
                    **camera,
                )

    def get_canvas_camera(self, view_name):
        return {
            "fov": self.view_panel[view_name].camera._fov,
            "elevation": self.view_panel[view_name].camera._elevation,
            "azimuth" : self.view_panel[view_name].camera._azimuth,
            "roll" : self.view_panel[view_name].camera._roll,
            "distance": self.view_panel[view_name].camera._distance,
            "scale_factor": self.view_panel[view_name].camera._scale_factor
        }

    def print_3dview_camera_params(self, view_name = "template"):
        print("=================3D view Camera Params:============")
        print("fov: ", self.view_panel[view_name].camera._fov)
        print("elevation: ", self.view_panel[view_name].camera._elevation)
        print("azimuth:", self.view_panel[view_name].camera._azimuth)
        print("roll:", self.view_panel[view_name].camera._roll)
        print("distance:", self.view_panel[view_name].camera._distance)
        print("scale_factor", self.view_panel[view_name].camera._scale_factor)
        print("=======================ending=====================\n")

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
        # Simple 3D axis for indicating coordinate system orientation. Axes are
        # x=red, y=green, z=blue.
        self.vis_module[vis_name] = visuals.XYZAxis(parent=self.view_panel[parent_view].scene, width = 5)

    def add_reference_grid_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Markers(parent=self.view_panel[parent_view].scene)
        # self.vis_module[vis_name].set_gl_state('translucent', depth_test=False)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_pointcloud_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Markers(parent=self.view_panel[parent_view].scene,
                            light_color='black', light_position=(0, 0, 0), light_ambient=0.3,)
        self.vis_module[vis_name].set_gl_state(**{'blend': False, 'cull_face': False, 'depth_test': True})
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_bbox_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = BoxMarkers(width=0.01, height=0.01, depth=0.01)
        self.vis_module[vis_name].transform = transforms.MatrixTransform()
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_pointvoxel_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = BoxMarkers(width=0.01, height=0.01, depth=0.01)
        self.vis_module[vis_name].transform = transforms.MatrixTransform()
        self.view_panel[parent_view].add(self.vis_module[vis_name])

        # transform = self.view_panel[parent_view].camera.transform
        # dir = np.array([-10, -10, -10, 0])
        # print(self.vis_module[vis_name]._mesh.shading_filter.__dict__)
        # self.vis_module[vis_name]._mesh.shading_filter.light_dir = transform.map(dir)[:3]
        # self.vis_module[vis_name]._mesh.shading_filter.shininess = 250
        # self.vis_module[vis_name]._mesh.shading_filter.specular_coefficient = 0.3
        # print(self.vis_module[vis_name]._mesh.shading_filter.__dict__)

    def add_referenceline_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Line(antialias=True)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_voxelline_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Line(antialias=True)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_arrow_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Arrow(arrow_type='stealth', antialias=True, width=2)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_box_line_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Line(antialias=True)
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_text_vis(self, vis_name, parent_view):
        self.vis_module[vis_name] = visuals.Text(font_size=600, color=(0,1,1))
        self.view_panel[parent_view].add(self.vis_module[vis_name])

    def add_veh_model(self, vis_name, parent_view,
                        obj_path=os.path.join(OVIZ_CONFIG_DIR, "colorful_car/car.obj"),
                        texture_path='00008.BMP'
                    ):
        texture_path = os.path.join(OVIZ_CONFIG_DIR, 'colorful_car', texture_path)
        mesh_path = load_data_file(obj_path, directory=".")
        texture_path = load_data_file(texture_path,  directory=".")
        vertices, faces, normals, texcoords = read_mesh(mesh_path)
        texture = np.flipud(imread(texture_path))

        mesh = Mesh(vertices, faces, shading="smooth", color=(1, 1, 1, 1))
        mesh.transform = transforms.MatrixTransform()

        mesh.transform.rotate(90, (1, 0, 0))
        # mesh.transform.rotate(-90, (0, 0, 1))
        mesh.transform.scale((1.3, 1.3, 1.3))
        mesh.transform.translate((0.5, 0., 1.0))
        texture_filter = TextureFilter(texture, texcoords)

        self.vis_module[vis_name] = mesh
        self.view_panel[parent_view].add(self.vis_module[vis_name])
        self.vis_module[vis_name].attach(texture_filter)
        # for a default initialised camera
        self.initial_light_dir = self.view_panel[parent_view].camera.transform.imap((0, 0, 1) )[:3]
        self.set_visible(vis_name, False)

    def set_pointcloud_glstate(self):
        for key in self.view_panel.keys():
            self.vis_module[key + "_" + "point_cloud"].set_gl_state(**{'blend': False, 'cull_face': False, 'depth_test': True})

    def on_mouse_move(self, event):
        for key in self.view_panel.keys():
            mesh = self.vis_module[key + "_" + 'car_model']
            transform = self.view_panel[key].camera.transform
            dir = np.concatenate((self.initial_light_dir, [0]))
            mesh.shading_filter.light_dir = transform.map(dir)[:3]

    def on_mouse_wheel(self, event):
        self.set_pointcloud_glstate()

    def on_mouse_press(self, event):
        self.set_pointcloud_glstate()

    def set_vis_bgcolor(self, value = (0, 0, 0, 1)):
        self.grid.bgcolor = value


    def draw_point_cloud(self, vis_name, point_clouds, point_color="#f3f3f3", size = 1):
        # face_color = edge_color = Color(point_color)
        self.vis_module[vis_name].set_data(np.array(point_clouds),
                                            # edge_width=5,
                                            edge_color=point_color,
                                            face_color=point_color,
                                            size=size,
                                            symbol = 'o')
        self.vis_module[vis_name].set_gl_state(**{'blend': False, 'cull_face': False, 'depth_test': True})


    def draw_point_voxel(self, vis_name, pos, w, l, h, face, edge):
        self.vis_module[vis_name].set_voxel_data(pos, width=w, height=l, depth=h, face_color=face)

    def draw_reference_line(self, vis_name, x_range = [-100, 100], y_range = [-100, 100], x_step = 10, y_step = 10,
                                color = (0.5, 0.5, 0.5, 0.9), ref_type = 0, box_line_width = 1):
        '''
            x_range, y_range, z_range (TODO): like [min, max] /m,
            step:
                if ref_type == 0: x_step y_step is m
                if ref_type == 1: x_step is m, y_step is angle
            color defaulte gray
            ref_type :
                0 Decare;
                1 Polar
        '''
        if ref_type == 0:
            idx = []
            all_pos = []
            index = 0
            for i in np.arange(x_range[0], x_range[1] + 1, step=x_step):
                pos = np.empty((2, 3), np.float32)
                pos[:, 0] = y_range
                pos[:, 1] = [i, i]
                pos[:, 2] = [0, 0]
                all_pos.append(pos)
                idx.append([index, index + 1])
                index += 2

            for i in np.arange(y_range[0], y_range[1] + 1, step=y_step):
                pos = np.empty((2, 3), np.float32)
                pos[:, 0] = [i, i]
                pos[:, 1] = x_range
                pos[:, 2] = [0, 0]
                all_pos.append(pos)
                idx.append([index, index + 1])
                index += 2
            all_pos = np.array(all_pos).reshape(-1, 3)
            idx = np.array(idx)
            self.vis_module[vis_name].set_data(pos=all_pos, connect = idx, color=color, width=box_line_width)
        else:
            pass


    def draw_voxel_line(self, vis_name, pos, w, l, h, box_line_width=0.8):
        vertex_point, p_idx = self.create_voxel_vertex(pos, w, l, h)
        self.vis_module[vis_name].set_data(pos=vertex_point, connect=p_idx,
                    color=(0,0,0,0.1), width=box_line_width)

    def draw_image(self, vis_name, img):
        self.vis_module[vis_name].set_data(img)

    def set_visible(self, vis_name, status):
        self.vis_module[vis_name].visible = status

    def draw_arrow(self, vis_name, pos, arrow, color, width):
        self.vis_module[vis_name].set_data(pos, connect='segments', arrows=arrow, width=width)

    def draw_bbox3d_arrow(self, vis_name, bboxes, vel_list, color, width = 3):
        pos, arrow = self.create_box_arrow(bboxes, vel_list)
        self.draw_arrow(vis_name, pos, arrow, color, width)

    def draw_box3d_line(self, vis_name, boxes, color, box_line_width=4):
        pos, width, length, height, theta = self.prepare_box_data(boxes)
        vertex_point, p_idx = self.create_box_vertex(pos,
                width, length, height, theta)
        color = np.tile(color, 8).reshape(-1, 4)
        self.vis_module[vis_name].set_data(pos=vertex_point, connect=p_idx,
                    color=color, width=box_line_width)

    def draw_box_surface(self, vis_name, boxes, color, box_surface_opacity = 0.5):
        pos, width, length, height, theta = self.prepare_box_data(boxes)
        color[:, -1] *= box_surface_opacity
        self.vis_module[vis_name].set_data(pos, width=width, height=length, depth=height,
            face_color=color, edge_color=color, rotation=theta)

    def draw_text(self, vis_name, text, text_pos, text_color):
        self.vis_module[vis_name].text = text
        self.vis_module[vis_name].pos = text_pos
        self.vis_module[vis_name].color = text_color

    def prepare_box_data(self, boxes, enlarge_ratio=1.0):
        pos = []

        pos = boxes[:, 0:3]
        # enlarge box a little bit
        width = boxes[:, 3].reshape(-1, 1) * enlarge_ratio
        depth = boxes[:, 4].reshape(-1, 1)  * enlarge_ratio
        height = boxes[:, 5].reshape(-1, 1)  * enlarge_ratio
        theta = boxes[:, 6]
        return pos, width, depth, height, theta

    def create_voxel_vertex(self, pos, width, length, height):
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
        vertices = box_vertex.reshape(1, nb_v, 3) * scale.reshape(-1, 1, 3) + pos.reshape(-1, 1, 3)

        vertices = vertices.reshape(-1, 3)
        module_list = [(0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 0), (7, 1), (0, 1), (2, 3), (4, 5), (6, 7)]
        pt_idx = np.array((pos.shape[0] * module_list), dtype=np.int64)

        arr_mask = np.repeat(np.arange(pos.shape[0]), 12).reshape(-1) * 8
        pt_idx += arr_mask.reshape(-1, 1)
        return vertices, pt_idx

    def create_box_vertex(self, pos, width, length, height,rotation):

        rotation_mat = []
        for theta in rotation:
            rotation_mat.append(Rotation.from_euler('xyz', [0., 0, theta]).as_matrix())

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

    def create_box_arrow(self, boxes, vel_list):
        pos = []
        arrow = []
        for i, vel in enumerate(vel_list):
            b = boxes[i]
            if len(vel) == 1:
                theta = np.pi * 0.5 - b[-1]
                x = b[0] + vel[0] * math.cos(theta)
                y = b[1] + vel[0] * math.sin(theta)
            else:
                x, y = vel[0], vel[1]

            pos.append(b[0:3])
            pos.append([x, y, b[2]])
            arrow.append([b[0],b[1], b[2], x, y, b[2]])

        pos = np.array(pos)
        arrow = np.array(arrow)
        return pos, arrow

    def destroy(self):
        # destroy the visualization
        self.close()
        vispy.app.quit()

    def run(self):
        vispy.app.run()
