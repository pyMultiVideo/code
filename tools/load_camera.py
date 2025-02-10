import logging
import importlib
import pkgutil
import sys
import os
import json
from typing import Dict, Any
import subprocess

from . import CameraSettingsConfig

logging.basicConfig(level=logging.INFO)


# from GUI import ViewfinderWidget
def cbox_update_options(cbox, options, used_cameras_labels, selected):
    """Update the options available in a qcombobox without changing the selection."""
    available_options = sorted(
        list(set(options) - set(used_cameras_labels)), key=str.lower
    )
    # get the current test from the combobox
    selected = cbox.currentText()

    if selected:
        available_options = sorted(
            list(set([selected] + available_options)), key=str.lower
        )
        i = available_options.index(selected)
    else:  # cbox is currently empty.
        i = 0
        pass
    cbox.clear()
    cbox.addItems(available_options)
    cbox.setCurrentIndex(i)


def gpu_available() -> bool:
    """Check if a GPU is available on the system running the program"""
    try:
        subprocess.check_output("nvidia-smi")
        print("Nvidia GPU detected!")
        return True
    except Exception:  # this command not being found can raise quite a few different errors depending on the configuration
        print("No Nvidia GPU in system!")
        return False


def valid_ffmpeg_encoders(GPU_AVAIALABLE: bool, encoder_dict_keys) -> list:
    """Return list of valid encoders depending on if GPU is available"""
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
        raise FileNotFoundError(
            f"Camera configuration file not found at {camera_config_path}"
        )
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

    return camera_module.initialise_by_id(
        _id=_id, CameraSettingsConfig=CameraSettingsConfig
    )


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


if __name__ == "__main__":
    pass
