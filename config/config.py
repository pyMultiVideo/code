import os
import shutil

# GUI settings ------------------------------------------------------------------------

__version__ = "1.0.0"

gui_config = {
    "camera_update_rate": 30,  # Rate at which to get new images from camera buffer.
}

# Default FFMPEG config -----------------------------------------------------------------------

ffmpeg_config = {
    "crf": 23,  # Controls video quality vs file size, range [1 - 51], lower is higher quality and larger files.
    "encoding_speed": "slow",  # Controls encoding speed vs file size, value values ["fast", "medium", "slow"]
    "compression_standard": "h264",  # ["h265" , "h264"]
}

# Paths -------------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pyMV code folder.

paths_config = {
    "ROOT": ROOT,
    "FFMPEG": shutil.which("ffmpeg"),
    "camera_dir": os.path.join(ROOT, "config"),
    "encoder_dir": os.path.join(ROOT, "config"),
    "data_dir": os.path.join(ROOT, "data"),
    "config_dir": os.path.join(ROOT, "config"),
    "assets_dir": os.path.join(ROOT, "GUI", "icons"),
}

# Default Camera Settings -------------------------------------------------------------

default_camera_config = {
    "fps": "60",
    "downsampling_factor": 1,
    "exposure_time": 15000,
    "gain": 0,
}
