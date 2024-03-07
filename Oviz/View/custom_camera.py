# -*- coding: utf-8 -*-
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

from __future__ import division

import numpy as np
from vispy.util import transforms, keys
from vispy.scene.cameras.perspective import Base3DRotationCamera, PerspectiveCamera

def rotate_around_forward(angle, forward):
    # 将向量转换为单位向量
    forward = forward / np.linalg.norm(forward)

    # 根据旋转角度创建旋转矩阵
    theta = np.radians(angle)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    rotation_matrix = np.array([[cos_theta + forward[0]**2 * (1 - cos_theta),
                                 forward[0] * forward[1] * (1 - cos_theta) - forward[2] * sin_theta,
                                 forward[0] * forward[2] * (1 - cos_theta) + forward[1] * sin_theta],
                                [forward[1] * forward[0] * (1 - cos_theta) + forward[2] * sin_theta,
                                 cos_theta + forward[1]**2 * (1 - cos_theta),
                                 forward[1] * forward[2] * (1 - cos_theta) - forward[0] * sin_theta],
                                [forward[2] * forward[0] * (1 - cos_theta) - forward[1] * sin_theta,
                                 forward[2] * forward[1] * (1 - cos_theta) + forward[0] * sin_theta,
                                 cos_theta + forward[2]**2 * (1 - cos_theta)]])

    # 应用旋转矩阵到forward向量上
    rotated_forward = np.dot(rotation_matrix, forward)

    return rotated_forward


