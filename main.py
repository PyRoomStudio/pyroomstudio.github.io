from render3 import Render3
# Trimesh rendering
# TODO: Can trimesh handle GUI elements and model interaction?
#from render4 import Render4
import sys
import time
import pygame
from OpenGL.GL import *


class App():
    def __init__(self, model_name):
        self.name = 'App'
        self.render = Render3(filename=model_name)
        self.running = True

    def run(self):
        self.render.run()

if __name__ == '__main__':
    model_name: str = 'resources/INRIA_MUSIS.stl' if (len(sys.argv) < 2) else sys.argv[1]
    app = App(model_name)
    app.run()
