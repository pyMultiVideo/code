"""
Generic API defining functionality needed for for camera system to interact with the GUI.
"""

from typing import Optional

from config.config import camera_pixel_format_priority
from GUI.pixel_formats import get_pixel_format_info

# GenericCamera class -------------------------------------------------------------------


class GenericCamera:
    """Template class for representing a camera. Defines functionallity that must be implemented for interaction with the GUI."""

    def __init__(self, unique_id: str):
        # Options for camera -----------------------------------------------------------

        self.unique_id = unique_id
        self.serial_number = None
        self.device_model = "GenericCameraModel"
        self.N_GPIO = 0
        self.image_width = None
        self.image_height = None
        self.manual_control_enabled = False  # Whether camera supports manual gain / exposure controls.
        self.pixel_format_key = None
        self.pixel_format_aliases = {}
        self._pixel_format = None

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

    def _get_supported_pixel_formats(self) -> list[str]:
        """Return the internal pixel-format names supported by the camera."""
        raise NotImplementedError

    def _get_camera_pixel_format(self) -> str:
        """Return the currently active backend-native pixel format name."""
        raise NotImplementedError

    def resolve_preferred_pixel_format(self, supported_pixel_formats: list[str] | None = None) -> str:
        """Return the first preferred canonical pixel-format key supported by the camera."""
        supported_pixel_formats = supported_pixel_formats or self._get_supported_pixel_formats()
        supported_canonical_formats = set()
        native_to_canonical = {
            native_name: canonical_name for canonical_name, native_name in self.pixel_format_aliases.items()
        }
        for native_pixel_format in supported_pixel_formats:
            canonical_pixel_format = native_to_canonical.get(native_pixel_format)
            if canonical_pixel_format:
                supported_canonical_formats.add(canonical_pixel_format)
        for pixel_format_key in camera_pixel_format_priority:
            if pixel_format_key in supported_canonical_formats:
                return pixel_format_key
        raise ValueError("No supported pixel format available.")

    def get_selected_pixel_format(self) -> str:
        """Return the selected canonical pixel-format key."""
        if self.pixel_format_key is None:
            raise ValueError("Pixel format has not been selected yet.")
        return self.pixel_format_key

    def get_selected_pixel_format_metadata(self) -> dict:
        """Return metadata for the selected pixel format."""
        return get_pixel_format_info(self.get_selected_pixel_format())

    def initialize_preferred_pixel_format(self) -> None:
        """Resolve, apply, and store the preferred pixel format for this camera."""
        self.pixel_format_key = self.resolve_preferred_pixel_format(self._get_supported_pixel_formats())
        self.set_pixel_format(self.pixel_format_key)
        self._pixel_format = self._get_camera_pixel_format()

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
