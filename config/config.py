import os
import shutil

# GUI settings ------------------------------------------------------------------------

__version__ = "1.0.5.3"

gui_config = {
    # This has no impact of the rate at which the buffer is emptied
    "update_display_rate": 30,  # (Hz) the rate at which the function for updating the display is called.
    "fetch_image_rate": 60,  # (Hz) the rate at which the function which is called to fetch images from the camera.
    # The default directory for the data from the application to be stored.
    "data_folder_directory": "data",
}

# FFMPEG config -----------------------------------------------------------------------

ffmpeg_config = {
    "input": {},
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
    raise FileNotFoundError("FFmpeg binary not found. Please install FFmpeg and ensure it's in your PATH.")
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
