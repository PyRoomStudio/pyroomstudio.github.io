"""
The Render2 Class processes all visual elements of the application using PyGame and PyOpenGL
to render meshes relative to the intended acoustics simulations.
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from stl import mesh
import math
import sys
from acoustic import Acoustic

# Constants for camera control
CAMERA_DIST = 5.0      # Distance from camera to object
MIN_DIST = 1.0         # Minimum zoom distance
MAX_DIST = 5.0         # Maximum zoom distance
CAMERA_HEADING = 35.0  # Horizontal rotation angle
CAMERA_PITCH = 35.0    # Vertical rotation angle
MIN_PITCH = 0.0        # Limit looking down
MAX_PITCH = 85.0       # Limit looking up

class Render:
    def __init__(self, filename, acoustic: Acoustic, width=800, height=600):
        """Initialize the renderer with PyGame and OpenGL"""
        pygame.init()
        self.width = width
        self.height = height
        self.display = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Model Viewer")
        
        # Set up OpenGL
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set up the viewport
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (width/height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        
        # Set white background
        glClearColor(1.0, 1.0, 1.0, 1.0)
        
        # Initialize camera parameters
        self.camera_distance = CAMERA_DIST
        self.camera_heading = CAMERA_HEADING
        self.camera_pitch = CAMERA_PITCH
        self.min_distance = MIN_DIST
        self.max_distance = MAX_DIST
        self.min_pitch = MIN_PITCH
        self.max_pitch = MAX_PITCH
        
        # Mouse control variables
        self.mouse_down = False
        self.last_mouse_pos = None
        
        # Initialize vertex colors (all blue)
        self.vertex_colors = None
        
        # Load the model
        self.center, self.volume = self.compute_volumetric_properties(filename)
        self.ratio = (self.volume / 1000 / 7500)
        self.model = self.load_model(filename)
        
        # Initialize vertex colors (all blue)
        self.vertex_colors = np.full((len(self.model['vertices']), 3), [0.0, 0.0, 1.0])
        
        # Store acoustic reference
        self.acoustic = acoustic
        
        # Set up lighting
        self.setup_lighting()
        
        # Initialize font for text rendering
        pygame.font.init()
        self.font = pygame.font.Font(None, 36)
        
        # Initialize model rotation state
        self.model_rotation_x = 0.0
        
        # Initialize highlight timer
        self.highlight_end_time = 0
        self.highlighted_triangles = set()

    def compute_volumetric_properties(self, filename: str) -> tuple[np.ndarray, float]:
        """Computes the volumetric center (centroid) of a closed triangular mesh."""
        stl_mesh = mesh.Mesh.from_file(filename)
        
        total_volume = 0.0
        centroid_sum = np.zeros(3)
        
        for triangle in stl_mesh.vectors:
            v0, v1, v2 = triangle
            tetra_volume = np.dot(v0, np.cross(v1, v2)) / 6.0
            tetra_centroid = (v0 + v1 + v2) / 4.0
            
            centroid_sum += tetra_centroid * tetra_volume
            total_volume += tetra_volume
            
        if np.isclose(total_volume, 0):
            raise ValueError("Calculated volume is zero; ensure the STL mesh is closed and valid.")
            
        volumetric_center = centroid_sum / total_volume
        return volumetric_center, total_volume

    def load_model(self, filename):
        """Load a 3D model from file"""
        if filename.endswith('.stl'):
            stl_mesh = mesh.Mesh.from_file(filename)
            vertices = stl_mesh.vectors.reshape(-1, 3)
            normals = stl_mesh.normals
            return {'vertices': vertices, 'normals': normals}
        else:
            raise ValueError("Only .stl files are supported")

    def setup_lighting(self):
        """Set up scene lighting"""
        # Ambient light
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        
        # Main light
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])

    def update_camera(self):
        """Update camera position based on current angles and distance"""
        glLoadIdentity()
        
        # Convert angles to radians
        heading_rad = math.radians(self.camera_heading)
        pitch_rad = math.radians(self.camera_pitch)
        
        # Calculate camera position using spherical coordinates
        x = self.camera_distance * math.sin(heading_rad) * math.cos(pitch_rad)
        y = -self.camera_distance * math.cos(heading_rad) * math.cos(pitch_rad)
        z = self.camera_distance * math.sin(pitch_rad)
        
        gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

    def get_ray_from_mouse(self, mouse_pos):
        """Convert mouse position to a ray in world space"""
        # Get viewport and modelview/projection matrices
        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        
        # Convert mouse position to normalized device coordinates
        x = mouse_pos[0]
        y = viewport[3] - mouse_pos[1]  # Flip y coordinate
        
        # Get near and far points in world space
        near = gluUnProject(x, y, 0.0, modelview, projection, viewport)
        far = gluUnProject(x, y, 1.0, modelview, projection, viewport)
        
        # Calculate ray direction
        ray_dir = np.array(far) - np.array(near)
        ray_dir = ray_dir / np.linalg.norm(ray_dir)
        
        return np.array(near), ray_dir

    def check_triangle_intersection(self, ray_origin, ray_dir, triangle):
        """Check if ray intersects with triangle using Möller–Trumbore algorithm"""
        v0, v1, v2 = triangle
        
        # Calculate edges
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        # Calculate determinant
        h = np.cross(ray_dir, edge2)
        a = np.dot(edge1, h)
        
        if abs(a) < 1e-6:
            return None  # Ray is parallel to triangle
            
        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)
        
        if u < 0.0 or u > 1.0:
            return None
            
        q = np.cross(s, edge1)
        v = f * np.dot(ray_dir, q)
        
        if v < 0.0 or u + v > 1.0:
            return None
            
        t = f * np.dot(edge2, q)
        
        if t > 1e-6:
            return t
            
        return None

    def find_connected_triangles(self, start_triangle_idx):
        """Find all triangles connected to the start triangle that share the same normal"""
        connected = set()
        to_check = {start_triangle_idx}
        start_normal = self.model['normals'][start_triangle_idx]
        
        while to_check:
            current = to_check.pop()
            if current in connected:
                continue
                
            connected.add(current)
            current_normal = self.model['normals'][current]
            
            # Only add triangles with the same normal
            if np.dot(start_normal, current_normal) > 0.9999:
                # Get vertices of current triangle
                v1, v2, v3 = self.model['vertices'][current*3:(current+1)*3]
                
                # Check all other triangles for connections
                for i in range(0, len(self.model['vertices']), 3):
                    other_idx = i // 3
                    if other_idx in connected:
                        continue
                        
                    other_normal = self.model['normals'][other_idx]
                    if np.dot(start_normal, other_normal) > 0.9999:
                        # Get vertices of other triangle
                        ov1, ov2, ov3 = self.model['vertices'][other_idx*3:(other_idx+1)*3]
                        
                        # Check if triangles share an edge
                        if (np.array_equal(v1, ov1) or np.array_equal(v1, ov2) or np.array_equal(v1, ov3) or
                            np.array_equal(v2, ov1) or np.array_equal(v2, ov2) or np.array_equal(v2, ov3) or
                            np.array_equal(v3, ov1) or np.array_equal(v3, ov2) or np.array_equal(v3, ov3)):
                            to_check.add(other_idx)
        
        return connected

    def handle_click(self, mouse_pos):
        """Handle mouse click to highlight connected planes"""
        # Get ray from mouse position
        ray_origin, ray_dir = self.get_ray_from_mouse(mouse_pos)
        
        # Find closest intersecting triangle
        closest_t = float('inf')
        closest_triangle = None
        
        for i in range(0, len(self.model['vertices']), 3):
            triangle = self.model['vertices'][i:i+3]
            t = self.check_triangle_intersection(ray_origin, ray_dir, triangle)
            
            if t is not None and t < closest_t:
                closest_t = t
                closest_triangle = i // 3
        
        if closest_triangle is not None:
            # Find all connected triangles with same normal
            connected_triangles = self.find_connected_triangles(closest_triangle)
            
            # Reset all triangles to blue
            self.vertex_colors[:] = [0.0, 0.0, 1.0]
            
            # Highlight connected triangles in red
            for triangle_idx in connected_triangles:
                start_idx = triangle_idx * 3
                self.vertex_colors[start_idx:start_idx+3] = [1.0, 0.0, 0.0]
            
            # Set timer for 1 second
            self.highlight_end_time = pygame.time.get_ticks() + 1000
            self.highlighted_triangles = connected_triangles

    def update_highlight_timer(self):
        """Update highlight timer and reset colors if time has expired"""
        current_time = pygame.time.get_ticks()
        if current_time > self.highlight_end_time and self.highlighted_triangles:
            # Reset highlighted triangles to blue
            for triangle_idx in self.highlighted_triangles:
                start_idx = triangle_idx * 3
                self.vertex_colors[start_idx:start_idx+3] = [0.0, 0.0, 1.0]
            self.highlighted_triangles.clear()

    def draw_model(self):
        """Draw the loaded 3D model"""
        glPushMatrix()
        
        # Scale and center the model
        scale = 1/self.ratio
        glScalef(scale, scale, scale)
        newcenter = self.center/self.ratio
        glTranslatef(-newcenter[0], newcenter[1]*1.75, -newcenter[2])
        
        # Apply X-axis rotation
        glRotatef(self.model_rotation_x, 1, 0, 0)
        
        # Draw the model with colors
        glBegin(GL_TRIANGLES)
        for i in range(0, len(self.model['vertices']), 3):
            normal = self.model['normals'][i//3]
            glNormal3fv(normal)
            for j in range(3):
                vertex = self.model['vertices'][i + j]
                color = self.vertex_colors[i + j]
                glColor3fv(color)
                glVertex3fv(vertex)
        glEnd()
        
        # Draw edges between planes
        glDisable(GL_LIGHTING)  # Disable lighting for edges
        glLineWidth(2.0)  # Set line width
        glBegin(GL_LINES)
        glColor3f(0.0, 0.0, 0.0)  # Black color for edges
        
        # Create a set to store processed edges to avoid duplicates
        processed_edges = set()
        
        for i in range(0, len(self.model['vertices']), 3):
            # Get vertices of current triangle
            v1 = tuple(self.model['vertices'][i])
            v2 = tuple(self.model['vertices'][i + 1])
            v3 = tuple(self.model['vertices'][i + 2])
            
            # Create edges (always store in sorted order to avoid duplicates)
            edges = [
                tuple(sorted([v1, v2])),
                tuple(sorted([v2, v3])),
                tuple(sorted([v3, v1]))
            ]
            
            # Draw each edge if not already processed
            for edge in edges:
                if edge not in processed_edges:
                    processed_edges.add(edge)
                    glVertex3fv(edge[0])
                    glVertex3fv(edge[1])
        
        glEnd()
        glLineWidth(1.0)  # Reset line width
        glEnable(GL_LIGHTING)  # Re-enable lighting
        
        glPopMatrix()

    def draw_axes(self):
        """Draw coordinate axes"""
        glPushMatrix()
        glBegin(GL_LINES)
        
        # X axis (red)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)
        
        # Y axis (green)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 1, 0)
        
        # Z axis (blue)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1)
        
        glEnd()
        glPopMatrix()

    def draw_stats(self):
        """Draw camera statistics on screen"""
        # Create text surfaces with black color for better visibility on white background
        heading_text = f"Heading: {self.camera_heading%360:.1f}°"
        pitch_text = f"Pitch: {self.camera_pitch:.1f}°"
        
        heading_surface = self.font.render(heading_text, True, (0, 0, 0))
        pitch_surface = self.font.render(pitch_text, True, (0, 0, 0))
        
        # Switch to 2D rendering mode
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Disable depth testing and lighting for 2D rendering
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Enable blending for text
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Convert PyGame surface to OpenGL texture
        heading_data = pygame.image.tostring(heading_surface, "RGBA", True)
        pitch_data = pygame.image.tostring(pitch_surface, "RGBA", True)
        
        # Create and bind textures
        heading_texture = glGenTextures(1)
        pitch_texture = glGenTextures(1)
        
        # Upload heading texture
        glBindTexture(GL_TEXTURE_2D, heading_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, heading_surface.get_width(), heading_surface.get_height(), 
                    0, GL_RGBA, GL_UNSIGNED_BYTE, heading_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        
        # Upload pitch texture
        glBindTexture(GL_TEXTURE_2D, pitch_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, pitch_surface.get_width(), pitch_surface.get_height(), 
                    0, GL_RGBA, GL_UNSIGNED_BYTE, pitch_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        
        # Enable texturing
        glEnable(GL_TEXTURE_2D)
        
        # Draw heading text (flipped texture coordinates to fix upside-down text)
        glBindTexture(GL_TEXTURE_2D, heading_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(20, 20)
        glTexCoord2f(1, 1); glVertex2f(20 + heading_surface.get_width(), 20)
        glTexCoord2f(1, 0); glVertex2f(20 + heading_surface.get_width(), 20 + heading_surface.get_height())
        glTexCoord2f(0, 0); glVertex2f(20, 20 + heading_surface.get_height())
        glEnd()
        
        # Draw pitch text (flipped texture coordinates to fix upside-down text)
        glBindTexture(GL_TEXTURE_2D, pitch_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(20, 60)
        glTexCoord2f(1, 1); glVertex2f(20 + pitch_surface.get_width(), 60)
        glTexCoord2f(1, 0); glVertex2f(20 + pitch_surface.get_width(), 60 + pitch_surface.get_height())
        glTexCoord2f(0, 0); glVertex2f(20, 60 + pitch_surface.get_height())
        glEnd()
        
        # Clean up
        glDeleteTextures([heading_texture, pitch_texture])
        glDisable(GL_TEXTURE_2D)
        
        # Restore OpenGL state
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def flip_model_x(self):
        """Flip the model 90 degrees around the X axis"""
        self.model_rotation_x = (self.model_rotation_x + 90) % 360 