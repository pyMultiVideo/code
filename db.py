'''
Database file for the project
'''
import sys
import os
import json
from typing import Tuple

import pandas as pd
# import numpy as np

def load_data() -> Tuple[pd.DataFrame]:
    
    encoder_file_path = os.path.join(this.paths['encoder_dir'], 'encoders.json')
    encoder_dict = json.load(open(encoder_file_path))
    
    return encoder_dict




ROOT = os.path.dirname(os.path.abspath(__file__))

# this a variable that is accessible from any module once this module has been imported 
# Pointer to module object instance
this = sys.modules[__name__]

this.paths = {
    'ROOT': ROOT,
    'logger_dir': os.path.join(ROOT, 'app_data', 'logs'),
    'camera_dir': os.path.join(ROOT, 'configs', 'experiments'),
    'encoder_dir': os.path.join(ROOT, 'configs', 'encoders')
}

# Load pandas dataframes

this.encoder_dict = load_data()

# Print the user_name column as a list
# print(this.camera_data)
# print(this.camera_data['user_name'].tolist())