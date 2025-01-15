"""
Database file for the project.

This module handles the management of project paths and loading of camera configuration data.

Move things from load_camera.py to this file neatness
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from tools.custom_data_classes import CameraSettingsConfig
from typing import Dict, Any

def find_project_root(marker='pyMultiVideo_GUI.pyw') -> (str | None):
    """Get the directory of the root folder based on the marker"""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return None

# Get the directory of the root
ROOT=find_project_root()

@dataclass
class ProjectDatabase:
    """
    A dataclass to manage project paths and load data for the project.
    """
    PROJECT_ROOT: str
    paths: Dict[str, str] = field(init=False)
    camera_data: Dict[str, Any] = field(init=False)

    def __post_init__(self):
        """
        Initialize derived attributes after the main attributes are set.
        """
        self.paths = {
            "ROOT": self.PROJECT_ROOT,
            "logger_dir": os.path.join(self.PROJECT_ROOT, "app_data", "logs"),
            "camera_dir": os.path.join(self.PROJECT_ROOT, "config"),
            "encoder_dir": os.path.join(self.PROJECT_ROOT, "config"),
            "data_dir": os.path.join(self.PROJECT_ROOT, "data"),
        }
        self.camera_data = self.load_camera_data()

    def load_camera_data(self) -> Dict[str, Any]:
        """
        Load camera configuration data from a JSON file.

        :return: A dictionary containing the camera configuration data.
        """
        camera_file_path = os.path.join(self.get_path("camera_dir"), "cameras_configs.json")
        try:
            with open(camera_file_path, "r") as file:
                camera_data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Camera configuration file not found at {camera_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {camera_file_path}")

        # Placeholder for data validation logic if needed.
        # self.validate_camera_data(camera_data)

        return camera_data

    def load_saved_setups(self) -> list[CameraSettingsConfig]:
        '''Function to load the saved setups from the database as a list of Setup objects'''
        setups_from_database = []
        for cam in self.camera_data: 
            setups_from_database.append(
                CameraSettingsConfig(
                    name      = cam['name'],
                    unique_id = cam['unique_id'],
                    fps       = cam['fps'],
                    pxl_fmt   = cam['pxl_fmt'],
                    downsample_factor=cam['downsample_factor']
                    )
                )
        return setups_from_database

    def get_path(self, key: str) -> str:
        """
        Retrieve a project path by its key.

        :param key: The key for the desired path (e.g., "camera_dir").
        :return: The corresponding path as a string.
        """
        return self.paths.get(key, f"Path '{key}' not found.")

    def validate_camera_data(self, camera_data: Dict[str, Any]):
        """
        Validate the camera data for consistency (e.g., check for duplicate unique identifiers).

        :param camera_data: The camera data to validate.
        """
        # Example placeholder for validation logic.
        pass



if __name__ =="__main__":
    # Initialize the database instance and expose it for global access.

    project_db = ProjectDatabase(ROOT)

    # Example usage:
    print(project_db.get_path("camera_dir"))
    print(project_db.camera_data)
