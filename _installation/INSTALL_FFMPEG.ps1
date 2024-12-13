# This code is adapted from the following discussion: https://gist.github.com/AnjanaMadu/5f9689e9572492a50089f4a74b9b8de5

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (!$isAdmin) {
    Write-Host "Please run this script as administrator."
    exit
}

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "ffmpeg is already installed."
    exit
}

Write-Host "Downloading ffmpeg..."
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "ffmpeg.zip"

Write-Host "Extracting..."
# Use the native Windows zip command
Expand-Archive -Path "ffmpeg.zip" -DestinationPath "C:\"

$ffmpegFolder = Get-ChildItem -Path "C:\" -Filter "ffmpeg-*" -Directory
Rename-Item -Path $ffmpegFolder.FullName -NewName "ffmpeg"

Write-Host "Adding ffmpeg to PATH..."
$envPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
[Environment]::SetEnvironmentVariable("PATH", $envPath + ";C:\ffmpeg\bin", "Machine")

Remove-Item ffmpeg.zip

Write-Host "ffmpeg is installed. Following commands are available: ffmpeg, ffplay, ffprobe"

