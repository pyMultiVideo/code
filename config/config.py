import os
import shutil
from PyQt6.QtWidgets import QMessageBox, QApplication
import sys

# GUI settings ------------------------------------------------------------------------

__version__ = "1.0.6"

gui_config = {
    "display_update_rate": 30,  # Rate at which function to update video displays is called (Hz).
    "fetch_image_rate": 60,  # Rate at which the function that fetches images from cameras is called (Hz).
}

# FFMPEG config -----------------------------------------------------------------------

ffmpeg_config = {
    "output": {
        # Encoders available to ffmpeg
        # {'GUI Name: ffmpeg_encoder name'}
        "encoder": {
            "GPU (H264)": "h264_nvenc",
            "GPU (H265)": "hevc_nvenc",
            "CPU (H264)": "libx264",
            "CPU (H265)": "libx265",
        },
        "pxl_fmt": {"yuv420p": "yuv420p"},
    },
}

# Paths -------------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pyMV code folder.

ffmpeg_path = shutil.which("ffmpeg")  # The location where the ffmpeg.exe is located.
if ffmpeg_path is None:
    app = QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText("FFmpeg binary not found. Please install FFmpeg and ensure it's in your PATH.")
    msg.setWindowTitle("FFmpeg Not Found")
    msg.exec()
    sys.exit("FFmpeg binary not found. Please install FFmpeg and ensure it's in your PATH.")
else:
    print(f"FFmpeg found at: {ffmpeg_path}")

paths_config = {
    "ROOT": ROOT,
    "FFMPEG": ffmpeg_path,
    "camera_dir": os.path.join(ROOT, "config"),
    "encoder_dir": os.path.join(ROOT, "config"),
    "data_dir": os.path.join(ROOT, "data"),
    "config_dir": os.path.join(ROOT, "config"),
    "assets_dir": os.path.join(ROOT, "assets", "icons"),
}
