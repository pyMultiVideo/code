"""Example of how to launch the pyMultiVideo application from a python subprocess with a configuration that you would like to use."""

import subprocess, sys
from pathlib import Path
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pyMV code folder.


config_data = {
    "application_config": {
        "gui_config": {
            "camera_update_rate": 20,  # Rate at which to get new images from camera buffer.
            "camera_updates_per_display_update": 1,  # How often images are fetched from camera per update of video display.
            "font_size": 12,  # Font size to use in GUI.
        },
        "ffmpeg_config": {
            "crf": 23,  # Controls video quality vs file size, range [1 - 51], lower is higher quality and larger files.
            "encoding_speed": "slow",  # Controls encoding speed vs file size, value values ["fast", "medium", "slow"]
            "compression_standard": "h264",  # ["h265" , "h264"]
        },
        "paths_config": {
            "ROOT": ROOT,
            "camera_dir": os.path.join(ROOT, "config"),
            "encoder_dir": os.path.join(ROOT, "config"),
            "data_dir": os.path.join(ROOT, "data"),
            "config_dir": os.path.join(ROOT, "config"),
            "icons_dir": os.path.join(ROOT, "GUI", "icons"),
        },
        "default_camera_config": {
            "name": None,
            "fps": 60,
            "downsampling_factor": 1,
            "exposure_time": 15000,
            "gain": 0,
            "pixel_format": "Mono8",
        },
    },
    "experiment_config": {
        "data_dir": Path(".") / "data",
        "n_cameras": 1,
        "n_columns": 1,
        "cameras": [{"label": "16401324-spinnaker", "subject_id": f"recording"}],
    },
    "camera_config": [
        {
            "name": None,
            "unique_id": "16401324-spinnaker",
            "fps": 60,
            "exposure_time": 10000,  # Ensure exposure time is between 1000 and 100000 microseconds
            "gain": 0,
            "pixel_format": "Mono8",
            "downsampling_factor": 2,
        }
    ],
    "record-on-startup": True,
    "close_after": "00:10",
}
# Convert test_config to a JSON formatted string
config_data = json.loads(json.dumps(config_data, default=str))

# Construct the command as a list of arguments
command = [
    sys.executable,  # Python executable
    Path(".") / "pyMultiVideo_GUI.pyw",  # Path to GUI
    # Test options specified
    "--experiment-config",
    json.dumps(json.dumps(config_data["experiment_config"])),  # Config file passed as JSON formatted string
    "--camera-config",
    json.dumps(json.dumps(config_data["camera_config"])),  # Config file passed as JSON formatted string
    "--application-config",
    json.dumps(json.dumps(config_data["application_config"])),  # Config file passed as JSON formatted string
    "--record-on-startup",
    config_data["record-on-startup"],  # Application records on startup
    "--close-after",
    config_data["close_after"],  # Time after which the application closes
]

# Join the list into a single string with spaces between each element
command = " ".join(map(str, command))
print(command)
# Start the process
process = subprocess.Popen(
    command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)  # Ensure it runs in a new process group
