# Script to activate the miniconda environment 
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Run the pyMultiCamera main GUI launcher. 
& "C:/Program Files/miniconda3/envs/pyMultiCam_env/python.exe" "$scriptPath/pyMultiVideo_GUI.pyw"


