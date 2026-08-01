"""
Generic API defining functionality needed for for camera system to interact with the GUI.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from config.config import pixel_format_priority
from GUI.pixel_formats import PIXEL_FORMAT_REGISTRY, PixelFormat


@dataclass
class FrameData:
    """Class for representing a single frame of image data and associated metadata."""

    image: np.ndarray  # Image data as a 1D numpy array.
    GPIO_pinstate: np.ndarray  # State of GPIO pins as a 1D numpy bool array.
    timestamp: int  # Frame timestamp in microseconds.
    number: int  # Frame number.


# GenericCamera class -------------------------------------------------------------------


class GenericCamera:
    """Template class for representing a camera. Defines functionallity that must be implemented
    for interaction with the GUI."""

    def __init__(self, serial_number: str):
        # Options for camera -----------------------------------------------------------

        # Camera parameters to be set by backend-specific camera API subclass.
        self.serial_number = serial_number
        # Camera system identifier is inferred from the backend module name.
        self.camera_system = self.__class__.__module__.split(".")[-1]
        self.device_model = "GenericCamera"
        self.N_GPIO = 0  # Number of GPIO pins used as inputs for sync pulses.
        self.image_width = None
        self.image_height = None
        self.pixel_format_aliases = {}  # Maps GUI pixel format names to backend pixel format names.
        self.has_manual_control = {  # Whether camera supports manual control of these parameters.
            "fps": False,
            "exposure": False,
            "gain": False,
            "trigger": False,
        }

        # Camera parameters set by GenericCamera methods (not backend-specific).
        self.pixel_format: PixelFormat | None = None  # set by initialize_preferred_pixel_format().

    def get_unique_id(self) -> str:
        """Return unique camera ID in SERIAL-MODULE format."""
        return f"{self.serial_number}-{self.camera_system}"

    # ======================================================================================================
    # Methods to implement in subclasses (backend/API-specific overrides required)
    # ======================================================================================================

    # Get camera parameters -------------------------------------------------------------------------------

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Get the min and max frame rate in Hz."""
        raise NotImplementedError

    def get_exposure_time(self) -> Optional[float]:
        """Get exposure of camera in microseconds, optional - used only in camera_preview."""
        return None

    def get_exposure_time_range(self) -> tuple[int, int]:
        """Get exposure time range of camera"""
        raise NotImplementedError

    def get_gain(self) -> Optional[float]:
        """Get camera gain setting in dB, optional - used only in camera_preview."""
        return None

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        raise NotImplementedError

    def _get_supported_pixel_formats(self) -> list[str]:
        """Return the backend-native pixel format names supported by the camera."""
        raise NotImplementedError

    def _get_camera_pixel_format(self) -> str:
        """Return the currently active backend-native pixel format name."""
        raise NotImplementedError

    # Write camera parameters --------------------------------------------------------------------------------

    def set_frame_rate(self, *frame_rate: int) -> None:
        """Set the aquisition frame rate of the camera"""
        raise NotImplementedError

    def set_exposure_time(self, *exposure_time) -> None:
        """Set the exposure_time of the camera"""
        raise NotImplementedError

    def set_gain(self, gain):
        """Set the gain of the camera"""
        raise NotImplementedError

    def set_external_trigger_enable(self, enable: bool):
        """Configure whether camera uses external triggering for frame acquisition."""
        raise NotImplementedError

    def _set_pixel_format(self, pixel_format: str) -> None:
        """Set the camera pixel format using the backend-native name."""
        raise NotImplementedError

    # Camera control methods --------------------------------------------------------------------------------

    def begin_capturing(self) -> None:
        """Start aquiruing images from the camera."""
        raise NotImplementedError

    def stop_capturing(self) -> None:
        """Stop acquiring images from the camera."""
        raise NotImplementedError

    def get_available_images(self) -> list[FrameData]:
        """Get all available frames from the camera and return as list of FrameData objects."""
        raise NotImplementedError

    def close(self):
        """Close the camera API and release any assoicated resources."""
        raise NotImplementedError

    # ======================================================================================================
    # Fully implemented GenericCamera methods (shared logic; usually not overridden)
    # ======================================================================================================

    def configure_settings(self, CameraConfig) -> None:
        """Apply settings from a CameraConfig object using the backend setters."""

        if self.has_manual_control["trigger"]:
            try:
                self.set_external_trigger_enable(CameraConfig.external_trigger)
            except Exception as e:
                print(f"Error occurred while setting external trigger mode: {e}")

        if self.has_manual_control["fps"] and not CameraConfig.external_trigger:
            try:
                self.set_frame_rate(CameraConfig.fps)
            except Exception as e:
                print(f"Error occurred while setting frame rate: {e}")

        if self.has_manual_control["gain"]:
            try:
                self.set_gain(CameraConfig.gain)
            except Exception as e:
                print(f"Error occurred while setting gain: {e}")

        if self.has_manual_control["exposure"]:
            try:
                self.set_exposure_time(CameraConfig.exposure_time)
            except Exception as e:
                print(f"Error occurred while setting exposure time: {e}")

    def initialize_preferred_pixel_format(self) -> None:
        """Set the camera pixel format given preferred and available formats. The selected pixel
        format is the first format in pixel_format_priority that is supported by the camera."""
        supported_native_formats = self._get_supported_pixel_formats()
        supported_formats = [
            fmt for fmt, native_name in self.pixel_format_aliases.items() if native_name in supported_native_formats
        ]
        preferred_format = next((fmt for fmt in pixel_format_priority if fmt in supported_formats), None)
        if preferred_format is None:
            raise ValueError("No supported pixel format available.")
        preferred_native_format = self.pixel_format_aliases[preferred_format]
        self._set_pixel_format(preferred_native_format)
        self.pixel_format = PIXEL_FORMAT_REGISTRY[preferred_format]


# Camera system utility functions -------------------------------------------------------


def list_available_cameras() -> list[str]:
    """Return a list of camera serial numbers available for this backend."""
    serial_number_list = []
    return serial_number_list


def initialise_camera_api(serial_number: str):
    """Return a GenericCamera object for the requested serial number."""
    return GenericCamera(serial_number=serial_number)
