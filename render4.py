import trimesh
import numpy as np
import pyglet
from pyglet.window import mouse
import random
from trimesh.viewer.windowed import SceneViewer
from pyglet.gl import glGetDoublev, glGetIntegerv, GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX, GL_VIEWPORT, gluUnProject
from ctypes import byref, c_double

class Render4:
    def __init__(self, filename):
        self.mesh = trimesh.load(filename, force='mesh')
        # Set all faces to the same color initially
        self.mesh.visual.face_colors = [150, 200, 255, 255]  # RGBA
        self.scene = trimesh.Scene(self.mesh)
        self.viewer = None

    def random_color(self):
        return [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]

    def run(self):
        # Only use SceneViewer; do not create a separate pyglet window.
        # Note: Custom picking is not supported in trimesh's default SceneViewer.
        # The mesh will be shown in the SceneViewer window only.
        self.viewer = SceneViewer(self.scene)
        # If you want to add custom picking, you would need to subclass SceneViewer or use another library.

        @self.viewer.event
        def on_mouse_press(x, y, button, modifiers):
            if button == mouse.LEFT:
                # Get OpenGL matrices and viewport
                modelview = (pyglet.gl.GLdouble * 16)()
                projection = (pyglet.gl.GLdouble * 16)()
                viewport = (pyglet.gl.GLint * 4)()
                glGetDoublev(GL_MODELVIEW_MATRIX, modelview)
                glGetDoublev(GL_PROJECTION_MATRIX, projection)
                glGetIntegerv(GL_VIEWPORT, viewport)
                real_y = viewport[3] - y

                # Unproject near and far points using c_double and byref
                near_x, near_y, near_z = c_double(), c_double(), c_double()
                far_x, far_y, far_z = c_double(), c_double(), c_double()
                gluUnProject(x, real_y, 0.0, modelview, projection, viewport, byref(near_x), byref(near_y), byref(near_z))
                gluUnProject(x, real_y, 1.0, modelview, projection, viewport, byref(far_x), byref(far_y), byref(far_z))
                ray_origin = np.array([near_x.value, near_y.value, near_z.value])
                ray_direction = np.array([far_x.value, far_y.value, far_z.value]) - ray_origin
                ray_direction /= np.linalg.norm(ray_direction)

                # Use trimesh ray-mesh intersection
                locations, index_ray, index_tri = self.mesh.ray.intersects_location(
                    ray_origins=[ray_origin],
                    ray_directions=[ray_direction]
                )
                if len(index_tri) > 0:
                    face = index_tri[0]
                    self.mesh.visual.face_colors[face] = self.random_color()
                    # Update the scene to reflect the color change
                    self.scene = trimesh.Scene(self.mesh)
                    self.viewer.scene = self.scene

        pyglet.app.run()
    