"""Camera management and validation module.

This module provides:
- CameraManager: A class for managing camera API instances across the GUI.
- get_camera_ids(): Function to discover all connected cameras from camera_api modules
- Validation of camera_api modules to ensure they meet package requirements
"""

import os
import importlib
import pkgutil

from camera_api.generic_camera import GenericCamera

# Validation logic for camera_api modules -------------------------------------------------------


def _validate_camera_modules():
    """Validate that all camera API modules in the camera_api package have required functions and classes."""
    package = importlib.import_module("camera_api")
    api_directory = package.__path__[0]

    # Loop through all files in the directory
    for file_name in os.listdir(api_directory):
        if file_name.endswith(".py") and file_name != "generic_camera.py":
            module_name = file_name[:-3]
            try:
                # Import the module
                module = importlib.import_module(f"camera_api.{module_name}")
            except ModuleNotFoundError:
                continue

            # Check if the expected functions and classes exist in every python module in the camera package
            if hasattr(module, "list_available_cameras") is False:
                print(
                    f"Error: {module} does not have the function 'list_available_cameras. \
                    This is a requirment of all modules in the camera package."
                )
            if hasattr(module, "initialise_camera") is False:
                print(
                    f"Error: {module} does not have the function 'initialise_camera. \
                    This is a requirment of all modules in the camera package."
                )

            # Check if the module has a class with the inheritance from GenericCamera
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if (
                    isinstance(attribute, type)
                    and issubclass(attribute, GenericCamera)
                    and attribute is not GenericCamera
                ):
                    break
            else:
                print(
                    f"Error: {module} does not have a class inheriting from 'GenericCamera'. \
                    This is a requirment of all modules in the camera package."
                )


# Run validation on module import
_validate_camera_modules()


def get_camera_ids():
    """Get a list of unique camera IDs for all the different types of cameras connected to the machine."""

    package = importlib.import_module("camera_api")
    package_path = package.__path__  # Get the package's path

    modules = []
    for _, module_name, _ in pkgutil.iter_modules(package_path):
        modules.append(module_name)

    camera_list = []
    for module in modules:
        try:
            camera_module = importlib.import_module(f"camera_api.{module}")
            serial_numbers = camera_module.list_available_cameras()
            camera_list.extend(f"{serial_number}-{module}" for serial_number in serial_numbers)
        except ModuleNotFoundError:
            continue
    return camera_list


class CameraManager:
    """Class responsible for creating, storing and closing camera API instances."""

    def __init__(self):
        self._instances = {}

    def _create(self, unique_id):
        serial_number, module_name = unique_id.rsplit("-", 1)
        camera_module = importlib.import_module(f"camera_api.{module_name}")
        return camera_module.initialise_camera(serial_number=serial_number)

    def get_or_create(self, unique_id):
        """Return an existing camera API instance, or create one for this camera ID."""
        camera_api = self._instances.get(unique_id)
        if camera_api is None:
            camera_api = self._create(unique_id)
            self._instances[unique_id] = camera_api
        return camera_api

    def get(self, unique_id):
        """Return a managed camera API instance if present."""
        return self._instances.get(unique_id)

    def close(self, unique_id):
        """Close and remove a managed camera API instance by unique ID."""
        camera_api = self._instances.pop(unique_id, None)
        if camera_api is None:
            return
        try:
            camera_api.close()
        except Exception:
            pass  # Best-effort cleanup: continue closing other cameras.

    def close_all(self):
        """Close and clear all managed camera API instances."""
        camera_ids = list(self._instances.keys())
        for unique_id in camera_ids:
            self.close(unique_id)
