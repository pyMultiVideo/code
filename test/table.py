# %% Load the data & create the dataframe
from pathlib import Path
import json
import pandas as pd
import cv2
from tqdm import tqdm

test_dir = Path(".") / "data" / "test-photo-1"
directories = [d for d in test_dir.resolve().iterdir() if d.is_dir()]

camera_rows = []
for directory in tqdm(directories, desc="Processing directories"):
    # Load testing parameters
    testing_params_path = directory / "test_config.json"
    with open(testing_params_path, "r") as f:
        testing_params = json.load(f)

    # Flatten the testing_params dictionary
    def flatten_dict(d, parent_key="", sep="_"):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    testing_params = flatten_dict(testing_params)
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
        try:
            video_capture = cv2.VideoCapture(str(video_file_path.resolve()))
            if not video_capture.isOpened():
                raise ValueError(f"Unable to open video file: {video_file_path}")

            # Extract video properties
            metadata["real_frame_count"] = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            metadata["real_fps"] = video_capture.get(cv2.CAP_PROP_FPS)  # FPS encoded by FFMPEG
            metadata["real_duration"] = (
                pd.to_timedelta(metadata["real_frame_count"] / metadata["real_fps"], unit="s")
                if metadata["real_fps"] > 0
                else None
            )
        except Exception as e:
            metadata["real_frame_count"] = None
            metadata["real_fps"] = None
            metadata["real_duration"] = None
            print(f"Error processing video file {video_file_path}: {e}")
        finally:
            if "video_capture" in locals():
                video_capture.release()
        # Concatenate metadata and testing parameters
        combined_data = {**metadata, **testing_params}
        camera_rows.append(combined_data)
# Create a DataFrame from the collected rows
metadata_df = pd.DataFrame(camera_rows)
# Create a % of dropped frames column
metadata_df["percent_dropped_frames"] = (
    metadata_df["dropped_frames"] / metadata_df["recorded_frames"] + metadata_df["dropped_frames"]
) * 100
# Reorder columns to make test_id the first column and n_cameras the second column
columns = ["test_id"] + [col for col in metadata_df.columns if col not in ["test_id"]]
metadata_df = metadata_df[columns]

# Save the DataFrame as a TSV file in the test directory
output_path = test_dir / "results.tsv"
metadata_df.to_csv(output_path, sep="\t", index=False)

# After report generation, create a .bat script to remove video files
bat_script_content = """@echo off
setlocal

:: Set the target folder (current folder by default)
set "targetFolder=%cd%"

:: Recursively delete all .mp4 files
for /r "%targetFolder%" %%f in (*.mp4) do (
    echo Deleting "%%f"
    del "%%f"
)

echo All .mp4 files have been removed.
pause
"""

# Save the .bat script in the test directory
bat_script_path = test_dir / "remove_videos.bat"
with open(bat_script_path, "w") as bat_file:
    bat_file.write(bat_script_content)
