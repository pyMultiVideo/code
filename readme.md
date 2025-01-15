# pyMultiVideo

- `pyMultiVideo` is an application for Aquiring images from Mulitple Cameras simulaneously. This is primarily a scientific application.
- This is a `python 3.10` implementation this with GUI written using the [QT framework](https://www.qt.io/product/framework) and has a in built GUI to see the images you are aquring, whilst aqurining them
- Use of the spinnaker-python API is a key feature of this appliaction. 
- 
> Description of the application and relevent features. 

- Ability to aquire video from mulitple cameras at the same time. 
- During recording the application can get  obtain the GPIO Pin states from the cameras that being used
- Then Encoding of video can be done using CPU or GPU (GPU preferred) using [FFMPEG](https://www.ffmpeg.org/).
- Some time has been spent making sure that  the Spinnaker Camera buffer handling done correctly and it does not drop frames when aquring video. (Video should not drop frames as internal buffer is emptied automatically)

- Spinnaker Cameras supported out of the box via Teledynes's Python API

## Installation
See [Installation Help](/_installation/README.md) for information how to install the application.

## Camera support

PySpin Spinnaker Chameleon.

### Currently supported cameras

- Should install from source as an editable library.
- Go to `/api/cameras.py` and add your own camera
- go to function that gets the list of unique ids and add your new class to the list of classes that are searched through.

### Adding your own APIs fro unsupported cameras

- Inheriting from the Camera template class and redefining functions

## Opening pyMultiVideo from config file

- Get the config file from the `/experiments` folder and use that as the input to the `--config` argument

`--config /path/to/config.json` argument and example usage. for example: `C:/Users/alifa/Anaconda3/envs/flir/python.exe "c:/Users/alifa/OneDrive - Nexus365/Documents/Video Aquisition Application/pyMultiVideo/code/pyMultiVideo_GUI.pyw" --config "C:\Users\alifa\OneDrive - Nexus365\Documents\Video Aquisition Application\pyMultiVideo\code\experiments\fps-3.json"`

