from pathlib import Path
import os
from datetime import datetime
import json

import sys
from pathlib import Path

# Add the parent directory to sys.path for proper imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config import paths_config, default_camera_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pyMV code folder.

### Start of helper functions ###


def get_camera_unique_ids():
    # config/camera_configs.json
    camera_configs = Path(".") / "config" / "camera_configs.json"
    with open(camera_configs.resolve(), "r") as file:
        data = json.load(file)
    return [camera["unique_id"] for camera in data]


def save_config_file(test_config_dir, test_config):
    """Helper function to save test configuration to a JSON file."""
    test_config_file = test_config_dir / "test_config.json"
    with open(test_config_file, "w") as f:
        json.dump(test_config, f, indent=4)


def create_experiment_config(data_dir, n_cameras):

    camera_unique_ids = get_camera_unique_ids()
    config = {
        "data_dir": str(data_dir),
        "n_cameras": n_cameras,
        "n_columns": 1,
        "cameras": [{"label": camera_unique_ids[i], "subject_id": f"recording-{i+1}"} for i in range(n_cameras)],
    }
    return config


def create_camera_config(n_cameras, fps, downsampling_factor):
    camera_unique_ids = get_camera_unique_ids()
    cameras = [
        {
            "name": None,
            "unique_id": camera_unique_ids[i],
            "fps": fps,
            "exposure_time": min(max(1000, 1000000 // fps), 100000)
            - 1000,  # Ensure exposure time is between 1000 and 100000 microseconds
            "gain": 0,
            "pixel_format": default_camera_config["pixel_format"],
            "downsampling_factor": downsampling_factor,
        }
        for i in range(n_cameras)
    ]
    return cameras


def generate_performance_test_config(
    fps, n_camera, downsampling_factor, encoding_speed, compression_standard, updates_per_display
):
    """Helper function to generate test configurations."""
    return {
        "application_config": {
            "gui_config": {
                "camera_update_rate": CAMERA_UPDATE_RATE,
                "camera_updates_per_display_update": updates_per_display,
                "font_size": 12,
            },
            "ffmpeg_config": {
                "crf": CRF,
                "encoding_speed": encoding_speed,
                "compression_standard": compression_standard,
            },
            "paths_config": paths_config,
            "default_camera_config": default_camera_config,
        },
        "experiment_config": create_experiment_config(data_dir=test_config_dir, n_cameras=n_camera),
        "camera_config": create_camera_config(n_cameras=n_camera, fps=fps, downsampling_factor=downsampling_factor),
        "record-on-startup": True,
        "close_after": testing_parameters["close_after"],
    }


### End of Helper Functions ###


subject_ids = [f"subject_{i}" for i in range(len(get_camera_unique_ids()))]

# The parameters which are varied
testing_parameters = {
    # Folder test name
    "test_name": f"test-photo-1",
    # "test_name": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    # Recording_length (s)
    "close_after": "02:00",  # MM:SS
    # Config
    "n_cameras": list(range(1, len(get_camera_unique_ids()) + 1)),
    "downsample_range": [1, 2, 4],
    "fps_range": [30, 60, 90, 120],
    # GUI config
    "camera_update_range": [10, 20, 40],
    "camera_updates_per_display_update": [1, 2, 4],
    # FFMPEG
    "crf_range": [1, 23, 51],
    "encoding_speed_options": ["fast", "medium", "slow"],
    "compression_standard": ["h264", "h265"],
}

# Setup data directors for test to take place in
# 1. Create directory
test_directory = Path(".") / "data" / testing_parameters["test_name"]
try:
    test_directory.mkdir(parents=True, exist_ok=True)
    print(f"Directory created at: {test_directory}")
except Exception as e:
    print(f"Failed to create directory: {e}")
# 2. Save the testing parameters
# Save the testing parameters to a JSON file
parameters_file = test_directory / "testing_parameters.json"
try:
    with open(parameters_file, "w") as f:
        json.dump(testing_parameters, f, indent=4)
    print(f"Testing parameters saved to: {parameters_file}")
except Exception as e:
    print(f"Failed to save testing parameters: {e}")

DOWNSAMPLING_FACTOR = 2
CAMERA_UPDATE_RATE = 20
UPDATES_PER_DISPLAY = 1
CRF = 23
ENCODERING_SPEED = "fast"
COMPRESSION_STANDARD = "h265"
N_CAMERAS = 4
FPS = 60


# Generate config files for fixed cameras and FPS
for fps in testing_parameters["fps_range"]:
    for n_camera in testing_parameters["n_cameras"]:
        for downsampling_factor in testing_parameters["downsample_range"]:
            for encoding_speed in testing_parameters["encoding_speed_options"]:
                for compression_standard in testing_parameters["compression_standard"]:
                    for updates_per_display in testing_parameters["camera_updates_per_display_update"]:
                        config_dir = (
                            f"config_ncams_{n_camera}_downsample_{downsampling_factor}_fps_{fps}_"
                            f"update_{CAMERA_UPDATE_RATE}_upd_per_disp_{updates_per_display}_"
                            f"crf_{CRF}_speed_{encoding_speed}_comp_{compression_standard}"
                        )
                        test_config_dir = test_directory / config_dir
                        test_config_dir.mkdir(parents=True, exist_ok=True)

                        save_config_file(
                            test_config_dir,
                            test_config=generate_performance_test_config(
                                fps=fps,
                                n_camera=n_camera,
                                downsampling_factor=downsampling_factor,
                                encoding_speed=encoding_speed,
                                compression_standard=compression_standard,
                                updates_per_display=updates_per_display,
                            ),
                        )
