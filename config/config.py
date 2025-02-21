import os
import shutil

# GUI settings ------------------------------------------------------------------------

__version__ = "1.0.5.3"

gui_config = {
    "display_update_rate": 30,  # Rate at which function to update video displays is called (Hz).
    "fetch_image_rate": 60,  # Rate at which the function that fetches images from cameras is called (Hz).
}

# Default FFMPEG config -----------------------------------------------------------------------

ffmpeg_config = {
    "pxl_fmt": {"Mono8": "yuv420p", "Mono16": "?"},
    "crf": 23, # between 1 - 51
    "encoding_speed": "slow", #["fast", "medium", "slow"]
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
    "assets_dir": os.path.join(ROOT, "assets", "icons"),
}

# Default Camera Settings -------------------------------------------------------------

default_camera_config = {
    "fps": "60",
    "downsampling_factor": 1,
    "exposure_time": 15000,
    "gain": 0,
}
