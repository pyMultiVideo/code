import importlib
import pkgutil
import sys
import os
import json
import subprocess
from typing import Dict, Any
from dataclasses import dataclass

from config.config import ffmpeg_config

# Custom data classes -----------------------------------------------------------------


@dataclass
class CameraSetupConfig:
    """
    Data class to hold the configuration of a single user set camera settings
    """

    label: str
    subject_id: str


@dataclass
class ExperimentConfig:
    """
    Data to hold the use set conPfiguPration of a single experiment
    """

    data_dir: str
    encoder: str
    num_cameras: int
    grid_layout: bool
    cameras: list[CameraSetupConfig]


@dataclass
class CameraSettingsConfig:
    """
    Data class to hold the camera settings for a single camera
    """

    name: str
    unique_id: str
    fps: str
    pxl_fmt: str
    downsample_factor: int


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
    cbox.setCurrentIndex(i)


def get_valid_ffmpeg_encoders() -> list:
    """Return list of valid encoders given GPU availibility."""
    # Check if GPU is available.
    try:
        subprocess.check_output("nvidia-smi")
        print("Nvidia GPU detected")
        GPU_AVAIALABLE = True
    except Exception:
        print("No Nvidia GPU available")
        GPU_AVAIALABLE = False
    # Get all corresponding encoders.
    encoder_dict_keys = ffmpeg_config["output"]["encoder"].keys()
    valid_encoders_keys = []
    for key in encoder_dict_keys:
        if "CPU" in key:
            valid_encoders_keys.append(key)
        elif "GPU" in key and GPU_AVAIALABLE:
            valid_encoders_keys.append(key)
    return valid_encoders_keys


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

    # If running in a frozen environment (e.g., PyInstaller), include the frozen modules
    if getattr(sys, "frozen", False):
        frozen_path = os.path.join(sys._MEIPASS, package_name)
        if os.path.exists(frozen_path):
            for _, module_name, _ in pkgutil.iter_modules([frozen_path]):
                if module_name not in modules:
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
    try:
        if getattr(sys, "frozen", False):
            sys.path.append(os.path.join(sys._MEIPASS, "code", "camera_api"))
        modules = get_modules_in_package("camera_api")
    except ModuleNotFoundError:
        if getattr(sys, "frozen", False):
            frozen_path = os.path.join(sys._MEIPASS, "camera_api")
            if os.path.exists(frozen_path):
                modules = [name for _, name, _ in pkgutil.iter_modules([frozen_path])]
            else:
                modules = []
        else:
            raise

    camera_list = []
    for module in modules:
        # Get the module
        camera_module = importlib.import_module(f"camera_api.{module}")
        # Get the list of cameras as a string.
        camera_list.extend(camera_module.list_available_cameras())

    return camera_list


def init_camera_api(_id, CameraSettingsConfig=None):
    """Go through each"""
    # Split the camera unique_id into its api and its serial_no
    serial_no, module_name = _id.split("-")

    camera_module = importlib.import_module(f"camera_api.{module_name}")

    return camera_module.initialise_by_id(_id=_id, CameraSettingsConfig=CameraSettingsConfig)


def load_saved_setups(camera_data) -> list[CameraSettingsConfig]:
    """Function to load the saved setups from the database as a list of Setup objects"""
    setups_from_database = []
    for cam in camera_data:
        setups_from_database.append(
            CameraSettingsConfig(
                name=cam["name"],
                unique_id=cam["unique_id"],
                fps=cam["fps"],
                pxl_fmt=cam["pxl_fmt"],
                downsample_factor=cam["downsample_factor"],
            )
        )
    return setups_from_database
