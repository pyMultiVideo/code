try {
    # Download the Miniconda environment
    Invoke-WebRequest https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -OutFile miniconda.exe
    # Install the downloaded file.
    Start-Process -FilePath ".\miniconda.exe" -ArgumentList "/S" -Wait
    # Remove the installer 
    Remove-Item miniconda.exe
} catch {
    Write-Error "An error occurred during the installation process."
}

try {
    # Create a new environment in Miniconda called pyMultiCam_env
    & "$env:USERPROFILE\miniconda3\Scripts\conda.exe" create -n pyMultiCam_env python=3.10 -y
}
catch {
    Write-Error "An Error occured whilst trying to make the virtual environment for pyMulitCam."
}

try {
    # Install the requirements.txt in the pyMultiCam_env
    & "$env:USERPROFILE\miniconda3\Scripts\conda.exe" run -n pyMultiCam_env pip install -r requirements.txt
} catch {
    Write-Error "An error occurred while installing the requirements."
}