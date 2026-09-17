"""Script for running a set of different performance tests and plotting the results."""

from make_test_config import generate_test_configs
from performance_test import run_performance_test
from make_data_table import make_data_table
from plot_test_results import plot_test_results

# Define test parameters. ------------------------------------------------------------------------

# General test parameters

default_parameters = {  # Default values for parameters not sweeped during the performance test.
    "n_cameras": 2,
    "fps": 60,
    "downsampling_factor": 1,
    "camera_update_rate": 30,
    "camera_updates_per_display_update": 1,
    "crf": 28,
    "encoding_speed": "fast",
    "compression_standard": "h264",
}

recording_duration = 10  # seconds.

# Individual tests.

test_fps_n_cameras = {  # Sweep fps and number of cameras.
    "test_name": "fps_n_cameras",
    "recording_duration": recording_duration,
    "parameter_sweeps": {
        "fps": [30, 60, 90, 120, 150],
        "n_cameras": [1, 2],
    },
    "default_parameters": default_parameters,
}

test_fps_downsampling = {  # Sweep fps and downsampling factor.
    "test_name": "fps_downsampling",
    "recording_duration": recording_duration,
    "parameter_sweeps": {
        "fps": [30, 60, 90, 120, 150],
        "downsampling_factor": [1, 2, 4],
    },
    "default_parameters": default_parameters,
}

test_fps_encoding_speed = {  # Sweep fps and encoding speed.
    "test_name": "fps_encoding_speed",
    "recording_duration": recording_duration,
    "parameter_sweeps": {
        "fps": [30, 60, 90, 120, 150],
        "encoding_speed": ["slow", "medium", "fast"],
    },
    "default_parameters": default_parameters,
}

test_fps_cam_updates = {  # Sweep fps and camera updates per display update.
    "test_name": "fps_cam_updates",
    "recording_duration": recording_duration,
    "parameter_sweeps": {
        "fps": [30, 60, 90, 120, 150],
        "camera_updates_per_display_update": [1, 2, 4],
    },
    "default_parameters": default_parameters,
}

test_fps_comp_standard = {  # Sweep fps and camera updates per display update.
    "test_name": "fps_comp_standard",
    "recording_duration": recording_duration,
    "parameter_sweeps": {
        "fps": [30, 60, 90, 120, 150],
        "compression_standard": ["h264", "h265"],
    },
    "default_parameters": default_parameters,
}

all_tests = [
    test_fps_n_cameras,
    test_fps_downsampling,
    test_fps_encoding_speed,
    test_fps_cam_updates,
    test_fps_comp_standard,
]

# Run all tests and plot results ----------------------------------------------------------------

for test_parameters in all_tests:
    generate_test_configs(test_parameters)
    run_performance_test(test_parameters["test_name"])
    make_data_table(test_parameters["test_name"])
    plot_test_results(test_parameters["test_name"], show_plot=False)