class CustomCamera(Base3DRotationCamera):
    """3D camera class that orbits around a center point while
    maintaining a view on a center point.

    For this camera, the ``scale_factor`` indicates the zoom level, and
    the ``center`` indicates the position to put at the center of the
    view.

    When ``elevation`` and ``azimuth`` are set to 0, the camera
    points along the +y axis.

    Parameters
    ----------
    fov : float
        Field of view. 0.0 means orthographic projection,
        default is 45.0 (some perspective)
    elevation : float
        Elevation angle in degrees. The elevation angle represents a
        rotation of the camera around the current scene x-axis. The
        camera points along the x-y plane when the angle is 0.
    azimuth : float
        Azimuth angle in degrees. The azimuth angle represents a
        rotation of the camera around the scene z-axis according to the
        right-hand screw rule. The camera points along the y-z plane when
        the angle is 0.
    roll : float
        Roll angle in degrees. The roll angle represents a rotation of
        the camera around the current scene y-axis.
    distance : float | None
        The distance of the camera from the rotation point (only makes sense
        if fov > 0). If None (default) the distance is determined from the
        scale_factor and fov.
    translate_speed : float
        Scale factor on translation speed when moving the camera center point.
    **kwargs : dict
        Keyword arguments to pass to `BaseCamera`.

    Notes
    -----
    Interaction:

        * LMB: orbits the view around its center point.
        * RMB or scroll: change scale_factor (i.e. zoom level)
        * SHIFT + LMB: translate the center point
        * SHIFT + RMB: change FOV

    """

    _state_props = Base3DRotationCamera._state_props + ("elevation", "azimuth", "roll")

    def __init__(
        self,
        fov=45.0,
        elevation=30.0,
        azimuth=30.0,
        roll=0.0,
        distance=None,
        translate_speed=1.0,
        **kwargs
    ):
        super(CustomCamera, self).__init__(fov=fov, **kwargs)

        # Set camera attributes
        self.azimuth = azimuth
        self.elevation = elevation
        self.roll = roll
        self.distance = distance  # None means auto-distance
        self.translate_speed = translate_speed

    @property
    def elevation(self):
        """Get the camera elevation angle in degrees.

        The camera points along the x-y plane when the angle is 0.
        """
        return self._elevation

    @elevation.setter
    def elevation(self, elev):
        elev = float(elev)
        self._elevation = min(90, max(-90, elev))
        self.view_changed()

    @property
    def azimuth(self):
        """Get the camera azimuth angle in degrees.

        The camera points along the y-z plane when the angle is 0.
        """
        return self._azimuth

    @azimuth.setter
    def azimuth(self, azim):
        azim = float(azim)
        while azim < -180:
            azim += 360
        while azim > 180:
            azim -= 360
        self._azimuth = azim
        self.view_changed()

    @property
    def roll(self):
        """Get the camera roll angle in degrees."""
        return self._roll

    @roll.setter
    def roll(self, roll):
        roll = float(roll)
        while roll < -180:
            roll += 360
        while roll > 180:
            roll -= 360
        self._roll = roll
        self.view_changed()

    def orbit(self, azim, elev):
        """Orbits the camera around the center position.

        Parameters
        ----------
        azim : float
            Angle in degrees to rotate horizontally around the center point.
        elev : float
            Angle in degrees to rotate vertically around the center point.
        """
        self.azimuth += azim
        self.elevation = np.clip(self.elevation + elev, -90, 90)
        self.view_changed()

    def _update_rotation(self, event):
        """Update rotation parmeters based on mouse movement"""
        p1 = event.mouse_event.press_event.pos
        p2 = event.mouse_event.pos
        if self._event_value is None:
            self._event_value = self.azimuth, self.elevation
        self.azimuth = self._event_value[0] - (p2 - p1)[0] * 0.5
        self.elevation = self._event_value[1] + (p2 - p1)[1] * 0.5

    def _update_ctrl_rotation(self, event):
        p1 = event.mouse_event.press_event.pos
        p2 = event.mouse_event.pos
        if self._event_value is None:
            self._event_value = self.azimuth, self.elevation, self.roll

        # dx, dy, dz = self._dist_to_trans(p2 - p1)
        # print(dx, dy, dz)
        # # self.azimuth = self._event_value[0] - dx * 0.5
        # self.elevation = self._event_value[0] + dy * 0.5
        self.roll = self._event_value[1] + (p2 - p1)[0]  * 0.5


    def _get_rotation_tr(self):
        """Return a rotation matrix based on camera parameters"""
        up, forward, right = self._get_dim_vectors()
        matrix = (
            transforms.rotate(self.elevation, -right)
            .dot(transforms.rotate(self.azimuth, up))
            .dot(transforms.rotate(self.roll, forward))
        )
        return matrix

    def _dist_to_trans(self, dist):
        """Convert mouse x, y movement into x, y, z translations"""
        rae = np.array([self.roll, self.azimuth, self.elevation]) * np.pi / 180
        sro, saz, sel = np.sin(rae)
        cro, caz, cel = np.cos(rae)
        d0, d1 = dist[0], dist[1]
        dx = (+ d0 * (cro * caz + sro * sel * saz)
              + d1 * (sro * caz - cro * sel * saz)) * self.translate_speed
        dy = (+ d0 * (cro * saz - sro * sel * caz)
              + d1 * (sro * saz + cro * sel * caz)) * self.translate_speed
        dz = (- d0 * sro * cel + d1 * cro * cel) * self.translate_speed
        return dx, dy, dz


    def viewbox_mouse_event(self, event):
        """
        The viewbox received a mouse event; update transform
        accordingly.

        Parameters
        ----------
        event : instance of Event
            The event.
        """
        if event.handled or not self.interactive:
            return

        PerspectiveCamera.viewbox_mouse_event(self, event)

        if event.type == 'mouse_release':
            self._event_value = None  # Reset
        elif event.type == 'mouse_press':
            event.handled = True
        elif event.type == 'mouse_move':
            if event.press_event is None:
                return
            if 1 in event.buttons and 2 in event.buttons:
                return

            modifiers = event.mouse_event.modifiers
            p1 = event.mouse_event.press_event.pos
            p2 = event.mouse_event.pos
            d = p2 - p1

            if 1 in event.buttons and not modifiers:
                # Rotate
                self._update_rotation(event)

            elif 2 in event.buttons and not modifiers:
                # # Zoom
                # if self._event_value is None:
                #     self._event_value = (self._scale_factor, self._distance)
                # zoomy = (1 + self.zoom_factor) ** d[1]

                # self.scale_factor = self._event_value[0] * zoomy
                # # Modify distance if its given
                # if self._distance is not None:
                #     self._distance = self._event_value[1] * zoomy
                # self.view_changed()
                # Translate
                norm = np.mean(self._viewbox.size)
                if self._event_value is None or len(self._event_value) == 2:
                    self._event_value = self.center
                dist = (p1 - p2) / norm * self._scale_factor
                dist[1] *= -1
                # Black magic part 1: turn 2D into 3D translations
                dx, dy, dz = self._dist_to_trans(dist)
                # Black magic part 2: take up-vector and flipping into account
                ff = self._flip_factors
                up, forward, right = self._get_dim_vectors()
                dx, dy, dz = right * dx + forward * dy + up * dz
                dx, dy, dz = ff[0] * dx, ff[1] * dy, dz * ff[2]
                c = self._event_value
                self.center = c[0] + dx, c[1] + dy, c[2] + dz

            elif 1 in event.buttons and keys.SHIFT in modifiers:
                # Translate
                norm = np.mean(self._viewbox.size)
                if self._event_value is None or len(self._event_value) == 2:
                    self._event_value = self.center
                dist = (p1 - p2) / norm * self._scale_factor
                dist[1] *= -1
                # Black magic part 1: turn 2D into 3D translations
                dx, dy, dz = self._dist_to_trans(dist)
                # Black magic part 2: take up-vector and flipping into account
                ff = self._flip_factors
                up, forward, right = self._get_dim_vectors()
                dx, dy, dz = right * dx + forward * dy + up * dz
                dx, dy, dz = ff[0] * dx, ff[1] * dy, dz * ff[2]
                c = self._event_value
                self.center = c[0] + dx, c[1] + dy, c[2] + dz

            elif 2 in event.buttons and keys.SHIFT in modifiers:
                # Change fov
                if self._event_value is None:
                    self._event_value = self._fov
                fov = self._event_value - d[1] / 5.0
                self.fov = min(180.0, max(0.0, fov))

            elif 1 in event.buttons and keys.CONTROL in modifiers:
                p1 = event.press_event.pos
                p2 = event.pos
                d = p2 - p1

                # 计算旋转角度
                rotation_angle = np.degrees(np.arctan2(d[1], d[0])) * 0.5
                self.azimuth += rotation_angle




'''
ch_em = self.events.transform_change
        with ch_em.blocker(self._update_transform):
            up, forward, right = self._get_dim_vectors()

            # Create mapping so correct dim is up
            pp1 = np.array([(0, 0, 0), (0, 0, -1), (1, 0, 0), (0, 1, 0)])
            pp2 = np.array([(0, 0, 0), forward, right, up])
            pos = -self._actual_distance * forward
            scale = [1.0/a for a in self._flip_factors]

            self.transform.matrix = np.linalg.multi_dot((
                transforms.affine_map(pp1, pp2).T,
                transforms.translate(pos),
                self._get_rotation_tr(),
                transforms.scale(scale),
                transforms.translate(self.center)
            ))
'''