from pathlib import Path
import json


def get_camera_unique_ids():
    # config/camera_configs.json
    camera_configs = Path(".") / "config" / "camera_configs.json"
    with open(camera_configs.resolve(), "r") as file:
        data = json.load(file)
    return [camera["unique_id"] for camera in data]


def create_experiment_config(data_dir, n_cameras):

    camera_unique_ids = get_camera_unique_ids()
    config = {
        "data_dir": str(data_dir),
        "n_cameras": n_cameras,
        "n_columns": 1,
        "cameras": [{"label": camera_unique_ids[i], "subject_id": f"recording-{i+1}"} for i in range(n_cameras)],
    }
    return config


def create_camera_config(n_cameras, fps, downsampling_factor):
    camera_unique_ids = get_camera_unique_ids()
    cameras = [
        {
            "name": None,
            "unique_id": camera_unique_ids[i],
            "fps": fps,
            "exposure_time": min(max(1000, 1000000 // fps), 100000)
            - 1000,  # Ensure exposure time is between 1000 and 100000 microseconds
            "gain": 0,
            "pixel_format": "Mono8",
            "downsampling_factor": downsampling_factor,
        }
        for i in range(n_cameras)
    ]
    return cameras
