from dataclasses import dataclass


@dataclass
class CameraSetupConfig:
    """
    Data class to hold the configuration of a single user set camera settings
    """

    label: str
    subject_id: str


@dataclass
class ExperimentConfig:
    """
    Data to hold the use set conPfiguPration of a single experiment
    """

    data_dir: str
    encoder: str
    num_cameras: int
    grid_layout: bool
    cameras: list[CameraSetupConfig]


@dataclass
class CameraSettingsConfig:
    """
    Data class to hold the camera settings for a single camera
    """

    name: str
    unique_id: str
    fps: str
    pxl_fmt: str
    downsample_factor: int
