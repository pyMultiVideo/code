
# $env_path = "$env:USERPROFILE\anaconda3\envs\flir"
$env_path = "$env:USERPROFILE\miniconda3\envs\pyMultiCam_env"


$package = conda list -p $env_path spinnaker-python

Write-Output $package


if ($package -match "spinnaker-python") {
    Write-Output "spinnaker-python is installed in the $env_path environment."
} else {
    # Write-Output "spinnaker_python is not installed in the pyMultiCam_env environment."
    Write-Output "spinnaker-python is not installed in the $env_path environment."
    exit
}

Write-Output "Passed"