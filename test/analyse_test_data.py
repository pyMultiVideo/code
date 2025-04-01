#%% Load the data & create the dataframe
from pathlib import Path
import json
import pandas as pd
test_dir = Path('..') / 'data' / 'test'
directories = [d for d in test_dir.iterdir() if d.is_dir()]

camera_rows = []

for directory in directories:
    # Load testing parameters
    testing_params_path = directory / 'test_config.json'
    with open(testing_params_path, 'r') as f:
        testing_params = json.load(f)
    
    # Add test ID for each row
    testing_params['test_id'] = directory.name
    
    # Load metadata files
    metadata_files = directory.glob('*metadata*.json')
    for metadata_file in metadata_files:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Concatenate metadata and testing parameters
        combined_data = {**metadata, **testing_params}
        camera_rows.append(combined_data)

# Create a DataFrame from the collected rows
metadata_df = pd.DataFrame(camera_rows)
# Create a % of dropped frames column
if 'total_frames' in metadata_df.columns and 'dropped_frames' in metadata_df.columns:
    metadata_df['percent_dropped_frames'] = (metadata_df['dropped_frames'] / metadata_df['total_frames']) * 100


# Save the DataFrame as a TSV file in the test directory
output_path = test_dir / 'summary.tsv'
metadata_df.to_csv(output_path, sep='\t', index=False)
# %% Create figures

# For each test_id, 




