"""
Generic API defining functionality needed for for camera system to interact with the GUI.
"""

from typing import Optional

from config.config import pixel_format_priority
from GUI.pixel_formats import PIXEL_FORMAT_REGISTRY, PixelFormat

# GenericCamera class -------------------------------------------------------------------


class GenericCamera:
    """Template class for representing a camera. Defines functionallity that must be implemented
    for interaction with the GUI."""

    def __init__(self, unique_id: str):
        # Options for camera -----------------------------------------------------------

        # Camera parameters to be set by backend-specific camera API subclass.
        self.unique_id = unique_id
        self.serial_number = None
        self.device_model = "GenericCamera"
        self.N_GPIO = 0  # Number of GPIO pins used as inputs for sync pulses.
        self.image_width = None
        self.image_height = None
        self.manual_control_enabled = False  # Whether camera supports manual gain / exposure controls.
        self.pixel_format_aliases = {}  # Maps GUI pixel format names to backend pixel format names.

        # Camera parameters set by GenericCamera methods (not backend-specific).
        self.pixel_format: PixelFormat | None = None  # set by initialize_preferred_pixel_format().

    # ======================================================================================================
    # Methods to implement in subclasses (backend/API-specific overrides required)
    # ======================================================================================================

    # Get camera parameters -------------------------------------------------------------------------------

    def get_frame_rate_range(self, *exposure_time: float) -> tuple[int, int]:
        """Get the min and max frame rate in Hz."""
        raise NotImplementedError

    def get_exposure_time(self) -> Optional[float]:
        """Get exposure of camera (optional, used only in camera_preview)."""
        return None

    def get_exposure_time_range(self, *fps: int) -> tuple[int, int]:
        """Get exposure time range of camera"""
        raise NotImplementedError

    def get_gain(self) -> Optional[float]:
        """Get camera gain setting in dB (optional, used only in camera_preview)."""
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

    def set_acqusition_mode(self, external_trigger: bool):
        """Configure the acqusition mode of the camera"""
        raise NotImplementedError

    def _set_pixel_format(self, pixel_format: str) -> None:
        """Set the camera pixel format using the backend-native name."""
        raise NotImplementedError

    # Camera control methods --------------------------------------------------------------------------------

    def begin_capturing(self) -> None:
        """Start aquiruing images from the camera."""
        raise NotImplementedError

    def stop_capturing(self) -> None:
        """Stop acquiring images from the camera"""
        raise NotImplementedError

    def get_available_images(self):
        """Get all available images from the camera buffer and clear buffer.
        Returns:
            {
            'images' : list[np.ndarray] : A list of images, each a 1D numpy byte array.
            'gpio_data' : list[np.ndarray] : List of gpio pinstates for each frame, each a 1D numpy boolean array.
            'timestamps' : list[int] : List of timestamps for each frame in microseconds
            'dropped_frames': int : Number of dropped frames since last call to get_available_images().
            }:
        """
        raise NotImplementedError

    def close(self):
        """Close the camera API and release any assoicated resources."""
        raise NotImplementedError

    # ======================================================================================================
    # Fully implemented GenericCamera methods (shared logic; usually not overridden)
    # ======================================================================================================

    def configure_settings(self, CameraConfig) -> None:
        """Apply settings from a CameraConfig object using the backend setters."""
        self.set_acqusition_mode(CameraConfig.external_trigger)
        if not CameraConfig.external_trigger:
            self.set_frame_rate(CameraConfig.fps)
        self.set_gain(CameraConfig.gain)
        self.set_exposure_time(CameraConfig.exposure_time)

    def initialize_preferred_pixel_format(self) -> None:
        """Resolve, apply, and store the preferred pixel format for this camera. The preferred pixel
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
    """Return a list of the available cameras identifier strings.
    naming format requirements: NUMBERS-MODULENAME
    type(name) == str
    """
    unique_id_list = []
    return unique_id_list


def initialise_camera_api(unique_id: str):
    """Returns a GenricCamera object"""
    return GenericCamera(unique_id=unique_id)
