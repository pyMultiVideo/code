"""
This is a template class for which a new camera's functionality can be added to this application's interface.
"""
import numpy as np
from datetime import datetime


class GenericCamera:
    def __init__(self, CameraConfig=None):
        """This function gets the nodemap for the camera and create the camera object that is required for doing downstream functions."""
        pass

    def get_width(self) -> int:
        """Function that returns the width of the camera resolution"""
        pass

    def get_height(self) -> int:
        """Function that returns the height of the camera resolution"""
        pass

    def get_frame_rate(self) -> int:
        """Get the framerate of the camera"""
        pass

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Get the range of frame rates the camera can return

        Returns:
            tuple[int, int]: A tuple of int containing this data
        """
        pass

    def set_frame_rate_range(self) -> None:
        """Function to set the aquisition frame rate of the camera"""
        pass

    def begin_capturing(self) -> None:
        """Function to start aquiruing images from the camera"""
        pass

    def stop_capturing(self) -> None:
        """Function to the aquisition of images from the camera"""

    def set_buffer_handling_mode(self) -> None:
        """Consider implementing a function that sets any internal camera buffer to overwrite the oldest image from the buffer to write a new image"""

    def get_next_image(self) -> np.ndarray:
        """Function returns an image from the camera as a numpy array

        Important Note: the aquisition of the next image from the camera can be a blocking function
        (i.e. the function will prevent any other functions from being called without being completed). This will block the GUI from updating.
        Make sure that there is a timeout for the time taken to get the image if this is the case

        Returns:
            self.next_image: np.ndarray of the next image
        """

    def get_image_timestamp(self, next_image) -> datetime:
        """Function that returns a datetime object of the timestamp when the `next_image` was aquired"""
        timestamp = None
        return timestamp

    def retrieve_buffered_data(
        self,
    ) -> dict[list[np.ndarray], list[dict[str, bool]], list[int]]:
        """Function to returns all the data from the camera buffer as a dictionary.

        Important notes:
        1. This function must empty the buffer to make sure that no frames are dropped from the recording.
        2. This function time stamps from this function are used to calculate if the frames are being aquired too slowly such that there is a risk of dropping frames

        Returns:
            {
            'images' : self.img_buffer - a list of images (as numpy arrays)
            'gpio_data' : self.gpio_buffer - a corresponding list of gpio data for each of the frames
            'timestamps : self.timestamps_buffer - a corresponding list of timestampes for each frame
            }:
        """
        return {
            "images": self.img_buffer,
            "gpio_data": self.gpio_buffer,
            "timestamps": self.timestamps_buffer,
        }

    def get_GPIO_data(self) -> dict[str, bool]:
        """Function to return a dictionary of the GPIO data from the camera's GPIO pins"""
        return {
            "Line0": False,
            "Line1": False,
            "Line2": False,
            "Line3": False,
        }


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