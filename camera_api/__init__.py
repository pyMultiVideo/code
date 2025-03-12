import os
import importlib
import pkgutil

from .generic_camera import GenericCamera

# Get the directory of this __init__.py file
current_directory = os.path.dirname(__file__)

# Loop through all files in the directory
for file_name in os.listdir(current_directory):
    if file_name.endswith(".py") and file_name != "__init__.py" and file_name != "generic_camera.py":
        # Remove the '.py' extension to get the module name
        module_name = file_name[:-3]
        # Import the module
        module = importlib.import_module(f".{module_name}", package=__name__)

        # Check if the expected functions and classes exist in every python module in the camera package
        if hasattr(module, "list_available_cameras") is False:
            print(
                f"Error: {module} does not have the function 'list_available_cameras. \
                    This is a requirment of all modules in the camera package."
            )
        if hasattr(module, "initialise_camera_api") is False:
            print(
                f"Error: {module} does not have the function 'initialise_camera_api. \
                    This is a requirment of all modules in the camera package."
            )

        # Check if the module has a class with the inheritance from GenericCamera
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if isinstance(attribute, type) and issubclass(attribute, GenericCamera) and attribute is not GenericCamera:
                break
        else:
            print(
                f"Error: {module} does not have a class inheriting from 'GenericCamera'. \
                    This is a requirment of all modules in the camera package."
            )

### Functions for initialising camera API -----------------------------------------------------------------------------


def get_camera_ids() -> list[str]:
    """Get a list of unique camera IDs for all the different types of cameras connected to the machine."""
    # for each module in the camera class, run the get unique ids function

    package = importlib.import_module("camera_api")
    package_path = package.__path__  # Get the package's path

    modules = []
    for _, module_name, _ in pkgutil.iter_modules(package_path):
        modules.append(module_name)

    camera_list = []
    for module in modules:
        # Get the module
        camera_module = importlib.import_module(f"camera_api.{module}")
        # Get the list of cameras as a string.
        camera_list.extend(camera_module.list_available_cameras())

    return camera_list


def init_camera_api_from_module(settings):
    """Initialise a camera API object given the camera ID and any camera settings."""
    _, module_name = settings.unique_id.split("-")
    camera_module = importlib.import_module(f"camera_api.{module_name}")
    return camera_module.initialise_camera_api(CameraSettingsConfig=settings)
