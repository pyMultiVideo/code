import logging
import importlib
import pkgutil

logging.basicConfig(level=logging.INFO)


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


def find_all_cameras() -> list[str]:
    """Get a list of unique camera IDs for all the different types of cameras connected to the machine."""
    # for each module in the camera class, run the get unique ids function
    modules = get_modules_in_package("tools.camera")
    camera_list = []
    for module in modules:
        # Get the module
        camera_module = importlib.import_module(f"tools.camera.{module}")
        # Get the list of cameras as a string.
        camera_list.extend(camera_module.list_available_cameras())

    return camera_list


def init_camera(_id, CameraSettingsConfig=None):
    """Go through each"""
    # Split the camera unique_id into its api and its serial_no
    serial_no, module_name = _id.split("-")

    camera_module = importlib.import_module(f"tools.camera.{module_name}")

    return camera_module.initialise_by_id(
        _id=_id, CameraSettingsConfig=CameraSettingsConfig
    )


if __name__ == "__main__":
    print(get_modules_in_package("camera"))
    print(find_all_cameras())
    init_camera("18360350-spinnaker")
