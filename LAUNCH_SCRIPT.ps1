# Script to activate the miniconda environment 
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Run the pyMultiCamera main GUI launcher. 
& $env:USERPROFILE/miniconda3/envs/pyMultiCam_env/python.exe "$scriptPath/pyMultiVideo_GUI.pyw"


