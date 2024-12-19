"""
Database file for the project
"""

import sys
import os
import json
from typing import Tuple

import pandas as pd
# import numpy as np


def load_data() -> Tuple[pd.DataFrame]:
    camera_file_path = os.path.join(this.paths["camera_dir"], "cameras_configs.json")
    camera_tables = json.load(open(camera_file_path))
    # When loading in the database we should be able to check things about the data (are there any repeated values for the unique idenifiers. )

    return camera_tables


ROOT = os.path.dirname(os.path.abspath(__file__))

# this a variable that is accessible from any module once this module has been imported
# Pointer to module object instance
this = sys.modules[__name__]

this.paths = {
    "ROOT": ROOT,
    "logger_dir": os.path.join(ROOT, "app_data", "logs"),
    "camera_dir": os.path.join(ROOT, "config"),
    "encoder_dir": os.path.join(ROOT, "config"),
    "data_dir": os.path.join(ROOT, "data"),
}

# Load pandas dataframes

this.camera_dict = load_data()

# Print the user_name column as a list
# print(this.camera_data)
# print(this.camera_data['user_name'].tolist())
