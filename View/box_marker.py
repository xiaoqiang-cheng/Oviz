import numpy as np
from vispy.geometry import create_box
from vispy.visuals.mesh import MeshVisual
from vispy.visuals.visual import CompoundVisual
from vispy.scene.visuals import create_visual_node
from scipy.spatial.transform import Rotation

class BoxMarkersVisual(CompoundVisual):
    """Visual that displays a box.

    Parameters
    ----------
    point_coords : array_like
        Marker coordinates
    width : float
        Box width.
    height : float
        Box height.
    depth : float
        Box depth.
    width_segments : int
        Box segments count along the width.
    height_segments : float
        Box segments count along the height.
    depth_segments : float
        Box segments count along the depth.
    planes: array_like
        Any combination of ``{'-x', '+x', '-y', '+y', '-z', '+z'}``
        Included planes in the box construction.
    vertex_colors : ndarray
        Same as for `MeshVisual` class. See `create_plane` for vertex ordering.
    face_colors : ndarray
        Same as for `MeshVisual` class. See `create_plane` for vertex ordering.
    color : Color
        The `Color` to use when drawing the cube faces.
    edge_color : tuple or Color
        The `Color` to use when drawing the cube edges. If `None`, then no
        cube edges are drawn.
    """

    def __init__(self, point_coords=np.array([0,0,0]), width=1, height=1, depth=1, width_segments=1,
                 height_segments=1, depth_segments=1, rotation=None, planes=None,
                 vertex_colors=None, face_color=None,
                 #  color=(0.5, 0.5, 1, 1), edge_color=None, **kwargs):
                 color=None, edge_color=None, **kwargs):

        self.point_coords = point_coords
        self.nb_points = point_coords.shape[0]
        self.width = width
        self.height = height
        self.depth =depth
        self.color = color
        self.edge_color = edge_color
        self.face_color = face_color
        self.rotation =rotation

        self.edge_colors = None
        self.face_colors = None
        self.rotation_mat = None

        if self.face_color is not None:
            self.set_face_colors()
        if self.rotation is not None:
            self.set_rotation_mat()

        # Create a unit box
        width_box  = 1
        height_box = 1
        depth_box  = 1

        #  scale = np.array([width/width_box, height/height_box, depth/depth_box])
        scale = np.hstack((self.width, self.height, self.depth))
        #  print('scale:', scale)

        self.vertices_box, self.filled_indices_box, self.outline_indices_box = create_box(
                width_box, height_box, depth_box, width_segments, height_segments,
                depth_segments, planes)

        # Store number of vertices, filled_indices and outline_indices per box
        self.nb_v  = self.vertices_box.shape[0]
        self.nb_fi = self.filled_indices_box.shape[0]
        self.nb_oi = self.outline_indices_box.shape[0]

        # Create empty arrays for vertices, filled_indices and outline_indices
        vertices = np.zeros(self.nb_v*point_coords.shape[0],
                        [('position', np.float32, 3),
                         ('texcoord', np.float32, 2),
                         ('normal', np.float32, 3),
                         ('color', np.float32, 4)])
        filled_indices = np.zeros([self.nb_fi*point_coords.shape[0], 3], np.uint32)
        outline_indices = np.zeros([self.nb_oi*point_coords.shape[0], 2], np.uint32)

        # Iterate for every marker
        for i in range(point_coords.shape[0]):
            idx_v_start  = self.nb_v*i
            idx_v_end    = self.nb_v*(i+1)
            idx_fi_start = self.nb_fi*i
            idx_fi_end   = self.nb_fi*(i+1)
            idx_oi_start = self.nb_oi*i
            idx_oi_end   = self.nb_oi*(i+1)

            # Scale and translate unit box
            vertices[idx_v_start:idx_v_end]['position'] = self.vertices_box['position']*scale[i]
            filled_indices[idx_fi_start:idx_fi_end] = self.filled_indices_box + idx_v_start
            outline_indices[idx_oi_start:idx_oi_end] = self.outline_indices_box + idx_v_start

            # rotation box
            if self.rotation is not None:
                vertices[idx_v_start:idx_v_end]['position'] = \
                        np.dot(vertices[idx_v_start:idx_v_end]['position'], self.rotation_mat[i])

            vertices[idx_v_start:idx_v_end]['position'] += point_coords[i]

        #  print('position:', vertices['position'])
        #  print('position:', vertices['position'].shape)

        # Create MeshVisual for faces and borders
        self._mesh = MeshVisual(vertices['position'], filled_indices,
                                vertex_colors, self.face_colors, color, shading=None)
        if self.edge_color is not None:
            self.set_edge_colors()
            self._border = MeshVisual(vertices['position'], outline_indices,
                                      vertex_colors=self.edge_colors, mode='lines')
        else:
            self._border = MeshVisual()

        CompoundVisual.__init__(self, [self._mesh, self._border], **kwargs)
        self.mesh.set_gl_state(polygon_offset_fill=True,
                               polygon_offset=(1, 1), depth_test=True)

    def set_face_colors(self):
        self.face_colors = np.tile(self.face_color, 12).reshape(-1, 4)

    def set_edge_colors(self):
        self.edge_colors = np.tile(self.edge_color, 24).reshape(-1, 4)

    def set_rotation_mat(self):
        self.rotation_mat = []
        for theta in self.rotation:
            #  self.rotation_mat.append(Rotation.from_rotvec([0., 0., theta]).as_matrix())
            self.rotation_mat.append(Rotation.from_euler('xyz', [0., 0., theta]).as_matrix())

    def set_data(self, point_coords=None, width=None, height=None, depth=None, vertex_colors=None,
            face_color=None, color=None, edge_color=None, rotation=None):

        if point_coords is None:
            point_coords = self.point_coords
        else:
            self.point_coords = point_coords

        if width is None:
            width = self.width
        else:
            self.width = width

        if height is None:
            height = self.height
        else:
            self.height = height

        if depth is None:
            depth = self.depth
        else:
            self.depth = depth

        if color is None:
            color = self.color
        else:
            self.color = color

        if edge_color is None:
            edge_color = self.edge_color
        else:
            self.edge_color = edge_color

        if face_color is None:
            face_color = self.face_color
        else:
            self.face_color = face_color

        if rotation is None:
            rotation = self.rotation
        else:
            self.rotation = rotation

        self.nb_points = point_coords.shape[0]

        if self.rotation is not None:
            self.set_rotation_mat()
        if self.face_color is not None:
            self.set_face_colors()
        if self.edge_color is not None:
            self.set_edge_colors()

        #  self.vertices_box, self.filled_indices_box, self.outline_indices_box = create_box(
                #  1, 1, 1, 1, 1, 1, None)

        # Create empty arrays for vertices, filled_indices and outline_indices
        vertices = np.zeros(self.nb_v*point_coords.shape[0],
                        [('position', np.float32, 3),
                         ('texcoord', np.float32, 2),
                         ('normal', np.float32, 3),
                         ('color', np.float32, 4)])
        filled_indices = np.zeros([self.nb_fi*point_coords.shape[0], 3], np.uint32)
        outline_indices = np.zeros([self.nb_oi*point_coords.shape[0], 2], np.uint32)

        #  scale = np.array([width, height, depth])
        #  scale = np.hstack((width, height, depth))
        scale = np.hstack((self.width, self.height, self.depth))

        # Iterate for every marker
        for i in range(point_coords.shape[0]):
            idx_v_start  = self.nb_v*i
            idx_v_end    = self.nb_v*(i+1)
            idx_fi_start = self.nb_fi*i
            idx_fi_end   = self.nb_fi*(i+1)
            idx_oi_start = self.nb_oi*i
            idx_oi_end   = self.nb_oi*(i+1)

            # Scale and translate unit box
            vertices[idx_v_start:idx_v_end]['position'] = self.vertices_box['position']*scale[i]
            filled_indices[idx_fi_start:idx_fi_end] = self.filled_indices_box + idx_v_start
            outline_indices[idx_oi_start:idx_oi_end] = self.outline_indices_box + idx_v_start
            if self.rotation is not None:
                vertices[idx_v_start:idx_v_end]['position'] = \
                        np.dot(vertices[idx_v_start:idx_v_end]['position'], self.rotation_mat[i])

            vertices[idx_v_start:idx_v_end]['position'] += point_coords[i]

        # Create MeshVisual for faces and borders
        self.mesh.set_data(vertices['position'], filled_indices, vertex_colors, self.face_colors,
                color)
        #  self.border.set_data(vertices['position'], outline_indices, color=edge_color)
        if self.edge_color is not None:
            self.border.set_data(vertices['position'], outline_indices,
                    vertex_colors=self.edge_colors)
        else:
            self.border.set_data(vertices['position'], outline_indices, edge_color=color)

    @property
    def mesh(self):
        """The vispy.visuals.MeshVisual that used to fill in.
        """
        return self._mesh

    @mesh.setter
    def mesh(self, mesh):
        self._mesh = mesh

    @property
    def border(self):
        """The vispy.visuals.MeshVisual that used to draw the border.
        """
        return self._border

    @border.setter
    def border(self, border):
        self._border = border

