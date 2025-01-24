<#
File for installing the miniconda environment 
- This can be done for a local user or globally (Globally this required administrator privileges) for all account on the machine.
#>

# Check if the script is running with administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Output "You must run this script as an administrator."
    exit
}

$minicondaPath = [System.Environment]::GetFolderPath('ProgramFiles')

Write-Output "Checking if miniconda is installed..."
# Check if the miniconda installation exists in the path
$minicondaOutput = & "$minicondaPath\miniconda3\Scripts\conda.exe" --version    
if ($minicondaOutput) {
    Write-Output "Miniconda is already installed in $minicondaPath."
    # exit
} else {
    Write-Output "Miniconda is not installed in $minicondaPath."
}


if ($minicondaOutput) {
    Write-Output "Skipping the downloading and installation of the miniconda installation "
    } else {
        try {
            Write-Output "Downloading the Miniconda installer..."
            # Download the Miniconda environment
            Invoke-WebRequest https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -OutFile miniconda.exe
        } catch {
            Write-Error "An error occurred while downloading the Miniconda installer."
        }
        
        # Set the configuration for which miniconda will be installed. 
        try {
            if ($installAllUsersInput -eq "Y") {
                $miniconda_argument_list = @("/InstallationType=AllUsers", "/S", "/D=$minicondaPath\miniconda3")
            } else {
                $miniconda_argument_list = @("/S")
            }
            Write-Output "Installing the miniconda applications with config: $miniconda_argument_list"
            # Installing the miniconda file
            Start-Process -FilePath ".\miniconda.exe" -ArgumentList $miniconda_argument_list -Wait

            # Remove the miniconda installation 
            Remove-Item -Path ".\miniconda.exe" -Force
        } catch {
            Write-Error "An error occurred during the Miniconda installation process."
        }
    }   

# Create a conda environment in the miniconda path that has been installe.
try {
    Write-Output "Creating pyMultiCam_env for running the applications"
    # Create a new environment in Miniconda called pyMultiCam_env
    & "$minicondaPath\miniconda3\Scripts\conda.exe" create -n pyMultiCam_env python=3.10 -y
}
catch {
    Write-Error "An Error occured whilst trying to make the virtual environment for pyMulitCam."
}

try {
    Write-Output  "Installing the requirements.txt in the pyMultiCam_env"
    & "$minicondaPath\miniconda3\Scripts\conda.exe" run -n pyMultiCam_env pip install -r "../requirements.txt"
} catch {
    Write-Error "An error occurred while installing the requirements."
}


Write-Host "Adding miniconda to PATH..."
$envPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$newPath = $envPath + ";C:\Program Files\miniconda3;C:\Program Files\miniconda3\Scripts;C:\Program Files\miniconda3\;C:\Program Files\miniconda3\Library\bin"
# C:\Program Files\miniconda3\Scripts;C:\Program Files\miniconda3\condabin
[Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")

Write-Output "Finish running miniconda installation script. miniconda has been installed at $minicondaPath"

# Restart powershell after adding miniconda to path
Get-Process -Id $PID |
        Select-Object -ExpandProperty Path |
            ForEach-Object {
                Invoke-Command { & "$_" } -NoNewScope
                }