# pyCamera

> Discription of the application and relevent features. 

## Installation

Important required libraries

- PySpin: install (link the stack exchange post and the actual website)
- OpenCV
- ffmpeg installation required
- ffmpeg-python API is how is it called
- GUI in PyQT6
- pyqtgraph

- USB camera support handled by cv2_enumerate_cameras

## Camera support

PySpin Spinnaker Chameleon.
USB Camera (almost supported.)

### Currently supported cameras

- Should install from source as an editable library.
- Go to `/api/cameras.py` and add your own camera
- go to function that gets the list of unique ids and add your new class to the list of classes that are searched through.

### Adding your own APIs fro unsupported cameras

- Inheriting from the Camera template class and redefining functions

## Opening pyCamera from config file

- Get the config file from the `/experiments` folder and use that as the input to the `--config` argument

`--config /path/to/config.json` argument and example usage. for example: `C:/Users/alifa/Anaconda3/envs/flir/python.exe "c:/Users/alifa/OneDrive - Nexus365/Documents/Video Aquisition Application/pyCamera/code/pyCamera_GUI.pyw" --config "C:\Users\alifa\OneDrive - Nexus365\Documents\Video Aquisition Application\pyCamera\code\experiments\fps-3.json"`

