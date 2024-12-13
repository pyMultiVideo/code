# Notes on how to install this application

## Batch file for installation of the application dependancies

There is a file that you can run to install these things. The things described below for easy installation.
You can do this yourself as well.

## Spinnaker SDK

Get the Spinnaker SDK from their [website](https://www.teledynevisionsolutions.com/products/spinnaker-sdk/?model=Spinnaker%20SDK&vertical=machine%20vision&segment=iis). A login is required to download this.
*It has only be tested using python 3.10*

The Spinnaker SDK has some specific requirements that mean installing the application has some specific requirements

1. The latest version of python that the SDK supports is `python==3.10`
2. The SDK does not support numpy version 2 or above.
For these reasons I would suggest that you use create a different virtural environment specifically for running this application (I used [anaconda](https://www.anaconda.com/) to do this)

## FFMPEG Installation

The encoder in this application uses ffmpeg so you need ffmpeg installed as well as the ffmpeg api ([`pip install ffmpeg-python`](https://pypi.org/project/ffmpeg-python/))

## Supporting USB cameras

To support USB cameras :

- `cv2_enumerate_cameras` library is used for listing the USB cameras that are connected to the computer
- `opencv-python` library is used to get the images from the USB camera

## Other dependancies

The GUI is made using the QT framework

- `PyQt6`
- `pyqtgraph`

## Known Bugs

> Check the ErrorLog.txt if it is generated for error messages from python.

- Installation is hard because
  - ffmpeg-python is not automatically installed from the requirements file
- Fixes required:
  - Should be verticallly scaling hot horizontally scaling
  - Handle with error message what happens when recording does not start ( because the error message that is being give)
  - Pixel formatting is not correct for the camera recording pipe to work properly.
    - yuv420 is not in the list of file formats so it has to be yuv420p. (Think about how to implement this)
    More generally there should be ways of showing these error messages to the user so they can debug...
  - need to rename the to the release name
  - Automatically running the pyw file from the file explorer opens it in 3.11**
- Flickering from the cameras in the lab i am not sure why though...
