# pyCamera

> Description of the application and relevent features. 

- Ability to aquire video from mulitple cameras at the same time. 
- Can Synchronously update collect the GPIO Pin states from the cameras that are set up
- Ability for you to write your own APIs that work with this application 
- Encoding of video can be done using CPU or GPU (GPU preferred). Note:  This is handled by FFMPEG
- Spinnaker Camera buffer handling done (Video should not drop frames as internal buffer is emptied automatically)

- Spinnaker Cameras supported out of the box via Teledynes's Python API

## Installation

Important required libraries

- PySpin: install ([link](https://stackoverflow.com/questions/77704588/no-module-named-pyspin) the stack exchange post and the actual [website](https://www.teledynevisionsolutions.com/products/spinnaker-sdk/?model=Spinnaker%20SDK&vertical=machine%20vision&segment=iis))
- `OpenCV`
- [ffmpeg](https://www.ffmpeg.org/download.html) installation required
- `ffmpeg-python` API is how is it called
- GUI in `PyQT6`
- `pyqtgraph`

- USB camera support handled by `cv2_enumerate_cameras`

## Camera support

PySpin Spinnaker Chameleon.
USB Camera

### Currently supported cameras

- Should install from source as an editable library.
- Go to `/api/cameras.py` and add your own camera
- go to function that gets the list of unique ids and add your new class to the list of classes that are searched through.

### Adding your own APIs fro unsupported cameras

- Inheriting from the Camera template class and redefining functions

## Opening pyCamera from config file

- Get the config file from the `/experiments` folder and use that as the input to the `--config` argument

`--config /path/to/config.json` argument and example usage. for example: `C:/Users/alifa/Anaconda3/envs/flir/python.exe "c:/Users/alifa/OneDrive - Nexus365/Documents/Video Aquisition Application/pyCamera/code/pyCamera_GUI.pyw" --config "C:\Users\alifa\OneDrive - Nexus365\Documents\Video Aquisition Application\pyCamera\code\experiments\fps-3.json"`

