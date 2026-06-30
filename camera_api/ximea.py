from ximea import xiapi

import cv2
import numpy as np
from math import floor, ceil

from .generic_camera import GenericCamera

# Look at the multiple camera example. There is a set_limit_bandwidth method that could cause problems.


class XimeaCamera(GenericCamera):
    """Inherits from the camera class and adds the Ximea specific functions from the xiAPI library"""

    def __init__(self, CameraConfig=None):
        if CameraConfig is None:
            raise ValueError("CameraConfig is required to initialize XimeaCamera")

        super().__init__(CameraConfig)
        self.unique_id = CameraConfig.unique_id
        # Initialise camera -------------------------------------------------------------
        # pMV Information
        self.serial_number, self._api = self.unique_id.split("-")
        self.N_GPIO = 1  # Number of GPIO pins
        self.manual_control_enabled = True
        # Open camera by serial number
        self._cam = xiapi.Camera()
        self._cam.open_device_by_SN(self.serial_number)
        self._previous_frame_number = 0
        self.device_model = self._cam.get_device_model_id()
        self.image_width = self._cam.get_width()
        self.image_height = self._cam.get_height()
        # Dictionaries for supporting colored cameras -----------------------------------

        self.pixel_format_map = {  # List of color formats Ximea supports
            "Colour": {
                "Internal": "BayerRG8",
                "ffmpeg": "bayer_rggb8",
                "cv2": cv2.COLOR_BayerRG2BGR,
            },
            "Mono": {
                "Internal": "XI_GenTL_Image_Format_Mono8",
                "ffmpeg": "gray",
                "cv2": cv2.COLOR_GRAY2BGR,
            },
        }
        # Get the pixel format
        self._pixel_format = self._get_camera_pixel_format()

        # Configure camera settings -----------------------------------------------------
        # Manual Control of camera
        self._cam.disable_aeag()  # Automatic exposure gain disabled
        self._cam.set_acq_timing_mode("XI_ACQ_TIMING_MODE_FRAME_RATE")  # Manual Framerate control

        # Configure user settings.
        # self.begin_capturing(CameraConfig)

        print(f"Ximea camera {self.serial_number} initialised")

    # Functions to get the camera parameters ----------------------------------------------

    def get_frame_rate_range(self, *exposure_time) -> tuple[int, int]:
        """Get the min and max frame rate (Hz)."""
        try:
            return ceil(self._cam.get_framerate_minimum()), floor(self._cam.get_framerate_maximum())
        except xiapi.Xi_error:
            if exposure_time:
                max_frame_rate = 1e6 / exposure_time[0]  # Use the first value of the tuple
                return ceil(1), floor(max_frame_rate)
            else:
                raise ValueError("Exposure time must be provided to calculate frame rate range.")

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""
        return self._cam.get_exposure()

    def get_exposure_time_range(self, *fps) -> tuple[int, int]:
        """Get the min and max exposure time (us)"""
        try:
            return ceil(self._cam.get_exposure_minimum()), floor(self._cam.get_exposure_maximum())
        except xiapi.Xi_error:
            max_exposure_time = 1e6 / fps[0] + 8  # Systematically underestimate maximum since init will fail if too big
            return ceil(7), floor(max_exposure_time)

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        return self._cam.get_gain()

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        return ceil(self._cam.get_gain_minimum()), floor(self._cam.get_gain_maximum())

    def _get_camera_pixel_format(self) -> str:
        """Get string specifying camera pixel format"""
        return self._cam.get_transport_pixel_format()

    # Functions to set camera parameters --------------------------------------------------------

    def set_frame_rate(self, frame_rate):
        """Set the frame rate of the camera in Hz indirectly by setting the exposure time."""
        self._cam.set_framerate(float(frame_rate))

    def set_exposure_time(self, exposure_time: float) -> None:
        """Set the exposure time of the camera in microseconds."""
        self._cam.set_exposure(exposure_time)

    def set_gain(self, gain: float):
        """Set gain (dB)"""
        self._cam.set_gain(gain)

    def set_pixel_format(self, pixel_format: str):
        """Set pixel format if backend supports it; otherwise keep current format."""
        print("Setting pixel format not implemented for Ximea cameras. Current pixel format:", self._pixel_format)

    # Configuring Acqusition mode -----------------------------------------------------------------

    def set_acqusition_mode(self, external_trigger: bool):
        """Setting the camera to external triggering or not"""
        was_streaming = self._is_streaming()  # Check if the camera was streaming initially
        if external_trigger:
            if was_streaming:
                self._cam.stop_acquisition()
            self._cam.set_trigger_source("XI_TRG_EDGE_RISING")  # Turn Trigger back on
            self._cam.set_trigger_selector("XI_TRG_SEL_FRAME_START")  # Trigger on frame start
            self._cam.set_acq_frame_burst_count(1)  # Single frame acquisition mode
        else:  # Turn off external trigger mode in case it is already enabled
            if was_streaming:
                self._cam.stop_acquisition()
            self._cam.set_trigger_source("XI_TRG_OFF")

        # Restart acquisition if it was streaming initially
        if was_streaming:
            self._cam.start_acquisition()

    # Functions to control the camera streaming and check status.

    def _is_streaming(self):
        """Check if the camera is streaming"""
        try:
            image = xiapi.Image()
            self._cam.get_image(image)
            return True
        except xiapi.Xi_error:
            return False

    def begin_capturing(self, CameraConfig=None) -> None:
        """Begin streaming images from the camera and configuring acquisition settings.
        Acqusition mode set before acquisition begins. All others are applied afterwards."""
        # Configure the camera settings
        if not self._cam.CAM_OPEN:
            self._cam.open_device_by_SN(self.serial_number)
            self._previous_frame_number = 0
        if CameraConfig:
            self.set_acqusition_mode(CameraConfig.external_trigger)
        if not self._is_streaming():
            try:
                self._cam.start_acquisition()
            except xiapi.Xi_error as e:
                print("Error starting acqusition:", e)
        if CameraConfig:
            self.set_frame_rate(CameraConfig.fps)
            self.set_gain(CameraConfig.gain)
            self.set_exposure_time(CameraConfig.exposure_time)
            self.set_pixel_format(CameraConfig.pixel_format)

    def stop_capturing(self) -> None:
        """Stop the camera from streaming"""
        try:
            self._cam.stop_acquisition()
        except xiapi.Xi_error:
            pass

    def close(self):
        """Close the Ximea API and release resources."""
        self.stop_capturing()
        try:
            if self._cam.CAM_OPEN:
                self._cam.close_device()
        except xiapi.Xi_error:
            pass

    def get_available_images(self):
        """Gets all available images from the buffer and return images GPIO pinstate data and timestamps."""
        img_buffer = []
        timestamps_buffer = []
        gpio_data = []
        dropped_frames = 0
        # Get all available images from camera buffer.
        try:
            while True:
                next_image = xiapi.Image()  # img class to put data into
                self._cam.get_image(next_image, timeout=0)  # Raise an exception if buffer is empty.
                # Add the image data to the image buffer as a 1D numpy array of bytes.
                img_buffer.append(np.frombuffer(next_image.get_image_data_raw(), dtype=np.uint8))
                # Add image timestamp to timestamp buffer.
                timestamps_buffer.append(next_image.tsSec * 1000000 + next_image.tsUSec)  # Microseconds.
                # Calcuate number of dropped frames.
                dropped_frames += next_image.acq_nframe - self._previous_frame_number - 1
                self._previous_frame_number = next_image.acq_nframe
                # Get state of GPIO pin and add to GPIIO data buffer [UNTESTED].
                gpio_data.append([int(self._cam.get_gpi_level())])
        except xiapi.Xi_error:  # Buffer is empty.
            if len(img_buffer) == 0:
                return
            else:
                return {
                    "images": img_buffer,
                    "gpio_data": gpio_data,
                    "timestamps": timestamps_buffer,
                    "dropped_frames": dropped_frames,
                }


# Camera system functions -------------------------------------------------------------------------------


def list_available_cameras(VERBOSE=False) -> list[str]:
    """Ximea specific implementation of getting a list of serial numbers from all the Ximea cameras"""
    cam = xiapi.Camera()
    num_devices = cam.get_number_devices()

    if VERBOSE:
        print(f"Number of cameras detected: {num_devices}")
    unique_id_list = []
    for idx in range(num_devices):
        try:
            cam = xiapi.Camera(dev_id=idx)
            cam_id: str = f"{cam.get_device_info_string('device_sn').decode('utf-8')}-ximea"
            if VERBOSE:
                print(f"Camera ID: {cam_id}")
            unique_id_list.append(cam_id)
        except Exception as e:
            if VERBOSE:
                print(f"Error accessing camera: {e}")
        finally:
            if cam.CAM_OPEN:
                cam.close_device()

    return unique_id_list


def initialise_camera_api(CameraConfig):
    """Instantiate the XimeaCamera object"""
    return XimeaCamera(CameraConfig=CameraConfig)
