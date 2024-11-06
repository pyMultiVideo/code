'''
Database file for the project
'''
import sys
import os
import json
from typing import Tuple

import pandas as pd

def load_data_csv() -> Tuple[pd.DataFrame, pd.DataFrame]:
    
    file_path = os.path.join(this.paths['camera_dir'], 'camera_information.csv')
    camera_data = pd.read_csv(file_path)
    camera_data.file_location = file_path
    
    return camera_data



config_path = os.path.join(os.path.dirname(__file__), 'config.json')
config = json.load(open(config_path))

ROOT = os.path.abspath(config['ROOT'])  # Root directory of the project


# this a variable that is accessible from any module once this module has been imported 
# Pointer to module object instance
this = sys.modules[__name__]

this.paths = {
    'ROOT': ROOT,
    'logger_dir': os.path.join(ROOT, 'app_data', 'logs'),
    'camera_dir': os.path.join(ROOT, 'app_data', 'camera'),
}

# Load pandas dataframes

this.camera_data = load_data_csv()