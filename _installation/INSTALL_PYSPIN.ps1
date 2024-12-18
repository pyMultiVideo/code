########################################################################################
# Download
########################################################################################
Write-Output 'Downloading PySpin'
$scriptDir = Get-Location
$SDKPathDir = "$scriptDir\SDK\"
$spinnakerSDKpath = "https://flir.netx.net/file/asset/59493/original/attachment"

if (-Not (Test-Path -Path $SDKPathDir)) {
    New-Item -ItemType Directory -Path $SDKPathDir
}


try {
    if (Test-Path -Path $SDKPathDir) {
        Write-Output "Removing any previous contents formt the \SDK\ folder"
        Remove-Item -Path "$SDKPathDir\*" -Recurse -Force
    }
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

$installScope = Read-Host "Would you like to install this [L]ocally or [G]lobally? (L/G)"

# Check if they are administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

# If you are not an administrator raise an error
if ($installScope -eq "g" -and -not $isAdmin) {
    throw "You must be an administrator to install globally."
# Ig you have a global scope, get the correct path to the pyMultiCam_env
} elseif ($installScope -eq "g") {
    $systemPath = [System.Environment]::GetFolderPath('ProgramFiles') 
    $envPath = "$systemPath\miniconda3\envs\pyMultiCam_env"
} elseif ($installScope -eq "l") {
    $envPath = "$env:USERPROFILE\miniconda3\envs\pyMultiCam_env"
} else {
    throw "Invalid input. Please enter 'local' or 'global'."
}

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