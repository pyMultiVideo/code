# Script to check if Miniconda is added to PATH

# Function to check PATH for Miniconda
function Test-MinicondaInPath {
    param (
        [string]$PathVariable
    )

    # Look for common Miniconda directories in PATH
    $minicondaPaths = @(
        "Miniconda3",
        "Miniconda",
        "condabin"
    )

    foreach ($minicondaPath in $minicondaPaths) {
        if ($PathVariable -match [regex]::Escape($minicondaPath)) {
            return $true
        }
    }

    return $false
}

# Get User PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)

# Get System PATH
$systemPath = [Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)

# Check if Miniconda is in User PATH
$userHasMiniconda = Test-MinicondaInPath -PathVariable $userPath

# Check if Miniconda is in System PATH
$systemHasMiniconda = Test-MinicondaInPath -PathVariable $systemPath

# Output the results
if ($userHasMiniconda -or $systemHasMiniconda) {
    Write-Host "Miniconda is present in the PATH environment variable." -ForegroundColor Green
    if ($userHasMiniconda) {
        Write-Host "Found in User PATH." -ForegroundColor Cyan
    }
    if ($systemHasMiniconda) {
        Write-Host "Found in System PATH." -ForegroundColor Cyan
    }
} else {
    Write-Host "Miniconda is NOT present in the PATH environment variable." -ForegroundColor Red
}
