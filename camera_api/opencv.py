import cv2

from collections import OrderedDict
import multiprocessing
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
        self.framerate = CameraConfig.fps
        self.N_GPIO = 3  # Number of GPIO pins
        self.pixel_format = "Mono8"

        # Buffers running the camera on a different python process

        self.buffer_size = 10  # Buffer size for Camera process
        self.buffer = multiprocessing.Queue(maxsize=self.buffer_size)

        self.process = None  # Attribute for WebCam Process
        self.running = multiprocessing.Value("b", False)

    # Camera Buffer process functions -------------------------------------------------------

    def begin_capturing(self, CameraConfig):
        """Start the webcam capture process"""
        print('begin capturing')
        self.running.value = True
        self.process = multiprocessing.Process(target=self.video_acquisition_process, args=(CameraConfig,))
        self.process.start()
        self.previous_frame_number = 0

    def video_acquisition_process(self, CameraConfig=None):
        """The method that captures frames in a separate process"""
        # Open the webcam
        cap = cv2.VideoCapture(int(self.serial_number))
        cap.set(cv2.CAP_PROP_FPS, self.framerate)

        # Set the gain of the camera
        cap.set(cv2.CAP_PROP_GAIN, CameraConfig.gain)
        # Set the exposure time of the camera
        cap.set(cv2.CAP_PROP_EXPOSURE, CameraConfig.exposure_time)

        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        while self.running.value:
            ret, frame = cap.read()
            if ret:
                # Add frame to the queue (circular buffer behavior)
                if self.buffer.full():
                    self.buffer.get()  # Discard oldest frame
                self.buffer.put(frame)
            time.sleep(1 / self.framerate)  # Ensure we are acquiring at the specified framerate

            # Add timestamp to the queue
            if self.timestamp_queue.full():
                self.timestamp_queue.get()  # Discard oldest timestamp
            self.timestamp_queue.put(time.time())

            # Add GPIO data to the queue
            gpio_data = self.read_gpio_data()  # Assuming you have a method to read GPIO data
            if self.gpio_queue.full():
                self.gpio_queue.get()  # Discard oldest GPIO data
            self.gpio_queue.put(gpio_data)

            # Increment frame number and add to the queue
            frame_number = self.frame_number_queue.get() + 1 if not self.frame_number_queue.empty() else 0
            if self.frame_number_queue.full():
                self.frame_number_queue.get()  # Discard oldest frame number
            self.frame_number_queue.put(frame_number)

        cap.release()

    def stop_capturing(self):
        """Stop capturing frames"""
        self.running.value = False
        if self.process is not None:
            self.process.join()

    def get_gpio_data(self):
        """"""
        return [0, 0, 0]

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
        if not self.buffer.empty():
            frame = self.buffer.get()
            self.buffer.put(frame)  # Put it back after getting the height
            return frame.shape[0]
        else:
            return None

    def get_width(self):
        """Get the width of the frames captured by the camera."""
        if not self.buffer.empty():
            frame = self.buffer.get()
            self.buffer.put(frame)  # Put it back after getting the width
            return frame.shape[1]
        else:
            return None

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
        gpio_data = []
        dropped_frames = 0

        # Get all available images from camera buffer.
        while not self.buffer.empty():
            img_buffer.append(self.buffer.get())
            timestamps_buffer.append(self.timestamps_queue.get())
            gpio_data.append(self.gpio_queue.get())
            frame_number = self.frame_number_queue.get()
            if self.previous_frame_number != (frame_number - 1):
                dropped_frames += frame_number - self.previous_frame_number - 1
            self.previous_frame_number = frame_number
            dropped_frames += 1

        return {
            "images": img_buffer,
            "gpio_data": gpio_data,
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


if __name__ == "__main__":
    import time
    from pyinstrument import Profiler

    # Create a profiler object
    profiler = Profiler()

    # Start profiling
    profiler.start()
    available_cameras = list_available_cameras()
    print("Available cameras:", available_cameras)
    profiler.stop()
    profiler.print()

    with open("profile_output.html", "w") as f:
        f.write(profiler.output_html())
