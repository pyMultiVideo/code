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


# Utility functions -------------------------------------------------------------------


def cbox_update_options(cbox, options, used_cameras_labels, selected):
    """Update the options available in a qcombobox without changing the selection."""
    available_options = sorted(list(set(options) - set(used_cameras_labels)), key=str.lower)
    # get the current test from the combobox
    selected = cbox.currentText()

    if selected:
        available_options = sorted(list(set([selected] + available_options)), key=str.lower)
        i = available_options.index(selected)
    else:  # cbox is currently empty.
        i = 0
        pass
    cbox.clear()
    cbox.addItems(available_options)
    cbox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)  # Adjust size to fit contents
    cbox.setCurrentIndex(i)


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


def get_modules_in_package(package_name):
    """
    Returns a list of all modules in a given package.

    :param package_name: The name of the package.
    :return: List of module names.
    """
    package = importlib.import_module(package_name)
    package_path = package.__path__  # Get the package's path

    modules = []
    for _, module_name, _ in pkgutil.iter_modules(package_path):
        modules.append(module_name)

    return modules


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


def find_all_cameras() -> list[str]:
    """Get a list of unique camera IDs for all the different types of cameras connected to the machine."""
    # for each module in the camera class, run the get unique ids function

    modules = get_modules_in_package("camera_api")

    camera_list = []
    for module in modules:
        # Get the module
        camera_module = importlib.import_module(f"camera_api.{module}")
        # Get the list of cameras as a string.
        camera_list.extend(camera_module.list_available_cameras())

    return camera_list


def init_camera_api_from_module(settings: CameraSettingsConfig):
    """Initialise a camera API object given the camera ID and any camera settings."""
    _, module_name = settings.unique_id.split("-")
    camera_module = importlib.import_module(f"camera_api.{module_name}")
    return camera_module.initialise_camera_api(CameraSettingsConfig=settings)


def load_saved_setups(camera_data) -> list[CameraSettingsConfig]:
    """Load camera settings. If there are none, replace them with default values."""
    saved_camera_settings = []
    for cam in camera_data:
        saved_camera_settings.append(
            CameraSettingsConfig(
                name=cam.get("name", None),
                unique_id=cam.get("unique_id"),
                fps=cam.get("fps", default_camera_config["fps"]),
                exposure_time=cam.get("exposure_time", default_camera_config["exposure_time"]),
                gain=cam.get("gain", default_camera_config["gain"]),
                pixel_format=cam.get("pixel_format", default_camera_config["pixel_format"]),
                downsampling_factor=cam.get("downsampling_factor", default_camera_config["downsampling_factor"]),
            )
        )
    return saved_camera_settings
