from ximea import xiapi

import cv2
import numpy as np
from collections import OrderedDict
from math import floor, ceil

from . import GenericCamera

# Look at the multiple camera example. There is a set_limit_batdwidth method


class XimeaCamera(GenericCamera):
    """Inherits from the camera class and adds the Ximea specific functions from the xiAPI library"""

    def __init__(self, CameraConfig=None):
        super().__init__(self)
        self.unique_id = CameraConfig.unique_id
        # Initialise camera -------------------------------------------------------------
        # pMV Information
        self.serial_number, self.api = self.unique_id.split("-")
        self.N_GPIO = 1  # Number of GPIO pins

        # Open camera by serial number
        self.cam = xiapi.Camera()
        self.cam.open_device_by_SN(self.serial_number)
        self.previous_frame_number = 0
        self.device_model = self.cam.get_device_model_id()

        # Dictionaries for supporting colored cameras -----------------------------------

        # List of color formats Ximea supports
        self.supported_pixel_formats = OrderedDict(
            [
                ("BayerRG8", "bayer_rggb8"),
                ("XI_GenTL_Image_Format_Mono8", "gray"),
            ]
        )
        self.cv2_conversion = {"BayerRG8": cv2.COLOR_BayerRG2BGR, "XI_GenTL_Image_Format_Mono8": cv2.COLOR_GRAY2BGR}
        # Get the pixel format
        self.pixel_format = self.camera_pixel_format()

        # Configure camera settings -----------------------------------------------------

        # Manual Control of camera
        self.cam.disable_aeag()  # Automatic exposure gain disabled
        self.cam.set_acq_timing_mode("XI_ACQ_TIMING_MODE_FRAME_RATE")  # Manual Framerate control
        print(self.cam.get_gpi_level())
        # Configure user settings.
        self.begin_capturing(CameraConfig)
        if CameraConfig is not None:
            self.configure_settings(CameraConfig)

    # Functions to get the camera parameters ----------------------------------------------

    def get_width(self) -> int:
        """Get the width of the camera image in pixels."""
        return self.cam.get_width()

    def get_height(self) -> int:
        """Get the height of the camera image in pixels."""
        return self.cam.get_height()

    def get_frame_rate(self) -> int:
        """Get the camera frame rate in Hz."""
        return self.cam.get_framerate()

    def get_frame_rate_range(self, exposure_time) -> tuple[int, int]:
        """Get the min and max frame rate (Hz)."""
        return ceil(self.cam.get_framerate_minimum()), floor(self.cam.get_framerate_maximum())

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""
        return self.cam.get_exposure()

    def get_exposure_time_range(self, fps) -> tuple[int, int]:
        """Get the min and max exposure time (us)"""
        return ceil(self.cam.get_exposure_minimum()), floor(self.cam.get_exposure_maximum())

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        return self.cam.get_gain()

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        return ceil(self.cam.get_gain_minimum()), floor(self.cam.get_gain_maximum())

    def camera_pixel_format(self) -> str:
        """Get string specifying camera pixel format"""
        # return self.cam.get_param('pixel_format')
        return self.cam.get_transport_pixel_format()

    # Functions to set camera parameters.

    def configure_settings(self, CameraConfig):
        """Configure all settings from CameraConfig."""
        self.set_frame_rate(CameraConfig.fps)
        self.set_gain(CameraConfig.gain)
        self.set_exposure_time(CameraConfig.exposure_time)

    def set_frame_rate(self, frame_rate):
        """Set the frame rate of the camera in Hz indirectly by setting the exposure time."""
        self.cam.set_framerate(float(frame_rate))

    def set_exposure_time(self, exposure_time: float) -> None:
        """Set the exposure time of the camera in microseconds."""
        self.cam.set_exposure(exposure_time)

    def set_gain(self, gain: float):
        """Set gain (dB)"""
        self.cam.set_gain(gain)

    # Functions to control the camera streaming and check status.

    def is_streaming(self):
        """Check if the camera is streaming"""
        try:
            image = xiapi.Image()
            self.cam.get_image(image)
            return True
        except xiapi.Xi_error:
            return False

    def begin_capturing(self, CameraConfig=None) -> None:
        """Start camera streaming images."""
        if not self.cam.CAM_OPEN:
            self.cam.open_device_by_SN(self.serial_number)
            self.previous_frame_number = 0
        if not self.is_streaming():
            self.cam.start_acquisition()
        # Configure the camera camera settigns
        if CameraConfig:
            self.configure_settings(CameraConfig)

    def stop_capturing(self) -> None:
        """Stop the camera from streaming"""
        try:
            self.cam.stop_acquisition()
            self.cam.close_device()
        except:
            print("Error raised closing Ximea API")

    def close_api(self):
        """Close the Ximea API and release resources."""
        self.stop_capturing()

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
                self.cam.get_image(next_image, timeout=0)  # Raise an exception if buffer is empty.
                img_buffer.append(
                    np.frombuffer(next_image.get_image_data_raw(), dtype=np.uint8)
                )  # Add the data as numpy buffer arrays
                timestamps_buffer.append(
                    int(str(next_image.tsSec) + str(next_image.tsUSec) + "000")  # Padded to nanosecond resolution
                )  # Create timestamp for the image
                if self.previous_frame_number != (next_image.acq_nframe - 1):
                    dropped_frames += next_image.acq_nframe - self.previous_frame_number - 1
                self.previous_frame_number = next_image.acq_nframe
                gpio_data.append(
                    [int(self.cam.get_gpi_level())]
                )  # UNTESTED: function that returns GPI level of the single pin input
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


def initialise_camera_api(CameraSettingsConfig):
    """Instantiate the XimeaCamera object based on the unique-id"""
    return XimeaCamera(CameraConfig=CameraSettingsConfig)
