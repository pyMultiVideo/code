"""
Generic API defining functionality needed for for camera system to interact with the GUI.
"""

import numpy as np
from datetime import datetime

# GenericCamera class -------------------------------------------------------------------


class GenericCamera:
    def __init__(self, CameraConfig=None):
        """Template class for representing a camera. Defines functionallity that must be implemented for interaction with the GUI."""
        pass

    def get_width(self) -> int:
        """Function that returns the width of the camera resolution"""
        pass

    def get_height(self) -> int:
        """Function that returns the height of the camera resolution"""
        pass

    def set_frame_rate(self, frame_rate: int) -> None:
        """Function to set the aquisition frame rate of the camera"""
        pass

    def begin_capturing(self) -> None:
        """Function to start aquiruing images from the camera"""
        pass

    def stop_capturing(self) -> None:
        """Function to the aquisition of images from the camera"""
        pass

    def get_available_images(
        self,
    ) -> dict[list[np.ndarray], list[dict[str, bool]], list[int]]:
        """Function to returns all the data from the camera buffer as a dictionary.

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

    def begin_capturing(self) -> None:
        """Function that sends a signal to trigger recording if the output of this function is True.
        This function will be called from by a refresh function enough times to be fast enough to start recording if required.

        For this camera, the recording will be triggered by one of the GPIO line states being set to High.

        In principle this function could do anything to start recording by doing something that means this function returns True.
        """
        pass

    def stop_capturing(self) -> None:
        """Conceptually same as above. This function is called if the camera is recording, and will take the outcome of this function (True / False) as a Trigger to stop recording"""
        pass


# Camera system utility functions -------------------------------------------------------


def list_available_cameras() -> list[str]:
    """Place holder function which returns a list of the available cameras.
    The should be uniquly idenified as a string.

    naming format requirements: NUMBERS-MODULENAME
    type(name) == str
    """
    unique_id_list = []
    return unique_id_list


def initialise_by_id(_id, CameraSettingsConfig=None):
    """Function that returns a camera instance based on the _id"""

    return GenericCamera()
