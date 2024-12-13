########################################################################################
# Download
########################################################################################
Write-Output 'Downloading PySpin'

$SDKPathDir = "$PSScriptRoot\SDK\"
$spinnakerSDKpath = "https://flir.netx.net/file/asset/59493/original/attachment"

if (-Not (Test-Path -Path $SDKPathDir)) {
    New-Item -ItemType Directory -Path $SDKPathDir
}


try {
    Invoke-WebRequest -Uri $spinnakerSDKpath -OutFile "$SDKPathDir\spinnakerSDK.zip"
} catch {
    Write-Host "An error occured: $_" -ForegroundColor Red
}


########################################################################################
# Extract
########################################################################################
Write-Output 'Extracting PySpin'


$zipPath = "$SDKPathDir\spinnakerSDK.zip"
$extractPath = "$SDKPathDir\spinnakerSDK\"

if (-Not (Test-Path -Path $extractPath)) {
    New-Item -ItemType Directory -Path $extractPath
}

try {
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    Write-Host "Extraction complete." -ForegroundColor Green
} catch {
    Write-Host "An error occurred during extraction: $_" -ForegroundColor Red
}

########################################################################################
# Install
########################################################################################
Write-Output 'Installing PySpin'

$envPath = "$env:USERPROFILE\miniconda3\envs\pyMultiCam_env"

$whl = "$SDKPathDir\spinnakerSDK\spinnaker_python-4.0.0.116-cp310-cp310-win_amd64.whl"

try {
    # Activate the Conda environment
    conda activate $envPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to activate Conda environment"
    }

    # Install the .whl file using pip
    pip install $whl
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install the .whl file using pip"
    }

    Write-Output "Installation completed successfully."
} catch {
    Write-Error "An error occurred: $_"
}