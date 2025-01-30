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
        self.set_buffer_handling_mode()
        self.stream_nodemap = self.cam.GetTLStreamNodeMap()

        self.setupChunkSelector()

        if self.camera_config is not None:
            self.set_frame_rate(self.camera_config.fps)
            self.set_pixel_format(self.camera_config.pxl_fmt)
        else:
            self.fps = self.get_frame_rate()

        # self.exposure_time  = self.get_exposure_time()
        self.width = self.get_width()
        self.height = self.get_height()
        self.gain = self.get_gain()
        self.pxl_fmt = self.get_pixel_format()
        self.bitrate = self.get_bitrate()

    def setupChunkSelector(self):
        """
        Setup the Chunk selector
        """
        self.cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
        self.cam.ChunkEnable.SetValue(True)
        self.cam.ChunkModeActive.SetValue(True)

    # Functions to get the camera parameters

    def get_width(self) -> int:
        """
        This Python function retrieves the width value from a node map using the PySpin library.
        :return: The `get_width` method returns the width value of the camera image as an integer. It
        retrieves the width node from the camera node map and returns its integer value.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("Width")).GetValue()

    def get_height(self) -> int:
        """
        This Python function retrieves the height value from a camera node map.
        :return: The `get_height` method returns the height value of the camera image as an integer. It
        retrieves the height node from the camera node map and returns its integer value.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("Height")).GetValue()

    def get_frame_rate(self) -> int:
        """
        This Python function retrieves the frame rate value from a camera node map.
        :return: The `get_frame_rate` method returns the frame rate value as an integer.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate")).GetValue()

    def get_frame_rate_range(self) -> tuple[int, int]:
        """
        Function that returns a tuple of ints that describes the minimum and maximum framerate

        Returns:
            tuple[int, int]: Minimum framerate and Maximum Frame rate
        """

        node_frame_rate = PySpin.CFloatPtr(
            self.cam.GetNodeMap().GetNode("AcquisitionFrameRate")
        )
        if PySpin.IsAvailable(node_frame_rate) and PySpin.IsReadable(node_frame_rate):
            min_frame_rate = node_frame_rate.GetMin()
            max_frame_rate = node_frame_rate.GetMax()
        else:
            print("Frame rate node is not readable.")

        return min_frame_rate, max_frame_rate

    def get_gain(self) -> int:
        """
        This Python function retrieves the gain value from a camera node map using the PySpin library.
        :return: The `get_gain` method returns the current gain value of the camera.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CFloatPtr(nodemap.GetNode("Gain")).GetValue()

    def get_pixel_format(self) -> str:
        """
        This Python function retrieves the current pixel format of an image using the PySpin library.
        :return: The `get_pixel_format` method returns a string representing the current pixel format of
        the camera. It retrieves the pixel format from the camera's node map and returns the symbolic
        representation of the current pixel format.
        """
        nodemap = self.cam.GetNodeMap()
        return (
            PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
            .GetCurrentEntry()
            .GetSymbolic()
        )

    def get_bitrate(self) -> int:
        """
        This Python function retrieves the bitrate value from a camera node map using the PySpin
        library.
        :return: The `get_bitrate` method returns an integer value representing the bitrate obtained
        from the node "DeviceLinkThroughputLimit" in the camera's node map.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(
            nodemap.GetNode("DeviceLinkThroughputLimit")
        ).GetValue()

    # def get_unique_id(self) -> str:
    #     '''Returns the unique id of the camera that is used in the pyMultiVideo application'''
    #     return self.unique_id

    ## Buffer handling functions

    def set_buffer_handling_mode(self, mode: str = "OldestFirst") -> None:
        """
        Sets the buffer handling mode.

        By default, the buffer handling mode is set to 'OldestFirst'. This means that the oldest image in the buffer is the first to be retrieved.

        Alternative modes are:
        - NewestFirst
        - NewestOnly
        - OldestFirstOverwrite

        See: https://www.teledynevisionsolutions.com/en-gb/support/support-center/application-note/iis/accessing-the-on-camera-frame-buffer/

        For this implementation, use of oldest first is important as the camera releases the images in the order they are collected.
        If the buffer is not emptied in this order then the images will be encoded in the wrong order which is bad

        """
        if mode not in ["OldestFirst"]:
            # Raise a warning if the mode is not set to 'OldestFirst'
            self.logger.warning(f"Buffer handling mode '{mode}' is not 'OldestFirst'.")

        try:
            # Access the Transport Layer Stream (TLStream) node map
            stream_nodemap = self.cam.GetTLStreamNodeMap()

            # Set buffer handling mode
            node_buffer_handling_mode = PySpin.CEnumerationPtr(
                stream_nodemap.GetNode("StreamBufferHandlingMode")
            )

            # Check if the node exists and is writable
            if PySpin.IsAvailable(node_buffer_handling_mode) and PySpin.IsWritable(
                node_buffer_handling_mode
            ):
                node_mode_value = node_buffer_handling_mode.GetEntryByName(
                    mode
                )  # Change to desired mode
                if PySpin.IsAvailable(node_mode_value) and PySpin.IsReadable(
                    node_mode_value
                ):
                    node_buffer_handling_mode.SetIntValue(node_mode_value.GetValue())
                    print(
                        f"Buffer Handling Mode set to: {node_mode_value.GetSymbolic()}"
                    )

        except PySpin.SpinnakerException as ex:
            print(f"Error setting buffer handling mode: {ex}")

    def get_buffer_handling_mode(self) -> str:
        """Function that returns the current buffer handling mode"""
        try:
            # Access the Transport Layer Stream (TLStream) node map
            stream_nodemap = self.cam.GetTLStreamNodeMap()

            # Get buffer handling mode
            node_buffer_handling_mode = PySpin.CEnumerationPtr(
                stream_nodemap.GetNode("StreamBufferHandlingMode")
            )

            # Check if the node exists and is readable
            if PySpin.IsAvailable(node_buffer_handling_mode) and PySpin.IsReadable(
                node_buffer_handling_mode
            ):
                mode = node_buffer_handling_mode.GetCurrentEntry().GetSymbolic()
                print(f"Buffer Handling Mode: {mode}")
                return mode

        except PySpin.SpinnakerException as ex:
            print(f"Error getting buffer handling mode: {ex}")
            return None

    def set_frame_rate(self, frame_rate: int) -> None:
        """
        Function to set the frame rate of the camera.
        """
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

    def get_next_image(self) -> np.ndarray:
        """
        Function to get the next image from the camera (one at a time).

        In the PySpin API, this function is a blocking function. i.e. running this function will stop the rest of the program
        running until is has completed its own task.
        """

        # Check if the camera is not in aquistion mode
        if not self.cam.IsStreaming():
            raise Exception(f"Camera {self.serial_number} is not in acquisition mode.")

        # Get the next image
        next_image = self.cam.GetNextImage()

        # Check if the image is incomplete
        if next_image.IsIncomplete():
            raise Exception("Image is incomplete.")

        # Convert the image to a numpy array
        self.next_image = next_image.GetNDArray()

        # This function is not going to release data from the buffer since it will only be used to display the current image.
        next_image.Release()

        # Return the image
        return self.next_image

    def retrieve_buffered_data(
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
            node_line_selector = PySpin.CEnumerationPtr(
                self.cam.GetNodeMap().GetNode("LineSelector")
            )
            if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsReadable(
                node_line_selector
            ):
                raise Exception("LineSelector node not available.")

            line_entries = node_line_selector.GetEntries()

            self.GPIO_data = {}
            for line_entry in line_entries:
                line_name = line_entry.GetName()

                node_line_status = PySpin.CBooleanPtr(
                    self.cam.GetNodeMap().GetNode("LineStatus")
                )
                if not PySpin.IsAvailable(node_line_status) or not PySpin.IsReadable(
                    node_line_status
                ):
                    raise Exception("LineStatus node not available.")

                line_state = node_line_status.GetValue()
                self.GPIO_data[line_name] = line_state

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
