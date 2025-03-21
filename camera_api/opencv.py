import cv2

from collections import OrderedDict
import multiprocessing
from signal import signal, SIGTERM
import os
import time
from math import floor, ceil

from . import GenericCamera


class OpenCVCamera(GenericCamera):
    # class OpenCVCamera:
    def __init__(self, CameraConfig=None):
        self.unique_id = CameraConfig.unique_id
        # Initialise camera -------------------------------------------------------------
        # pMV Information
        self.serial_number, self.api = self.unique_id.split("-")
        self.framerate = int(CameraConfig.fps)
        self.N_GPIO = 0  # Number of GPIO pins
        self.pixel_format = "RGB"
        self.cv2_conversion = {"RGB": cv2.COLOR_RGB2BGR, "Mono8": cv2.COLOR_GRAY2BGR}
        self.device_model = "Webcam"
        # Capture one frame to get the height and width
        cap = cv2.VideoCapture(int(self.serial_number))
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                self.height, self.width = frame.shape[:2]
            cap.release()
        else:
            self.height, self.width = None, None

        # Buffers running the camera on a different python process

        self.buffer_size = 10  # Buffer size for Camera process
        self.buffer = multiprocessing.Queue(maxsize=self.buffer_size)
        self.running = multiprocessing.Value("b", False)  # Initialize running flag

    # Camera Buffer process functions -------------------------------------------------------

    def begin_capturing(self, CameraConfig):
        """Start the webcam capture process"""
        print("begin capturing")
        self.running.value = True
        self.process = multiprocessing.Process(target=self.video_acquisition_process)
        self.frame_number = 0
        self.process.start()

    def video_acquisition_process(self, CameraConfig=None):
        """The method that captures frames in a separate process"""
        signal(SIGTERM, self.end_video_acquisition_process)
        # Open the webcam
        self.cap = cv2.VideoCapture(int(self.serial_number))

        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return

        while self.running.value:
            ret, frame = self.cap.read()
            if ret:
                # Add frame to the queue (circular buffer behavior)
                if self.buffer.full():
                    self.buffer.get()  # Discard oldest frame
                image = {}  # Create a dictionary to put thing into the queue
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert frame to monochrome
                image["frame"] = gray_frame.tobytes()  # Frame information as byte array
                image["timestamp"] = int(time.time_ns())  # Computer time stamp in nanoseconds
                self.frame_number = self.frame_number + 1  # Increment frame number
                image["frame_number"] = self.frame_number
                self.buffer.put(image)  # Put image dictionary into queue

            time.sleep(1 / self.framerate)  # Ensure we are acquiring at the specified framerate

    def end_video_acquisition_process(self, *args):
        """End the video acquisition process gracefully."""
        print("running end process")
        self.cap.release()

    def stop_capturing(self):
        """Stop capturing frames"""
        self.running.value = False
        if self.process is not None:
            print("terminating process")
            self.process.terminate()

    def get_frame(self):
        """Get the most recent frame from the queue"""
        if not self.buffer.empty():
            return self.buffer.get()
        else:
            return None

    def get_frame_rate_range(self, exposure_time):
        return 0, 70

    def get_exposure_time_range(self, frame_rate):
        return 0, 20000

    def get_gain_range(self):
        return 0, 10

    def get_exposure_time(self):
        """Get the current exposure time of the camera."""
        if self.process is not None and self.process.is_alive():
            cap = cv2.VideoCapture(self.serial_number)
            exposure_time = cap.get(cv2.CAP_PROP_EXPOSURE)
            cap.release()
            return exposure_time
        else:
            return None

    def get_frame_rate(self):
        return 0

    def get_height(self):
        """Get the height of the frames captured by the camera."""
        return self.height

    def get_width(self):
        """Get the width of the frames captured by the camera."""
        return self.width

    def is_streaming(self):
        """Check if the camera is currently streaming."""
        return self.running.value

    def close_api(self):
        self.stop_capturing()

    # Main function to get images -------------------------------------------------------------------------

    def get_available_images(self):
        """Gets all available images from the buffer and return images GPIO pinstate data and timestamps."""
        img_buffer = []
        timestamps_buffer = []
        gpio_buffer = []
        dropped_frames = 0
        # Get all available images from camera buffer.
        while not self.buffer.empty():
            image = self.buffer.get()  # Get next image from buffer
            img_buffer.append(image["frame"])  # Get frame
            timestamps_buffer.append(image["timestamp"])  # Get image timestamp
            gpio_buffer.append([])
        if len(img_buffer) == 0:  # Buffer is empty
            return
        else:
            return {
                "images": img_buffer,
                "gpio_data": gpio_buffer,
                "timestamps": timestamps_buffer,
                "dropped_frames": dropped_frames,
            }


# Camera system functions -------------------------------------------------------------------------------


def list_available_cameras(VERBOSE=True) -> list[str]:
    """List available webcams using OpenCV."""
    index = 0
    available_cameras = []
    while True:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            available_cameras.append(str(index) + "-opencv")
            if VERBOSE:
                print(f"Camera ID: {index} is available.")
            cap.release()
        else:
            break
        index += 1
    return available_cameras


def initialise_camera_api(CameraSettingsConfig):
    """Instantiate the OpenCVCamera object based on the CameraSettingsConfig."""
    return OpenCVCamera(CameraConfig=CameraSettingsConfig)
