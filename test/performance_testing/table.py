# %% Load the data & create the dataframe
from pathlib import Path
import json
import pandas as pd
import seaborn as sns
import cv2
from tqdm import tqdm
import matplotlib.pyplot as plt

test_dir = Path(".") / "data" / "test-with-fps"
directories = [d for d in test_dir.resolve().iterdir() if d.is_dir()]

camera_rows = []
for directory in tqdm(directories, desc="Processing directories"):
    # Load testing parameters
    testing_params_path = directory / "test_config.json"
    with open(testing_params_path, "r") as f:
        testing_params = json.load(f)

    # Add test ID for each row
    testing_params["test_id"] = directory.name

    # Load metadata files
    metadata_files = directory.glob("*metadata*.json")
    for metadata_file in metadata_files:
        with open(metadata_file.resolve(), "r") as f:
            metadata = json.load(f)

        # Extract the corresponding video file name
        video_file_name = metadata_file.stem.replace("_metadata", "") + ".mp4"

        # Load the MP4 file path
        video_file_path = directory / video_file_name
        metadata["video_file_path"] = str(video_file_path.resolve())
        # Load the MP4 file as a video

        video_capture = cv2.VideoCapture(str(video_file_path.resolve()))
        if not video_capture.isOpened():
            raise ValueError(f"Unable to open video file: {video_file_path}")

        # Extract video properties
        metadata["real_frame_count"] = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        metadata["real_fps"] = video_capture.get(cv2.CAP_PROP_FPS)
        metadata["real_duration"] = (
            pd.to_timedelta(metadata["real_frame_count"] / metadata["real_fps"], unit="s")
            if metadata["real_fps"] > 0 else None
        )

        video_capture.release()

        # Concatenate metadata and testing parameters
        combined_data = {**metadata, **testing_params}
        camera_rows.append(combined_data)

# Create a DataFrame from the collected rows
metadata_df = pd.DataFrame(camera_rows)
# Create a % of dropped frames column
metadata_df["percent_dropped_frames"] = (metadata_df["dropped_frames"] /  metadata_df["recorded_frames"] + metadata_df["dropped_frames"]) * 100


# Save the DataFrame as a TSV file in the test directory
output_path = test_dir / "results.tsv"
metadata_df.to_csv(output_path, sep="\t", index=False)