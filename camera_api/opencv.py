import logging
import cv2_enumerate_cameras
import cv2
import numpy as np
from datetime import datetime

# import the camera template
from . import GenericCamera
import platform

if platform.system() == "Darwin":
    from AppKit import AVCaptureDevice
    import av
from collections import deque
import threading


class openvcvCamera(GenericCamera):
    """Class for handling USB cameras. This implementation used the cv2 and cv2_enumerate_cameras libraries"""

    def __init__(self, unique_id: str, CameraConfig):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)
        pid, api = unique_id.split("-")
        if platform.system == "Windows":
            self.pid = int(pid)
        else:
            self.pid = int(pid)
        self._init_camera()
        self.get_camera_parameters()

        self.initialsed = False  # by default
        self.fps = CameraConfig.fps if CameraConfig is not None else 30

        self.img_buffer = deque(maxlen=10)

        self.time_stamps_buffer = deque(maxlen=10)

        self.gpio_buffer = deque(maxlen=10)
        
        
        self.begin_aquisition()

    def _init_camera(self):
        """For USB camera, this function initializes the cv2.VideoCapture object"""
        # Use cv2_enumerate_cameras to get the total list of usb cameras

        if platform.system() == "Windows":
            usb_cam_list = cv2_enumerate_cameras.enumerate_cameras()
            # Search this list for the camera with the pid
            for cam in usb_cam_list:
                if cam.pid == self.pid:
                    self.camera = cam
                    break

            self.capture = cv2.VideoCapture(self.camera.index, self.camera.backend)
        elif platform.system() == "Darwin":
            self.capture = cv2.VideoCapture(self.pid)

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
        """Always initialized

        Implemetentation: There is no buffer in the camera. We can make it synethically though.
        This is important as we do not call the camera to retrieve all the data every frame in the
        GUI so we so to have a frame rate that is not capped at the rate at which we aquire images from the GUI,
        then we need a buffer to keep images tempruaroly due to the implementation of the saving to disk funciton in the GUI

        By settings a rate at which the  frames are saved to a internal camera buffer (as NP array)
        This can be done at a 'frame rate' which is the rate at which we save the images to teh nparray when the camera
        is initialised.

        When the self.retrieve_buffered_data function is called, we get all data from the internally
        created buffer and then delete it for the function to be called again

        """
        return self.initalised

    def begin_aquisition(self):
        """Get frames every fps and add it to the queue"""
        def acquire_images():
            while self.is_streaming():
                # Get the frame
                frame = self.get_next_image()
                self.img_buffer.append(frame)
                # Get the time stamp
                time = self.get_image_timestamp()
                self.time_stamps_buffer.append(time)
                # Get the GPIO data
                gpio_data = self.get_GPIO_data()
                self.gpio_buffer.append(gpio_data)
                cv2.waitKey(int(1000 / int(self.fps)))

        # Start the acquisition in a separate thread
        acquisition_thread = threading.Thread(target=acquire_images)
        acquisition_thread.daemon = True
        acquisition_thread.start()

    def end_aquisition(self):
        """Stops the acquisition process"""
        self.capture.release()


    def get_next_image(self) -> np.ndarray:
        ret, frame = self.capture.read()
        # convert the frame to monochrome if the color is set to false
        # if not self.CameraConfig.color:
        #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame

    def retrieve_buffered_data(self):
        """Since the last time this function was called get all the images"""
        
        # Copy image buffer and clear 
        img_buffer = list(self.img_buffer)
        self.img_buffer.clear()
        
        gpio_buffer = self.gpio_buffer
        self.gpio_buffer.clear()
        
        timestamps_buffer =self.time_stamps_buffer
        self.time_stamps_buffer.clear()
        # Return the copy of the buffer data
        return {
            "images": img_buffer,
            "gpio_data": gpio_buffer,
            "timestamps": timestamps_buffer,
        }


########### Finding Cameras


def list_available_cameras() -> list[str]:
    """Place holder function which returns a list of the available cameras.
    The should be uniquly idenified as a string.
    """
    # Windows 11
    if platform.system() == "Windows":
        usb_cam_list = cv2_enumerate_cameras.enumerate_cameras()
        # Preprocess this list because it returns duplicates sometimtes
        for cam1 in usb_cam_list:
            for cam2 in usb_cam_list:
                if cam1.path == cam2.path:
                    usb_cam_list.remove(cam2)

        unique_id_list = []
        for cam in usb_cam_list:
            cam_id: str = f"{cam.pid}-opencv"
            unique_id_list.append(cam_id)
    # macOS 15.0.1 (24A348)
    elif platform.system() == "Darwin":
        unique_id_list = []
        try:
            for i in range(10):
                cap = cv2.VideoCapture(
                    i, cv2.CAP_AVFOUNDATION
                )  # Use AVFoundation backend for macOS
                if cap.isOpened():
                    unique_id_list.append(str(i) + "-opencv")
                    cap.release()
        except Exception as e:
            pass

    return unique_id_list


def initialise_by_id(_id, CameraSettingsConfig):
    """Function that returns a camera instance based on the _id"""

    return openvcvCamera(unique_id=_id, CameraConfig=CameraSettingsConfig)


if __name__ == "__main__":
    # Code for checking if the functions work
    initialise_by_id(list_available_cameras()[0])
