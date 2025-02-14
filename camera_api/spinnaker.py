import numpy as np
from datetime import datetime
import logging

import PySpin
from . import GenericCamera


class SpinnakerCamera(GenericCamera):
    """Inherits from the camera class and adds the spinnaker specific functions from the PySpin library"""

    def __init__(self, unique_id: str, CameraConfig=None):
        super().__init__(self)
        self.camera_config = CameraConfig
        self.unique_id = unique_id
        self.logger = logging.getLogger(__name__)

        # Initialise camera -------------------------------------------------

        self.system = PySpin.System.GetInstance()
        self.serial_number, self.api = unique_id.split("-")
        self.cam = self.system.GetCameras().GetBySerial(self.serial_number)
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        self.stream_nodemap = self.cam.GetTLStreamNodeMap()
        print("Camera:", self.cam)

        # Configure camera --------------------------------------------------

        # Set Buffer handling mode to Oldest First
        bh_node = PySpin.CEnumerationPtr(self.stream_nodemap.GetNode("StreamBufferHandlingMode"))
        bh_node.SetIntValue(bh_node.GetEntryByName("OldestFirst").GetValue())

        # Configure ChunkData
        self.cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
        self.cam.ChunkEnable.SetValue(True)
        self.cam.ChunkModeActive.SetValue(True)

        # Configure user settings.
        if self.camera_config is not None:
            self.set_frame_rate(self.camera_config.fps)
            self.set_pixel_format(self.camera_config.pxl_fmt)

        # Set frame rate control to manual.
        fra_node = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionFrameRateAuto"))
        fra_node.SetIntValue(fra_node.GetEntryByName("Off").GetValue())
        frc_node = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnabled"))
        frc_node.SetValue(True)

    # Functions to get the camera parameters ----------------------------------------------

    def get_width(self) -> int:
        """Get the width of the camera image in pixels."""
        return PySpin.CIntegerPtr(self.nodemap.GetNode("Width")).GetValue()

    def get_height(self) -> int:
        """Get the height of the camera image in pixels."""
        return PySpin.CIntegerPtr(self.nodemap.GetNode("Height")).GetValue()

    def get_frame_rate(self) -> int:
        """Get the camera frame rate in Hz."""
        return PySpin.CFloatPtr(self.nodemap.GetNode("AcquisitionFrameRate")).GetValue()

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Get the min and max frame rate in Hz."""
        node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("AcquisitionFrameRate"))
        return node.GetMin(), node.GetMax()

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        return PySpin.CFloatPtr(self.nodemap.GetNode("Gain")).GetValue()

    def get_pixel_format(self) -> str:
        """Get string specifying camera pixel format"""
        return PySpin.CEnumerationPtr(self.nodemap.GetNode("PixelFormat")).GetCurrentEntry().GetSymbolic()

    def get_available_pixel_fmt(self) -> list[str]:
        """Gets a string of the pixel formats available to the camera"""

        # Get available framerates
        node_map = self.cam.GetNodeMap()
        pixel_format_node = PySpin.CEnumerationPtr(node_map.GetNode("PixelFormat"))
        pixel_format_entries = pixel_format_node.GetEntries()

        # Convert to string
        available_pxl_fmts = []
        for entry in pixel_format_entries:
            entry = PySpin.CEnumEntryPtr(entry)
            available_pxl_fmts.append(entry.GetSymbolic())

        # Return list
        return available_pxl_fmts

    # Functions to set camera paramteters.

    def set_frame_rate(self, frame_rate: int) -> None:
        """Set the frame rate of the camera."""
        ## Make sure that frame rate is an int
        if type(frame_rate) is str:
            frame_rate = int(frame_rate)
        try:
            # Set frame rate value
            node_frame_rate = PySpin.CFloatPtr(self.nodemap.GetNode("AcquisitionFrameRate"))
            node_frame_rate.SetValue(frame_rate)
            print(f"Frame rate set to {frame_rate} FPS.")
        except PySpin.SpinnakerException as ex:
            print(f"Error Setting Frame Rate: {ex}")

    def set_pixel_format(self, pixel_format):
        pass

    # Functions to control the camera streaming and check status.

    def begin_capturing(self) -> None:
        """Start camera streaming images."""
        try:
            # initialize the camera if it is not already initialized
            if not self.cam.IsInitialized():
                self.cam.Init()
                print(f"Camera {self.serial_number} has been initialized.")
            if not self.cam.IsStreaming():
                self.cam.BeginAcquisition()
                print(f"Camera {self.serial_number} is in acquisition mode.")
            print(f"Begin capturing: {self.serial_number}")
        except PySpin.SpinnakerException as e:
            self.logger.error(f"Error during begin capturing: {e}")
            print(f"Error during begin capturing: {e}")
            raise

    def stop_capturing(self) -> None:
        """Stop the camera from streaming"""
        if self.cam.IsStreaming():
            print(f"Camera {self.serial_number} has stopped aquisiton.")
            self.cam.EndAcquisition()
        if self.cam.IsInitialized():
            self.cam.DeInit()
            print(f"Camera {self.serial_number} has been deinitialized.")
        # make sure to release the camera

    def is_initialized(self) -> bool:
        """Check if the camera is initialised"""
        return self.cam.IsInitialized()

    def is_streaming(self) -> bool:
        """Check if the camera is streaming"""
        return self.cam.IsStreaming()

    # Function to aquire images from the camera

    def get_available_images(
        self,
    ) -> dict[list[np.ndarray], list[dict[str, bool]], list[int]]:
        """
        Gets all available images from the buffer and returns a list of images and corresponding lists
        of the GPIO pinstate data and timestamps.
        """
        self.img_buffer = []
        self.gpio_buffer = []
        self.timestamps_buffer = []
        # Get LineStatus from the nodemap
        line_status = PySpin.CIntegerPtr(self.nodemap.GetNode("LineStatusAll")).GetValue()
        line_status_binary = format(line_status, "04b")  # Convert to 4 bit binary array.
        # Get all available images from buffer.
        try:
            call_count = 0
            while True:
                next_image = self.cam.GetNextImage(0)  # Raises exception if buffer empty.
                image_pixels = next_image.GetNDArray()  # Image pixels as numpy array.
                chunk_data = next_image.GetChunkData()  # Additional image data.
                img_time_stamp = chunk_data.GetTimestamp()  # Image timestamp (ns?)
                next_image.Release()  # Clears image from buffer.
                # Append to lists
                self.img_buffer.append(image_pixels)
                self.gpio_buffer.append(
                    {
                        "Line0": int(line_status_binary[0]),
                        "Line1": int(line_status_binary[1]),
                        "Line2": int(line_status_binary[3]),
                    }
                )
                self.timestamps_buffer.append(img_time_stamp)
                call_count += 1
        except PySpin.SpinnakerException:
            # When the buffer is empty, the 'GetNextImage' function will raise an exception.
            if call_count > 1:
                print(f"Multiple images aquired between calls:{call_count}")
            return {
                "images": self.img_buffer,
                "gpio_data": self.gpio_buffer,
                "timestamps": self.timestamps_buffer,
            }


# Camera system functions -------------------------------------------------------------------------------


def list_available_cameras(VERBOSE=False) -> list[str]:
    """PySpin specific implementation of getting a list of serial numbers from all the pyspin cameras"""
    unique_id_list = []
    pyspin_system = PySpin.System.GetInstance()
    pyspin_cam_list = pyspin_system.GetCameras()

    if VERBOSE:
        print(f"Number of cameras detected: {pyspin_cam_list.GetSize()}")

    for cam in pyspin_cam_list:
        try:
            # Initialize the camera
            cam.Init()
            # Get cam serial number
            cam_id: str = f"{cam.DeviceSerialNumber()}-spinnaker"
            if VERBOSE:
                print(f"Camera ID: {cam_id}")
            unique_id_list.append(cam_id)
        except Exception as e:
            if VERBOSE:
                print(f"Error accessing camera: {e}")
        finally:
            if cam.IsStreaming():
                continue
            else:
                cam.DeInit()

    # Release resources
    pyspin_cam_list.Clear()

    return unique_id_list


def initialise_by_id(_id, CameraSettingsConfig):
    """Instantiate the SpinnakerCamera object based on the unique-id"""
    return SpinnakerCamera(unique_id=_id, CameraConfig=CameraSettingsConfig)
