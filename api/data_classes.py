from dataclasses import dataclass

@dataclass
class CameraConfig:
    name: str # name of the camera
    unique_id: str # unique id for the camera
    # subject_id: str # subject id (of the thing thing being recorded) 
    width: int
    height: int
    bitrate: int
    fps: int
    pixel_format: str
    gain: int
    exposure_time: int
    

@dataclass
class ExperimentConfig:
    data_dir: str
    encoder: str
    num_cameras: int
    cameras: list[CameraConfig]
    
    