class UnifiedBoxMarkersVisual(CompoundVisual):
    """Visual that displays a box.

    Parameters
    ----------
    point_coords : array_like
        Marker coordinates
    width : float
        Box width.
    height : float
        Box height.
    depth : float
        Box depth.
    width_segments : int
        Box segments count along the width.
    height_segments : float
        Box segments count along the height.
    depth_segments : float
        Box segments count along the depth.
    planes: array_like
        Any combination of ``{'-x', '+x', '-y', '+y', '-z', '+z'}``
        Included planes in the box construction.
    vertex_colors : ndarray
        Same as for `MeshVisual` class. See `create_plane` for vertex ordering.
    face_colors : ndarray
        Same as for `MeshVisual` class. See `create_plane` for vertex ordering.
    color : Color
        The `Color` to use when drawing the cube faces.
    edge_color : tuple or Color
        The `Color` to use when drawing the cube edges. If `None`, then no
        cube edges are drawn.
    """

    def __init__(self, point_coords=np.array([0,0,0]), width=1, height=1, depth=1, width_segments=1,
                 height_segments=1, depth_segments=1, planes=None,
                 vertex_colors=None, face_colors=None,
                 color=(0.5, 0.5, 1, 1), edge_color=None, **kwargs):

        self.point_coords = point_coords

        # Create a unit box
        width_box  = 1
        height_box = 1
        depth_box  = 1

        scale = np.array([width/width_box, height/height_box, depth/depth_box])

        vertices_box, filled_indices_box, outline_indices_box = create_box(
                width_box, height_box, depth_box, width_segments, height_segments,
                depth_segments, planes)

        # Store number of vertices, filled_indices and outline_indices per box
        self.nb_v  = vertices_box.shape[0]
        self.nb_fi = filled_indices_box.shape[0]
        self.nb_oi = outline_indices_box.shape[0]

        # Create empty arrays for vertices, filled_indices and outline_indices
        vertices = np.zeros(24*point_coords.shape[0],
                        [('position', np.float32, 3),
                         ('texcoord', np.float32, 2),
                         ('normal', np.float32, 3),
                         ('color', np.float32, 4)])
        filled_indices = np.zeros([12*point_coords.shape[0], 3], np.uint32)
        outline_indices = np.zeros([24*point_coords.shape[0], 2], np.uint32)

        # Iterate for every marker
        for i in range(point_coords.shape[0]):
            idx_v_start  = self.nb_v*i
            idx_v_end    = self.nb_v*(i+1)
            idx_fi_start = self.nb_fi*i
            idx_fi_end   = self.nb_fi*(i+1)
            idx_oi_start = self.nb_oi*i
            idx_oi_end   = self.nb_oi*(i+1)
            #  print('position:', vertices['position'])

            # Scale and translate unit box
            vertices[idx_v_start:idx_v_end]['position'] = vertices_box['position']*scale + point_coords[i]
            filled_indices[idx_fi_start:idx_fi_end] = filled_indices_box + idx_v_start
            outline_indices[idx_oi_start:idx_oi_end] = outline_indices_box + idx_v_start
        #  print('position:', vertices['position'])

        # Create MeshVisual for faces and borders
        self._mesh = MeshVisual(vertices['position'], filled_indices,
                                vertex_colors, face_colors, color, shading=None)
        if edge_color:
            self._border = MeshVisual(vertices['position'], outline_indices,
                                      color=edge_color, mode='lines')
        else:
            self._border = MeshVisual()

        CompoundVisual.__init__(self, [self._mesh, self._border], **kwargs)
        self.mesh.set_gl_state(polygon_offset_fill=True,
                               polygon_offset=(1, 1), depth_test=True)

    @property
    def mesh(self):
        """The vispy.visuals.MeshVisual that used to fill in.
        """
        return self._mesh

    @mesh.setter
    def mesh(self, mesh):
        self._mesh = mesh

    @property
    def border(self):
        """The vispy.visuals.MeshVisual that used to draw the border.
        """
        return self._border

    @border.setter
    def border(self, border):
        self._border = border


BoxMarkers = create_visual_node(BoxMarkersVisual)
UnifiedBoxMarkers = create_visual_node(UnifiedBoxMarkersVisual)

#  if __name__ == '__main__':
    #  boxes = BoxMarkers()
