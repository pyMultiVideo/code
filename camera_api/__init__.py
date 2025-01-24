import os
import importlib

# from camera.generic_camera import GenericCamera
from .generic_camera import GenericCamera

# Get the directory of this __init__.py file
current_directory = os.path.dirname(__file__)

# Loop through all files in the directory
for file_name in os.listdir(current_directory):
    if (
        file_name.endswith(".py")
        and file_name != "__init__.py"
        and file_name != "generic_camera.py"
    ):
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
        if hasattr(module, "initialise_by_id") is False:
            print(
                f"Error: {module} does not have the function 'initialise_by_id. \
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
