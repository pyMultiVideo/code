"""
Generic API defining functionality needed for for camera system to interact with the GUI.
"""

import cv2
from typing import Optional

# GenericCamera class -------------------------------------------------------------------


class GenericCamera:
    """Template class for representing a camera. Defines functionallity that must be implemented for interaction with the GUI."""

    def __init__(self, unique_id: str):
        # Options for camera -----------------------------------------------------------

        self.unique_id = unique_id
        self.serial_number = None  # To be replaced with device serial number.
        self.device_model = "GenericCameraModel"  # Replace with the camera model name to be recorded in metadata.
        self.N_GPIO = 3  # Number of pins that the camera records each frame.
        self.image_width = None
        self.image_height = None
        self.manual_control_enabled = False  # Whether camera supports manual gain / exposure controls.

        # This ordered dictionary represents the metadata that the camera class requires for handling different pixel formats.
        # 'Internal' refers to the camera's internal name for the pixel format.
        # 'ffmpeg' specifies the corresponding pixel format name used by ffmpeg.
        # 'cv2' specifices the OpenCV conversion code for the pixel format.
        self.pixel_format_map = {
            "Colour": {
                "Internal": "BayerRG8",
                "ffmpeg": "bayer_rggb8",
                "cv2": cv2.COLOR_BayerRG2BGR,
            },
            "Mono": {
                "Internal": "Mono8",
                "ffmpeg": "gray",
                "cv2": cv2.COLOR_GRAY2BGR,
            },
        }

    # Functions to get the camera parameters -----------------------------------------------------------------

    def get_frame_rate_range(self, *exposure_time: float) -> tuple[int, int]:
        """Get the min and max frame rate in Hz."""
        raise NotImplementedError

    def get_exposure_time(self) -> Optional[float]:
        """Get exposure of camera"""
        return None

    def get_exposure_time_range(self, *fps: int) -> tuple[int, int]:
        """Get exposure time range of camera"""
        raise NotImplementedError

    def get_gain(self) -> Optional[float]:
        """Get camera gain setting in dB."""
        return None

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        raise NotImplementedError

    # Functions to set the camera parameters -----------------------------------------------------------------

    def set_frame_rate(self, *frame_rate: int) -> None:
        """Set the aquisition frame rate of the camera"""
        raise NotImplementedError

    def set_exposure_time(self, *exposure_time) -> None:
        """Set the exposure_time of the camera"""
        raise NotImplementedError

    def set_gain(self, gain):
        """Set the gain of the camera"""
        raise NotImplementedError

    def set_pixel_format(self, pixel_format: str) -> None:
        """Set the camera pixel format."""
        raise NotImplementedError

    # Configure Acqusition Mode -------------------------------------------------------------------------------

    def set_acqusition_mode(self, external_trigger: bool):
        """Configuriung the acqusition mode of the camera"""
        raise NotImplementedError

    def configure_settings(self, CameraConfig) -> None:
        """Apply settings from a CameraConfig-like object using the backend setters."""
        self.set_acqusition_mode(CameraConfig.external_trigger)
        if not CameraConfig.external_trigger:
            self.set_frame_rate(CameraConfig.fps)
        self.set_gain(CameraConfig.gain)
        self.set_exposure_time(CameraConfig.exposure_time)
        self.set_pixel_format(CameraConfig.pixel_format)

    #  Functions to control the camera streaming and check status ---------------------------------------------

    def begin_capturing(self) -> None:
        """Start aquiruing images from the camera."""
        raise NotImplementedError

    def stop_capturing(self) -> None:
        """Stop acquiring images from the camera"""
        raise NotImplementedError

    def get_available_images(self):
        """Return all the data from the camera buffer as a dictionary.

        Important notes:
        1. This function must empty the buffer to make sure that no frames are dropped from the recording.
        2. This function time stamps from this function are used to calculate if the frames are being aquired too slowly such that there is a risk of dropping frames

        Returns:
            {
            'images' : img_buffer - a list of images (as 1D numpy byte arrays).
            'gpio_data' : gpio_buffer - a corresponding list of gpio data for each of the frames
            'timestamps : timestamps_buffer - a corresponding list of timestampes for each frame
            'dropped_frames': the number of dropped frames found (can be calculayted or a camera attributed)
            }:
        """
        raise NotImplementedError

    def close(self):
        """Close the camera API and release any assoicated resources."""
        raise NotImplementedError


# Camera system utility functions -------------------------------------------------------


def list_available_cameras() -> list[str]:
    """Return a list of the available cameras identifier strings.
    naming format requirements: NUMBERS-MODULENAME
    type(name) == str
    """
    unique_id_list = []
    return unique_id_list


def initialise_camera_api(unique_id: str):
    """Returns a GenricCamera object"""
    return GenericCamera(unique_id=unique_id)
