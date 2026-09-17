"""Example of how to launch the pyMultiVideo application using subprocess with a config specificed"""

import subprocess, sys
from pathlib import Path
import json, os

ROOT = Path(__file__).resolve().parent.parent  # pyMV code folder.

config_data = {
    "application_config": {
        "gui_config": {
            "camera_update_rate": 30,  # Rate at which to get new images from camera buffer.
            "camera_updates_per_display_update": 1,  # How often images are fetched from camera per update of video display.
            "font_size": 12,  # Font size to use in GUI.
        },
        "ffmpeg_config": {
            "crf": 28,  # Controls video quality vs file size, range [1 - 51], lower is higher quality and larger files.
            "encoding_speed": "fast",  # Controls encoding speed vs file size, value values ["fast", "medium", "slow"]
            "compression_standard": "h264",  # ["h265" , "h264"]
        },
        "paths_config": {
            "ROOT": ROOT,
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
            "pixel_format": "mono8",
        },
    },
    "experiment_config": {
        "data_dir": ROOT / "data",
        "n_cameras": 1,
        "n_columns": 1,
        "cameras": [{"label": "21013411-spinnaker", "subject_id": f"recording"}],
    },
    "camera_config": [
        {
            "name": None,
            "unique_id": "21013411-spinnaker",
            "fps": "60",
            "exposure_time": 10111,
            "gain": 0,
            "pixel_format": "mono8",
            "external_trigger": False,
            "downsampling_factor": 1,
        },
    ],
    "record-on-startup": True,  # Start recording immediately when the GUI is launched.
    "close_after": 10,  # Close the GUI after 10 seconds.
}
# Convert test_config to a JSON formatted string
config_data = json.loads(json.dumps(config_data, default=str))

# Construct the command as a list of arguments
command = [
    sys.executable,
    ROOT / "pyMultiVideo_GUI.pyw",
    "--experiment-config",
    json.dumps(config_data["experiment_config"]),
    "--camera-config",
    json.dumps(config_data["camera_config"]),
    "--application-config",
    json.dumps(config_data["application_config"]),
    "--record-on-startup",
    config_data["record-on-startup"],
    "--close-after",
    config_data["close_after"],
]

command = [str(argument) for argument in command]

# Start the process
process = subprocess.Popen(
    command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)  # Ensure it runs in a new process group
