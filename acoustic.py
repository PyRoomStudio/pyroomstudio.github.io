"""
The Acoustic Class handles all the pyroomacoustics functions 
necessary for simulating sound in a given environment.
"""

import pyroomacoustics as pra
import numpy as np

class Acoustic(pra.room.Room):

    def build_stl():
        """
        Build the room from an STL file.
        """
        pass


    def build_obj():
        """
        Build the room from an OBJ file.
        """
        pass


    def __init__(self, filename: str):
        pra.room.Room.__init__(self)
        self.sample_rate = 44100
        self.speed_of_sound = 343.0

        w = pra.wall.Wall()
        return
    
    def simulate(self):
        return 0