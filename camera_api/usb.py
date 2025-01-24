import logging
import cv2_enumerate_cameras
import cv2
import numpy as np

# import the camera template
from . import GenericCamera


class USBCamera(GenericCamera):
    """Class for handling USB cameras. This implementation used the cv2 and cv2_enumerate_cameras libraries"""

    def __init__(self, unique_id: str, CameraConfig):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)
        pid, api = unique_id.split("-")
        self.pid = int(pid)
        self._init_camera()
        self.get_camera_parameters()

    def _init_camera(self):
        """For USB camera, this function initializes the cv2.VideoCapture object"""
        # Use cv2_enumerate_cameras to get the total list of usb cameras
        usb_cam_list = cv2_enumerate_cameras.enumerate_cameras()
        # Search this list for the camera with the pid
        for cam in usb_cam_list:
            if cam.pid == self.pid:
                self.camera = cam
                break
        # Initialize the camera

        self.capture = cv2.VideoCapture(self.camera.index, self.camera.backend)

    def get_camera_parameters(self):
        """Get the camera parameters"""
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Camera parameters: {self.fps}, {self.width}, {self.height}")

    def is_streaming(self) -> bool:
        """Always recording"""
        return True

    def is_initialized(self) -> bool:
        """Always initialized"""
        return True

    def get_next_image(self) -> np.ndarray:
        ret, frame = self.capture.read()
        # convert the frame to monochrome if the color is set to false
        if self.color:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            pass
        return frame

    def get_next_image_list(self) -> list[np.ndarray]:
        """Get all the images in the buffer. Here there is no buffer so the only image that is returned is from the normal function call , just reformatted."""
        return [self.get_next_image()]


########### Finding Cameras


def list_available_cameras() -> list[str]:
    """Place holder function which returns a list of the available cameras.
    The should be uniquly idenified as a string.
    """
    usb_cam_list = cv2_enumerate_cameras.enumerate_cameras()
    # Preprocess this list because it returns duplicates sometimtes
    for cam1 in usb_cam_list:
        for cam2 in usb_cam_list:
            if cam1.path == cam2.path:
                usb_cam_list.remove(cam2)

    unique_id_list=[]
    for cam in usb_cam_list:
        cam_id: str = f"{cam.pid}-usb"
        # print(f"Camera ID: {cam_id}")
        unique_id_list.append(cam_id)


    return unique_id_list


def initialise_by_id(_id, CameraSettingsConfig):
    """Function that returns a camera instance based on the _id"""

    return USBCamera(unique_id=_id, CameraConfig=CameraSettingsConfig)


if __name__ == "__main__":
    # Code for checking if the functions work
    initialise_by_id(list_available_cameras()[0])
