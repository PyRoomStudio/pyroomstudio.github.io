from direct.showbase.ShowBase import ShowBase, loadPrcFileData
from panda3d.core import Vec3

# Enable the assimp loader so that .obj files can be loaded.
loadPrcFileData("", "load-file-type p3assimp")

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # Disable default mouse-based camera control to allow custom movement.
        #self.disableMouse()

        # Load the .obj model. Change the file path as needed.
        self.model = self.loader.loadModel("resources/eb_house_plant_01.obj")
        self.model.reparentTo(self.render)
        # Adjust model placement if necessary.
        self.model.setPos(0, 50, 0)

        # Set an initial camera position and orient it towards the model.
        self.camera.setPos(0, 0, 10)
        self.camera.lookAt(self.model)

        # Speeds for movement (units per second) and rotation (degrees per second).
        self.moveSpeed = 20
        self.rotateSpeed = 60

        # Add a task to update the camera position each frame.
        self.taskMgr.add(self.updateTask, "updateTask")

    def updateKey(self, key, state):
        self.keyMap[key] = state

    def updateTask(self, task):
        dt = globalClock.getDt()

        # Calculate the forward and right vectors relative to the current view.
        forward = self.camera.getQuat(self.render).getForward()
        right = self.camera.getQuat(self.render).getRight()

        return task.cont

app = MyApp()
app.run()