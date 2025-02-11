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
        # Logger
        self.logger = logging.getLogger(__name__)
        self.system = PySpin.System.GetInstance()
        self.unique_id = unique_id
        self.serial_number, self.api = unique_id.split("-")
        self.cam = self.system.GetCameras().GetBySerial(self.serial_number)


        print("Camera:", self.cam)
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        self.stream_nodemap = self.cam.GetTLStreamNodeMap()
        self.set_buffer_handling_mode("OldestFirst")


        self.setupChunkSelector()

        if self.camera_config is not None:
            self.set_frame_rate(self.camera_config.fps)
            self.set_pixel_format(self.camera_config.pxl_fmt)
        else:
            self.fps = self.get_frame_rate()

        self.width = self.get_width()
        self.height = self.get_height()
        self.gain = self.get_gain()
        self.pxl_fmt = self.get_pixel_format()

    def setupChunkSelector(self):
        """
        Setup the Chunk selector
        """
        self.cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
        self.cam.ChunkEnable.SetValue(True)
        self.cam.ChunkModeActive.SetValue(True)

    # Functions to get the camera parameters

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
        return (
            PySpin.CEnumerationPtr(self.nodemap.GetNode("PixelFormat"))
            .GetCurrentEntry()
            .GetSymbolic()
        )

    ## Buffer handling functions

    def set_buffer_handling_mode(self, mode: str = "OldestFirst") -> None:
        """
        Sets the buffer handling mode. Default mode 'OldestFirst' means that the oldest image in the
        buffer is the first to be retrieved.  Alternative modes are:

        - NewestFirst
        - NewestOnly
        - OldestFirstOverwrite

        See: https://www.teledynevisionsolutions.com/en-gb/support/support-center/application-note/iis/accessing-the-on-camera-frame-buffer/
        """
        try:
            node = PySpin.CEnumerationPtr(self.stream_nodemap.GetNode("StreamBufferHandlingMode"))
            node.SetIntValue(node.GetEntryByName(mode).GetValue())
        except PySpin.SpinnakerException as ex:
            print(f"Error setting buffer handling mode: {ex}")



    def set_frame_rate(self, frame_rate: int) -> None:
        """Set the frame rate of the camera."""
        ## Make sure that frame rate is an int
        if type(frame_rate) is str:
            frame_rate = int(frame_rate)

        nodemap = self.cam.GetNodeMap()

        try:
            # Disable automatic frame rate control if applicable
            if PySpin.IsAvailable(
                nodemap.GetNode("AcquisitionFrameRateEnable")
            ) and PySpin.IsWritable(nodemap.GetNode("AcquisitionFrameRateEnable")):
                node_acquisition_frame_rate_enable = PySpin.CBooleanPtr(
                    nodemap.GetNode("AcquisitionFrameRateEnable")
                )
                node_acquisition_frame_rate_enable.SetValue(True)
                print("Frame rate control enabled.")

            # Set frame rate value
            node_frame_rate = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
            if PySpin.IsAvailable(node_frame_rate) and PySpin.IsWritable(
                node_frame_rate
            ):
                node_frame_rate.SetValue(frame_rate)
                print(f"Frame rate set to {frame_rate} FPS.")
            else:
                print("Frame rate control is not available.")

        except PySpin.SpinnakerException as ex:
            print(f"Error Setting Frame Rate: {ex}")

    def get_available_pixel_fmt(self) -> list[str]:
        """Gets a string of the pixel formats available to the camera"""

        available_pxl_fmts = []

        node_map = self.cam.GetNodeMap()
        pixel_format_node = PySpin.CEnumerationPtr(node_map.GetNode("PixelFormat"))

        if not PySpin.IsAvailable(pixel_format_node) or not PySpin.IsReadable(
            pixel_format_node
        ):
            print("PixelFormat node is not available or readable.")
        else:
            pixel_format_entries = pixel_format_node.GetEntries()
            for entry in pixel_format_entries:
                entry = PySpin.CEnumEntryPtr(entry)
                if PySpin.IsReadable(entry):
                    available_pxl_fmts.append(entry.GetSymbolic())
        print(available_pxl_fmts)
        return available_pxl_fmts

    def set_pixel_format(self, pixel_format):
        pass

    # Function to aquire images from the camera

    def begin_capturing(self) -> None:
        """BUG: without the try except block, the program crashes when a config file is loaded for the second time.
        The except loops fixes this problem. however, the error is not caught.
        """
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

    def get_available_images(
        self,
    ) -> dict[list[np.ndarray], list[dict[str, bool]], list[int]]:
        """
        This function returns a list of images and a corresponding list of the GPIO data
        This is passed to a function that will saved the data to a file in batches of the lengths of theses lists.


        How this function works
        =======================
        self.cam.GetNextImage() is a blocking function. This means that it will wait until the next image is available before returning.
        The '0' argument in the GetNextImage() function is the timeout. This is set to 0 to make the function non-blocking.
        It will therefore get images as fast as possible. If there are no images available, the function will raise an exception.
        This is the signal that the buffer is empty.

        We handle the exception and return the buffer of images (and corresponding GPIO data). This is sent the encoder in the main logic of the GUI.


        The format of the GPIO pin states is a dictionary. Therefore the data itself is the dict.value() of this dictionary.
        The current implemenation requires that you are just sending the GPIO data to the function that saves it to disk.
        The writer function requires a list of bools to be passed to it.
        """
        self.img_buffer = []
        self.gpio_buffer = []
        self.timestamps_buffer = []
        try:
            while True:
                # Get the next image
                next_image = self.cam.GetNextImage(0)
                # Get information about the image

                next_image.Release()
                self.img_buffer.append(next_image.GetNDArray())
                # Get the GPIO data
                self.gpio_buffer.append(list(self.get_GPIO_data().values()))
                # Get chunk data
                self.timestamps_buffer.append(
                    self.get_image_time_stamp(next_image=next_image)
                )

        except PySpin.SpinnakerException as e:
            # When the buffer is empty, the 'GetNextImage' function will raise an exception.
            # This marks the end of the buffer.
            # print(f'PySpin Exeception Raised {e}. The buffer has been emptied.')
            pass
        finally:
            return {
                "images": self.img_buffer,
                "gpio_data": self.gpio_buffer,
                "timestamps": self.timestamps_buffer,
            }

    def get_image_time_stamp(self, next_image) -> datetime:
        """Function for getting the timestamp of an image as a datetime object"""
        chunk_data = next_image.GetChunkData()
        # Convert to datetime-readable number
        time_stamp_int = chunk_data.GetTimestamp() / 1e9
        # return the datetime object
        return datetime.fromtimestamp(time_stamp_int)

    def stop_capturing(self) -> None:
        if self.cam.IsStreaming():
            print(f"Camera {self.serial_number} has stopped aquisiton.")
            self.cam.EndAcquisition()
        if self.cam.IsInitialized():
            self.cam.DeInit()
            print(f"Camera {self.serial_number} has been deinitialized.")
        # make sure to release the camera

    def get_GPIO_data(self) -> dict[str, bool]:
        "Get the GPIO data from the camera"

        try:
            nodemap = self.cam.GetNodeMap()

            # Access the EventLine0AnyEdgeTimestamp node (replace with the correct name if different)
            line_status = PySpin.CIntegerPtr(nodemap.GetNode('LineStatusAll'))

            if line_status is None:
                print("GPIO data not available.")
                return

            # Retrieve the timestamp (it might be in microseconds or a similar unit)
            timestamp_value = line_status.GetValue()
            # Pad the timestamp to 8-bit binary
            timestamp_binary = format(timestamp_value, '04b')
            # print(f"(4-bit binary): {timestamp_binary}")

            # Create a dictionary to store the outputs
            self.GPIO_data = {
                'Line0': bool(int(timestamp_binary[0])),
                'Line1': bool(int(timestamp_binary[1])),
                'Line2': bool(int(timestamp_binary[2])),
                'Line3': bool(int(timestamp_binary[3]))
            }


        except PySpin.SpinnakerException as e:
            print(f"Spinnaker error occurred: {e}")
        except Exception as e:
            print(f"General error: {e}")

        except Exception as e:
            self.logger.error(f"Error getting GPIO data: {e}")

        return self.GPIO_data

    def is_initialized(self) -> bool:
        return self.cam.IsInitialized()

    def is_streaming(self) -> bool:
        return self.cam.IsStreaming()

    def trigger_start_recording(self) -> bool:
        """Function that sends a signal to trigger recording if the output of this function is True.
        This function will be called from by a refresh function enough times to be fast enough to start recording if required.

        For this camera, the recording will be triggered by one of the GPIO line states being set to High.

        In principle this function could do anything to start recording by doing something that means this function returns True.
        
        This could also be triggered by a pattern of vSync pulses that are triggered by pyControl to the GPIO pins. This function could look for the trigger that could be send from a hardware definition's file from pyControl custom camera hardware class. 
        """
        return False

    def trigger_stop_recording(self) -> bool:
        """Conceptually same as above. This function is called if the camera is recording, and will take the outcome of this function (True / False) as a Trigger to stop recording"""
        return False


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


if __name__ == "__main__":
    pass
