import cv2

import multiprocessing
import numpy as np
from signal import signal, SIGTERM
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
        self.N_GPIO = 0  # Number of GPIO pins
        self.manual_control_enabled = False
        self.pixel_format = "RGB"
        self.pixel_format_map = OrderedDict(
            [
                ("Colour", {"Internal": "BayerRG8", "ffmpeg": "bayer_rggb8", "cv2": cv2.COLOR_BayerRG2BGR}),
                ("Mono", {"Internal": "Mono8", "ffmpeg": "gray", "cv2": cv2.COLOR_GRAY2BGR}),
            ]
        )

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
        self.running = multiprocessing.Value("b", False)  # Initialize running flag

    # Camera Buffer process functions -------------------------------------------------------

    def begin_capturing(self, CameraConfig=None):
        """Start the webcam capture process"""
        if self.running.value:
            pass
        else:
            # Only begin capturing if that hasn't already happened
            self.running.value = True
            self.buffer = multiprocessing.Queue(maxsize=self.buffer_size)
            self.process = multiprocessing.Process(target=self.video_acquisition_process, name="OpenCVCameraProcess")
            self.frame_number = 0
            self.process.start()

    def video_acquisition_process(self, CameraConfig=None):
        """The method that captures frames in a separate process"""
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

    def end_video_acquisition_process(self, signum, frame):
        """End the video acquisition process gracefully."""
        self.cap.release()
        self.buffer.put({"signal": "SIGTERM"})  # Send a termination signal into the queue

    def stop_capturing(self):
        """Stop capturing frames"""
        self.running.value = False

        # Attempt to empty the queue
        try:
            while not self.buffer.empty():
                self.buffer.get_nowait()  # Avoid blocking
        except Exception as e:
            print(f"Error emptying buffer: {e}")

        try:
            # Properly close and join the queue
            self.buffer.close()
            self.buffer.join_thread()
        except Exception as e:
            print(f"Error closing buffer: {e}")

        try:
            if self.process.is_alive():  # Check if process is still running
                self.process.terminate()  # Kill the process
                self.process.join(timeout=2)  # Give it time to close

                if self.process.is_alive():  # If it's still alive, force kill
                    print("Process did not terminate, forcing kill.")
                    self.process.kill()
        except Exception as e:
            print(f"Error terminating process: {e}")

    # Camera Settings ------------------------------------------------------------

    def get_frame_rate_range(self, exposure_time):
        return 0, 30

    def get_exposure_time_range(self, frame_rate):
        return 0, 20000

    def get_gain_range(self):
        return 0, 10

    def get_height(self):
        """Get the height of the frames captured by the camera."""
        return self.height

    def get_width(self):
        """Get the width of the frames captured by the camera."""
        return self.width

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
                if "signal" in image and image["signal"] == "SIGTERM":  # Check for Termination signal
                    self.end_video_acquisition_process(None, None)
                    break
                img_buffer.append(np.frombuffer(image["frame"], dtype=np.uint8).reshape(self.height, self.width))  # Convert frame bytes to numpy array
                timestamps_buffer.append(image["timestamp"])  # Get image timestamp
                gpio_buffer.append([])
            # dropped_frames += 1 # Calculate dropped frames
        except:  # Buffer is empty
            # Return images
            pass
        if len(img_buffer) == 0:
            return
        else:
            return {
                "images": img_buffer,
                "gpio_data": gpio_buffer,
                "timestamps": timestamps_buffer,
                "dropped_frames": dropped_frames,
            }


# Camera system functions -------------------------------------------------------------------------------


def list_available_cameras(VERBOSE=False) -> list[str]:
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


def initialise_camera_api(CameraConfig):
    """Instantiate the OpenCVCamera object based on the CameraSettingsConfig."""
    return OpenCVCamera(CameraConfig=CameraConfig)