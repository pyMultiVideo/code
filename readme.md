# pyMultiVideo

- What it is this application for 

> Description of the application and relevent features. 

- Ability to aquire video from mulitple cameras at the same time. 
- Can Synchronously update collect the GPIO Pin states from the cameras that are set up
- Ability for you to write your own APIs that work with this application 
- Encoding of video can be done using CPU or GPU (GPU preferred). Note:  This is handled by FFMPEG
- Spinnaker Camera buffer handling done (Video should not drop frames as internal buffer is emptied automatically)

- Spinnaker Cameras supported out of the box via Teledynes's Python API

## Installation

See [Installation Help](/_installation/README.md) for information how to install the application.

## Camera support

PySpin Spinnaker Chameleon.
USB Camera

### Currently supported cameras

- Should install from source as an editable library.
- Go to `/api/cameras.py` and add your own camera
- go to function that gets the list of unique ids and add your new class to the list of classes that are searched through.

### Adding your own APIs fro unsupported cameras

- Inheriting from the Camera template class and redefining functions

## Opening pyMultiVideo from config file

- Get the config file from the `/experiments` folder and use that as the input to the `--config` argument

`--config /path/to/config.json` argument and example usage. for example: `C:/Users/alifa/Anaconda3/envs/flir/python.exe "c:/Users/alifa/OneDrive - Nexus365/Documents/Video Aquisition Application/pyMultiVideo/code/pyMultiVideo_GUI.pyw" --config "C:\Users\alifa\OneDrive - Nexus365\Documents\Video Aquisition Application\pyMultiVideo\code\experiments\fps-3.json"`

