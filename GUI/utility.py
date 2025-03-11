import importlib
import pkgutil
import os
import json
import subprocess
from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtWidgets import QComboBox

from config.config import default_camera_config

# Custom data classes -----------------------------------------------------------------


@dataclass
class CameraWidgetConfig:
    """Represents the configuration of a Camera_widget in the VideoCaptureTab."""

    label: str
    subject_id: str


@dataclass
class ExperimentConfig:
    """Represents the configuration of the whole VideoCaptureTab."""

    data_dir: str
    n_cameras: int
    n_columns: int
    cameras: list[CameraWidgetConfig]


@dataclass
class CameraSettingsConfig:
    """Represents the CamerasTab settings for one camera"""

    name: str
    unique_id: str
    fps: int
    exposure_time: float
    gain: float
    pixel_format: str
    downsampling_factor: int


# ffmpeg encoding maps ----------------------------------------------------------------------


def gpu_available(VERBOSE=False) -> list:
    """Return list of valid encoders given GPU availibility."""
    # Check if GPU is available.
    try:
        subprocess.check_output("nvidia-smi")
        if VERBOSE:
            print("Nvidia GPU detected")
        return True
    except Exception:
        if VERBOSE:
            print("No Nvidia GPU available")
        return False


# Specify the FFMPEG encoders available
if gpu_available():
    ffmpeg_encoder_map = {
        "h264": "h264_nvenc",
        "h265": "hevc_nvenc",
    }
else:
    ffmpeg_encoder_map = {
        "h264": "libx264",
        "h265": "libx265",
    }


def validate_ffmpeg_path(ffmpeg_path):
    """Validate the provided ffmpeg path."""
    if type(ffmpeg_path) is type(None):
        return False
    if not os.path.isfile(ffmpeg_path):
        raise FileNotFoundError(f"ffmpeg executable not found at {ffmpeg_path}")

    try:
        result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError(f"Invalid ffmpeg executable at {ffmpeg_path}")
    except Exception as e:
        raise ValueError(f"Error validating ffmpeg path: {e}")

    return True


# Utility functions -------------------------------------------------------------------


def load_camera_dict(camera_config_path: str) -> Dict[str, Any]:
    """
    Load camera configuration data from a JSON file.

    :return: A dictionary containing the camera configuration data.
    """
    try:
        if not os.path.exists(camera_config_path):
            with open(camera_config_path, "w") as file:
                json.dump({}, file)
        with open(camera_config_path, "r") as file:
            camera_dict = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Camera configuration file not found at {camera_config_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {camera_config_path}")

    return camera_dict
