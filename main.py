from render3 import Render3
from acoustic import Acoustic

# Trimesh rendering
# TODO: Can trimesh handle GUI elements and model interaction?
#from render4 import Render4

import sys
from OpenGL.GL import *


class App():
    def __init__(self, model_name):
        self.name = 'App'
        self.render = Render3(filename=model_name)
        self.acoustic = Acoustic()
        self.running = True

    def run(self):
        self.render.run()

if __name__ == '__main__':
    model_name: str = 'resources/prism_star_5.stl' if (len(sys.argv) < 2) else sys.argv[1]
    app = App(model_name)
    app.run()
