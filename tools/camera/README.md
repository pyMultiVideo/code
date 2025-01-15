# Camera API classes
## Introduction

Located in this folder are two camera classes (each in a different file (e.g. [spinnaker_camera.py](/tools/camera/spinnaker_camera.py)))

In this example you can see different core functions of the camera api that are defined. 

These functions are then used in the main GUI of the application to perform the required functionality. 

## Add new classes

You may want to add new camera support to the application. To do this, you should add a new python file to the `/camera` directory. 

Within this you should define the behaviour required by the functions. For example the  new_camera.get_next_image() should return a np.ndarray from the function as has been done in the spinnaker_camera.get_next_image() function does.

This should be done for all the functions that are defined in the spinnaker camera and the 