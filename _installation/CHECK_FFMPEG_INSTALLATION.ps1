# CHECK_FFMPEG_INSTALLATION.ps1

# Check if ffmpeg is installed
$ffmpegPath = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Path

if ($ffmpegPath) {
    Write-Output "ffmpeg is installed at: $ffmpegPath"
} else {
    Write-Output "ffmpeg is not installed."
}