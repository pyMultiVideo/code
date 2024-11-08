from dataclasses import dataclass

@dataclass
class CameraConfig:
    name: str
    subject_ID: str
    width: int
    height: int
    bitrate: str
    fps: int
    pixel_format: str
    exposure_time: int
    gain: int
    display_update_ps: int

@dataclass
class ExperimentConfig:
    data_dir: str
    encoder: str
    num_cameras: int
    cameras: list[CameraConfig]