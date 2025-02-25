import os
import shutil

# GUI settings ------------------------------------------------------------------------

__version__ = "1.0.0"

gui_config = {
    "camera_update_rate": 30,  # Rate at which to get new images from camera buffer.
}

# Default FFMPEG config -----------------------------------------------------------------------

ffmpeg_config = {
    # "pxl_fmt": {"Mono8": "yuv420p", "Mono16": "?"},
    "crf": 23,  # between 1 - 51 https://slhck.info/video/2017/02/24/crf-guide.html
    "encoding_speed": "slow",  # ["fast", "medium", "slow"]
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
