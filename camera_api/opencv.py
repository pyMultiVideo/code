"""
TODO:
1. Closing the processes which the frames are aquired by properly using the multiprocessing
2. Understanding and fixing why the queue is mostly 2 frames even though it should be lonter sometimes
3. Low resolution output from the cameras (color conversion using cv2?)
4. Opening the camera is slow on the windows computer...
5. Settings and getting camera parameters
"""

import cv2

import multiprocessing
import queue
from signal import signal, SIGTERM
import os
import time
from collections import OrderedDict
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
        self.framerate = 60
        self.N_GPIO = 0  # Number of GPIO pins
        self.manual_control_enabled = False
        self.pixel_format = "RGB"
        self.supported_pixel_formats = OrderedDict(
            [
                ("BayerRG8", "bayer_rggb8"),
                ("Mono8", "gray"),
            ]
        )
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

        self.buffer_size = 100  # Buffer size for Camera process
        self.process = None
        self.buffer = multiprocessing.Queue(maxsize=self.buffer_size)
        self.running = multiprocessing.Value("b", False)  # Initialize running flag

    # Camera Buffer process functions -------------------------------------------------------

    def begin_capturing(self, CameraConfig=None):
        """Start the webcam capture process"""
        self.RUNNING = True
        if self.running.value:
            pass
        else:
            # Only begin capturing if that hasn't already happened
            self.running.value = True
            self.process = multiprocessing.Process(target=self.video_acquisition_process, name="OpenCVCameraProcess")
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
            start_time = time.time()
            ret, frame = self.cap.read()  # The read function could be too slow to keep up with the high framerate
            if ret:
                # Add frame to the queue (circular buffer behaviour)
                if self.buffer.full():
                    print("FRAME DISCARDED")
                    self.buffer.get()  # Discard oldest frame
                image = {}  # Create a dictionary to put thing into the queue
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert frame to monochrome
                image["frame"] = gray_frame.tobytes()  # Frame information as byte array
                image["timestamp"] = int(time.time_ns())  # Computer time stamp in nanoseconds
                self.frame_number = self.frame_number + 1  # Increment frame number
                image["frame_number"] = self.frame_number
                self.buffer.put(image)  # Put image in queue

            elapsed_time = time.time() - start_time
            sleep_time = max(0, (1 / self.framerate) - elapsed_time)
            time.sleep(sleep_time)
            if self.RUNNING == False:
                self.process.terminate()

    def end_video_acquisition_process(self, signum, frame):
        """End the video acquisition process gracefully."""
        self.cap.release()
        self.RUNNING = False

    def stop_capturing(self):
        """Stop capturing frames"""

        self.RUNNING = False
        try:
            self.process.terminate()
            self.process.join(1)
            self.buffer.close()
            self.buffer.join_thread()
        except:
            print("Fail to terminate process")

    # Camera Settings ------------------------------------------------------------

    def get_frame_rate_range(self, exposure_time):
        return 0, 70

    def get_exposure_time_range(self, frame_rate):
        return 0, 20000

    def get_gain_range(self):
        return 0, 10

    def get_exposure_time(self):
        """Get the current exposure time of the camera."""
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
        try:
            while True:
                image = self.buffer.get(block=False, timeout=0)  # Get next image from buffer
                img_buffer.append(image["frame"])  # Get frame
                timestamps_buffer.append(image["timestamp"])  # Get image timestamp
                gpio_buffer.append([])
            # dropped_frames += 1 # Calculate dropped frames
        except:  # Buffer is empty
            print("error raised")
            pass
        # Return images
        if len(img_buffer) == 0:
            print("buffer empty")
            return
        else:
            print("Images returned", len(img_buffer))
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
