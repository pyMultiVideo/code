# This script simply activate the correct virtual environment and lauches the application. 

# Script to activate the miniconda environment 
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Run the pyMultiVideo% main GUI launcher. 
& "C:/Program Files/miniconda3/envs/pyMultiCam_env/python.exe" "$scriptPath/pyMultiVideo_GUI.pyw"
# convert to windows syntax
# add a option to downloads to skip redownloading the pyspin sdk


