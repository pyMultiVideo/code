from pathlib import Path
import os
from datetime import datetime
import json


# Get the camera_labels from the camera_configs.json
def get_camera_labels():
    """From the config/camera_configs.json get the labels"""
    camera_config = Path(".") / "config" / "camera_configs.json"
    # Check if path exists
    if not camera_config.exists():
        raise FileNotFoundError(
            f"The file {camera_config} does not exist. Please run the application once to generate this file."
        )
    with open(camera_config, "r") as f:
        camera_data = json.load(f)
    return [camera["name"] if camera.get("name") is not None else camera["unique_id"] for camera in camera_data]


subject_ids = [f"subject_{i}" for i in range(len(get_camera_labels()))]

# The parameters which are varied
testing_parameters = {
    # Folder test name
    "test_name": f"test-with-fps",
    # "test_name": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    # Recording_length (s)
    "close_after": "00:02",  # HH:MM
    # Config
    "n_cameras": list(range(1, len(get_camera_labels()) + 1)),
    "downsample_range": [1, 2, 3, 4],
    "fps_range": [30, 60, 120],
    # GUI config
    "camera_update_range": [20, 30, 40],
    "camera_updates_per_display_update": [1],
    # FFMPEG
    "crf_range": [1, 23, 51],
    "encoding_speed_options": ["fast", "medium", "slow"],
    "compression_standard": ["h264", "h265"],
}

# Setup data directors for test to take place in
# 1. Create directory
test_directory = Path(".") / "data" / testing_parameters["test_name"]
try:
    test_directory.mkdir(parents=True, exist_ok=True)
    print(f"Directory created at: {test_directory}")
except Exception as e:
    print(f"Failed to create directory: {e}")
# 2. Save the testing parameters
# Save the testing parameters to a JSON file
parameters_file = test_directory / "testing_parameters.json"
try:
    with open(parameters_file, "w") as f:
        json.dump(testing_parameters, f, indent=4)
    print(f"Testing parameters saved to: {parameters_file}")
except Exception as e:
    print(f"Failed to save testing parameters: {e}")

# 3. Generate Config files
# Generate config files for each combination of parameters and Iterate over all parameter combinations
# Iterate over all parameter combinations, including the new parameters
for n_cameras in testing_parameters["n_cameras"]:
    for downsampling_factor in testing_parameters["downsample_range"]:
        for fps in testing_parameters["fps_range"]:
            for camera_update_rate in testing_parameters["camera_update_range"]:
                for updates_per_display in testing_parameters["camera_updates_per_display_update"]:
                    for crf in testing_parameters["crf_range"]:
                        for encoding_speed in testing_parameters["encoding_speed_options"]:
                            for compression_standard in testing_parameters["compression_standard"]:
                                # Generate a unique filename for the test
                                config_dir = (
                                    f"config_ncams_{n_cameras}_downsample_{downsampling_factor}_fps_{fps}_"
                                    f"update_{camera_update_rate}_upd_per_disp_{updates_per_display}_"
                                    f"crf_{crf}_speed_{encoding_speed}_comp_{compression_standard}"
                                )
                                # Folder for the metadata to be saved into for the test
                                test_config_dir = test_directory / config_dir
                                test_config_dir.mkdir(parents=True, exist_ok=True)

                                # Record the experiment configuration in a dictionary
                                test_config = {
                                    "n_cameras": n_cameras,
                                    "downsampling_factor": downsampling_factor,
                                    "fps": fps,
                                    "camera_update_rate": camera_update_rate,
                                    "camera_updates_per_display_update": updates_per_display,
                                    "crf": crf,
                                    "encoding_speed": encoding_speed,
                                    "compression_standard": compression_standard,
                                    "data_dir": str(test_config_dir.resolve()),  # Ensure this is a string
                                    "close_after": testing_parameters["close_after"],
                                }

                                # Save the experiment configuration to a JSON file in the test_config_dir
                                test_config_file = test_config_dir / "test_config.json"
                                try:
                                    with open(test_config_file, "w") as f:
                                        json.dump(test_config, f, indent=4)
                                    print(f"Experiment configuration saved to: {test_config_file}")
                                except Exception as e:
                                    print(f"Failed to save experiment configuration: {e}")
