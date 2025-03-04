"""
Generic API defining functionality needed for for camera system to interact with the GUI.
"""

# GenericCamera class -------------------------------------------------------------------


class GenericCamera:
    def __init__(self, CameraConfig=None):
        """Template class for representing a camera. Defines functionallity that must be implemented for interaction with the GUI."""
        pass

    # Functions to get the camera parameters -----------------------------------------------------------------

    def get_width(self) -> int:
        """Get the width of the camera image in pixels."""
        pass

    def get_height(self) -> int:
        """Get the height of the camera image in pixels."""
        pass

    def get_frame_rate(self) -> int:
        """Get the camera frame rate in Hz."""
        pass

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Get the min and max frame rate in Hz."""
        pass

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""

    def get_exposure_time_range(self) -> tuple[int, int]:
        """Get exposure time range of camera"""
        pass

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        pass

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        pass

    def get_pixel_format(self) -> str:
        """Get string specifying camera pixel format"""
        pass

    def get_available_pixel_fmt(self) -> list[str]:
        """Gets a string of the pixel formats available to the camera"""
        pass

    # Functions to set the camera parameters -----------------------------------------------------------------

    def set_frame_rate(self, frame_rate: int) -> None:
        """Set the aquisition frame rate of the camera"""
        pass

    def set_exposure_time(self, exposure_time) -> None:
        """Set the exposure_time of the camera"""
        pass

    def set_gain(self, gain):
        """Set the gain of the camera"""
        pass

    #  Functions to control the camera streaming and check status ---------------------------------------------

    def begin_capturing(self) -> None:
        """Start aquiruing images from the camera"""
        pass

    def stop_capturing(self) -> None:
        """Stop acquiring images from the camera"""
        pass

    def get_available_images(self):
        """Return all the data from the camera buffer as a dictionary.

        Important notes:
        1. This function must empty the buffer to make sure that no frames are dropped from the recording.
        2. This function time stamps from this function are used to calculate if the frames are being aquired too slowly such that there is a risk of dropping frames

        Returns:
            {
            'images' : img_buffer - a list of images (as numpy arrays)
            'gpio_data' : gpio_buffer - a corresponding list of gpio data for each of the frames
            'timestamps : timestamps_buffer - a corresponding list of timestampes for each frame
            }:
        """
        return {
            "images": img_buffer,
            "gpio_data": gpio_buffer,
            "timestamps": timestamps_buffer,
        }


# Camera system utility functions -------------------------------------------------------


def list_available_cameras() -> list[str]:
    """Return a list of the available cameras identifier strings.
    naming format requirements: NUMBERS-MODULENAME
    type(name) == str
    """
    unique_id_list = []
    return unique_id_list


def initialise_camera_api(CameraSettingsConfig=None):
    """Returns a camera instance based on the _id"""
    return GenericCamera()
