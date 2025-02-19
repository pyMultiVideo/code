import os
import shutil

# GUI settings ------------------------------------------------------------------------

__version__ = "1.0.5.3"

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
        "pxl_fmt": {"Mono8": "yuv420p", "Mono16": "yuv420p"},
    },
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
    "pxl_fmt": "Mono8",
    "downsample_factor": 1,
    "exposure_time": 15000,
    "gain": 0,
}
