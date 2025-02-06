# This script simply activate the correct virtual environment and lauches the application. 

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
& "C:/Program Files/miniconda3/envs/pyMultiCam_env/python.exe" "$scriptPath/pyMultiVideo_GUI.pyw"
