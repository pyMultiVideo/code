# How to install pyMultiVideo

## Cloning the repository

The recommended way to install this program is to clone this repository using github. If you intend on installing it for all users consider installing it in `C:/Program Files`.

To install using github: 

1. Install git bash if you havent already. 
2. Open the Git Bash powershell
3. Navigate to the folder you would like to install the repository in (using the e.g. `cd C:/Program Files/`)
4. clone the repository `git clone https://github.com/pyMultiVideo/code.git`

After this has been done, to update the repositiory: 

1. Navigate to the folder you installed pyMultiVideo `cd path/to/code/`
2. Pull changes from the repository `git pull`

## Batch file for installation of the application dependancies

To install this application you can run these powershell installation scripts.

  1. [INSTALL_MINICONDA_ADMIN.ps1](/_installation/INSTALL_MINICONDA_ADMIN.ps1)
  2. [INSTALL_PYSPIN.ps1](/_installation/INSTALL_PYSPIN.ps1).  
  3. [INSTALL_FFMPEG.ps1](/_installation/INSTALL_FFMPEG.ps1)

IMPORTANT: For the installtion to work properly, you must run the installation scripts in the directory that they are being saved in. 

You can check the requirements of the installation were met with the following scripts

  1. [CHECK_SPINNAKER_INSTALLATION.ps1](/_installation/CHECK_SPINNAKER_INSTALLATION.ps1)
  2. [CHECK_FFMPEG_INSTALLATION.ps1](/_installation/CHECK_FFMPEG_INSTALLATION.ps1)

## What the scripts do

### INSTALL_MINICONDA.ps1

This script installs a virtual environment manager called miniconda. At a high level, a virtual enviroment is a separate installation of python. This is useful for avoiding dependancies conflicts that occur between different python packages that you might want to install. For more information an article is linked [here](https://medium.com/@aminasaeed223/a-comprehensive-tutorial-on-miniconda-creating-virtual-environments-and-setting-up-with-vs-code-f98d22fac8e2).

This is useful here because the pyMultiVideo requires the following: 
1. The latest version of python that the SDK supports is `python==3.10`
2. The SDK does not support numpy version 2 or above.

The script also creates a python 3.10 virtual environment in miniconda and installs the requirements of pyMutliVideo, with the execption of the PySpin API which is installed in `INSTALL_PYSPIN.ps1`

### INSTALL_PYSPIN.ps1

Get the Spinnaker SDK from their [website](https://www.teledynevisionsolutions.com/products/spinnaker-sdk/?model=Spinnaker%20SDK&vertical=machine%20vision&segment=iis).
*It has only be tested using python 3.10*

This SDK is installed on the computer and the spinnaker python api is also downloaded, and installed into the miniconda virtual environment. 

### INSTALL_FFMPEG

The encoder in this application uses ffmpeg so you need ffmpeg installed (by simply running [this](/_installation/CHECK_FFMPEG_INSTALLATION.ps1) script.) as well as the ffmpeg api ([`pip install ffmpeg-python`](https://pypi.org/project/ffmpeg-python/))

### Supporting USB cameras

To support USB cameras :

- `cv2_enumerate_cameras` library is used for listing the USB cameras that are connected to the computer
- `opencv-python` library is used to get the images from the USB camera

### Other dependancies

- `PyQt6` (Main GUI)
- `pyqtgraph` (for displaying images to GUI)

