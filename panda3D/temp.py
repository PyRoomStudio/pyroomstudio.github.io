import sys, os
import direct.directbase.DirectStart
from panda3d.core import Filename

# Get the location of the 'py' file I'm running:
mydir = os.path.dirname(os.path.abspath(__file__))

# Convert that to panda's unix-style notation.
mydir = Filename.fromOsSpecific(mydir)

# Now load the model:
model = loader.loadModel(mydir / "resources/eb_house_plant_01.obj")

# Reparent the model to render.
model.reparentTo(render)

# Apply scale and position transforms on the model.
model.setScale(0.01)
model.setPos(0, 0, 0)

# Run the engine:
base.run()