from pathlib import Path
import os
import json
import sys
from itertools import product

# Add the parent directory to sys.path for proper imports
ROOT = Path(__file__).resolve().parent.parent  # pyMV code folder.
sys.path.append(str(ROOT))

from config.config import default_camera_config, ffmpeg_config, gui_config, paths_config

# Performance test parameters.

test_parameters = {
    "test_name": "perf-test",
    "recording_duration": 10,  # seconds.
    "parameter_sweeps": {  # Parameters to be systematically varied for performance testing.
        "fps": [30, 60, 90, 120, 150],
        "n_cameras": [1, 2],
    },
}

# Default values for parameters not sweeped during the performance test.

SWEEP_DEFAULTS = {
    "n_cameras": 1,
    "fps": default_camera_config["fps"],
    "downsampling_factor": default_camera_config["downsampling_factor"],
    "camera_update_rate": gui_config["camera_update_rate"],
    "camera_updates_per_display_update": gui_config["camera_updates_per_display_update"],
    "crf": ffmpeg_config["crf"],
    "encoding_speed": ffmpeg_config["encoding_speed"],
    "compression_standard": ffmpeg_config["compression_standard"],
}

# Generate test config.


def generate_test_configs(test_parameters):
    """Create all performance-test configuration files from the supplied parameters."""
    test_directory = ROOT / "data" / test_parameters["test_name"]
    test_directory.mkdir(parents=True, exist_ok=True)
    print(f"Directory created at: {test_directory}")

    parameters_file = test_directory / "test_parameters.json"
    with open(parameters_file, "w") as f:
        json.dump(test_parameters, f, indent=4)
    print(f"Testing parameters saved to: {parameters_file}")

    for combination in _get_parameter_combinations(test_parameters):
        config_dir = _get_config_directory_name(combination)
        test_config_dir = test_directory / config_dir
        test_config_dir.mkdir(parents=True, exist_ok=True)
        with open(test_config_dir / "test_config.json", "w") as f:
            json.dump(
                _generate_recording_config(
                    data_dir=test_config_dir,
                    close_after=test_parameters["recording_duration"],
                    fps=combination["fps"],
                    n_camera=combination["n_cameras"],
                    crf=combination["crf"],
                    camera_update_rate=combination["camera_update_rate"],
                    downsampling_factor=combination["downsampling_factor"],
                    encoding_speed=combination["encoding_speed"],
                    compression_standard=combination["compression_standard"],
                    updates_per_display=combination["camera_updates_per_display_update"],
                ),
                f,
                indent=4,
            )


# Helper functions.


def _get_camera_unique_ids():
    """Get all unique camera IDs from the camera_configs.json file."""
    camera_configs = ROOT / "config" / "camera_configs.json"
    with open(camera_configs.resolve(), "r") as file:
        data = json.load(file)
    return [camera["unique_id"] for camera in data]


def _create_experiment_config(data_dir, n_cameras):
    """Create an experiment configuration dictionary with specified data directory and number of cameras."""
    camera_unique_ids = _get_camera_unique_ids()
    config = {
        "data_dir": str(data_dir),
        "n_cameras": n_cameras,
        "n_columns": 1,
        "cameras": [{"label": camera_unique_ids[i], "subject_id": f"recording-{i+1}"} for i in range(n_cameras)],
    }
    return config


def _create_camera_config(n_cameras, fps, downsampling_factor):
    """Create a list of camera configurations with specified parameters."""
    camera_unique_ids = _get_camera_unique_ids()
    cameras = [
        {
            "name": None,
            "unique_id": camera_unique_ids[i],
            "fps": fps,
            "exposure_time": min(max(1000, 1000000 // fps), 100000)
            - 1000,  # Ensure exposure time is between 1000 and 100000 microseconds
            "gain": 0,
            "pixel_format": default_camera_config["pixel_format"],
            "downsampling_factor": downsampling_factor,
        }
        for i in range(n_cameras)
    ]
    return cameras


def _generate_recording_config(
    data_dir,
    close_after,
    camera_update_rate,
    updates_per_display,
    fps,
    n_camera,
    downsampling_factor,
    crf,
    encoding_speed,
    compression_standard,
):
    """Create a complete configuration for a single recording run during a performance test.."""
    return {
        "application_config": {
            "gui_config": {
                "camera_update_rate": camera_update_rate,
                "camera_updates_per_display_update": updates_per_display,
                "font_size": 12,
            },
            "ffmpeg_config": {
                "crf": crf,
                "encoding_speed": encoding_speed,
                "compression_standard": compression_standard,
            },
            "paths_config": paths_config,
            "default_camera_config": default_camera_config,
        },
        "experiment_config": _create_experiment_config(data_dir=data_dir, n_cameras=n_camera),
        "camera_config": _create_camera_config(n_cameras=n_camera, fps=fps, downsampling_factor=downsampling_factor),
        "record-on-startup": True,
        "close_after": close_after,
    }


def _as_list(value):
    """Normalize a scalar or sequence into a list of sweep values."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _get_parameter_combinations(parameters):
    """Return parameter combinations for a test specification."""
    parameter_sweeps = parameters.get("parameter_sweeps", {})
    unknown_parameters = set(parameter_sweeps) - set(SWEEP_DEFAULTS)
    if unknown_parameters:
        raise ValueError(f"Unknown parameter sweep(s): {sorted(unknown_parameters)}")

    sweep_names = list(SWEEP_DEFAULTS)
    sweep_values = [
        _as_list(parameter_sweeps[name]) if name in parameter_sweeps else [SWEEP_DEFAULTS[name]]
        for name in sweep_names
    ]
    return [dict(zip(sweep_names, values)) for values in product(*sweep_values)]


def _get_config_directory_name(parameters):
    """Build a stable directory name from one effective parameter combination."""
    return (
        f"config_ncams_{parameters['n_cameras']}_downsample_{parameters['downsampling_factor']}_"
        f"fps_{parameters['fps']}_update_{parameters['camera_update_rate']}_"
        f"upd_per_disp_{parameters['camera_updates_per_display_update']}_crf_{parameters['crf']}_"
        f"speed_{parameters['encoding_speed']}_comp_{parameters['compression_standard']}"
    )


if __name__ == "__main__":
    generate_test_configs(test_parameters)
