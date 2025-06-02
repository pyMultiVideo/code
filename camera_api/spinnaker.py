import PySpin
import cv2
from collections import OrderedDict
from math import floor, ceil
from . import GenericCamera


PYSPINSYSTEM = PySpin.System.GetInstance()  # One PySpin system instance per pMV


class SpinnakerCamera(GenericCamera):
    """Inherits from the camera class and adds the spinnaker specific functions from the PySpin library"""

    def __init__(self, CameraConfig=None):
        super().__init__(self)
        self.unique_id = CameraConfig.unique_id

        # Options for camera -----------------------------------------------------------

        self.serial_number, self.api = self.unique_id.split("-")
        self.N_GPIO = 3  # Number of GPIO pins
        self.manual_control_enabled = True
        self.trigger_line = 2  # Trigger line name
        self.previous_frame_number = 0
        # Initialise camera -------------------------------------------------------------
        self.cam_list = PYSPINSYSTEM.GetCameras()
        self.cam = next(
            (cam for cam in self.cam_list if cam.TLDevice.DeviceSerialNumber.GetValue() == self.serial_number), None
        )
        self.device_model = self.cam.TLDevice.DeviceModelName.GetValue()[:10]
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        self.stream_nodemap = self.cam.GetTLStreamNodeMap()

        # Dictionaries for supporting colored cameras -----------------------------------

        # List of color formats pMV supports listed in order or priority. Prioritise Color.
        self.pixel_format_map = OrderedDict(
            [
                ("Mono", {"Internal": "Mono8", "ffmpeg": "gray", "cv2": cv2.COLOR_GRAY2BGR}),
                ("Colour", {"Internal": "BayerRG8", "ffmpeg": "bayer_rggb8", "cv2": cv2.COLOR_BayerRG2BGR}),
            ]
        )

        self.pixel_format = self.get_supported_pixel_formats()
        # Set the pixel format
        self.set_pixel_format(self.pixel_format)

        # Configure camera settings -----------------------------------------------------

        # Set Buffer handling mode to OldestFirst and buffer size to 100 frames.
        bh_node = PySpin.CEnumerationPtr(self.stream_nodemap.GetNode("StreamBufferHandlingMode"))
        bh_node.SetIntValue(bh_node.GetEntryByName("OldestFirst").GetValue())
        sbc_node = PySpin.CIntegerPtr(self.stream_nodemap.GetNode("StreamBufferCountManual"))
        sbc_node.SetValue(100)  # Set buffer size to 100 frames.
        # Configure ChunkData to include frame count and timestamp.
        chunk_selector = PySpin.CEnumerationPtr(self.nodemap.GetNode("ChunkSelector"))
        if self.device_model == "Chameleon3":
            chunk_selector.SetIntValue(chunk_selector.GetEntryByName("FrameCounter").GetValue())
            self.cam.ChunkEnable.SetValue(True)
            # Configure camera to embed GPIO pinstate in image data.
            FRAME_INFO_REG = 0xFFFFF0F012F8
            reg_read = self.cam.ReadPort(FRAME_INFO_REG)
            reg_write = (reg_read & 0xFFFFFC00) + 0x3FF
            self.cam.WritePort(FRAME_INFO_REG, reg_write)
        else:
            # Frame Counter
            chunk_selector.SetIntValue(chunk_selector.GetEntryByName("FrameID").GetValue())
            self.cam.ChunkEnable.SetValue(True)
            # GPIO Pin state
            chunk_selector.SetIntValue(chunk_selector.GetEntryByName("ExposureEndLineStatusAll").GetValue())
            self.cam.ChunkEnable.SetValue(True)

        chunk_selector.SetIntValue(chunk_selector.GetEntryByName("Timestamp").GetValue())
        self.cam.ChunkEnable.SetValue(True)
        self.cam.ChunkModeActive.SetValue(True)

        # Acqusition mode continuous
        acq_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionMode"))
        acq_mode.SetIntValue(acq_mode.GetEntryByName("Continuous").GetValue())

        # Set Exposure to manual
        exc_node = PySpin.CEnumerationPtr(self.nodemap.GetNode("ExposureAuto"))
        exc_node.SetIntValue(PySpin.ExposureAuto_Off)
        # Set Gain to manual
        gnc_node = PySpin.CEnumerationPtr(self.nodemap.GetNode("GainAuto"))
        gnc_node.SetIntValue(PySpin.GainAuto_Off)

        # Configure user settings.
        if CameraConfig is not None:
            self.configure_settings(CameraConfig)

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

    def get_frame_rate_range(self, *exposure_time) -> tuple[int, int]:
        """Get the min and max frame rate (Hz)."""
        try:
            node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("AcquisitionFrameRate"))
            return ceil(node.GetMin()), floor(node.GetMax())
        except PySpin.SpinnakerException:
            if exposure_time:
                max_frame_rate = 1e6 / exposure_time[0]  # Use the first value of the tuple
                return ceil(1), floor(max_frame_rate)
            else:
                raise ValueError("Exposure time must be provided to calculate frame rate range.")

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""
        return float(PySpin.CFloatPtr(self.nodemap.GetNode("ExposureTime")).GetValue())

    def get_exposure_time_range(self, *fps) -> tuple[int, int]:
        """Get the min and max exposure time (us)"""
        try:
            node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("ExposureTime"))
            return ceil(node.GetMin()), floor(node.GetMax())
        except PySpin.SpinnakerException:
            max_exposure_time = 1e6 / fps[0] + 8  # Systematically underestimate maximum since init will fail if too big
            return ceil(7), floor(max_exposure_time)

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        return PySpin.CFloatPtr(self.nodemap.GetNode("Gain")).GetValue()

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("Gain"))
        return ceil(node.GetMin()), floor(node.GetMax())

    def camera_pixel_format(self) -> str:
        """Get string specifying camera pixel format"""
        return PySpin.CEnumerationPtr(self.nodemap.GetNode("PixelFormat")).GetCurrentEntry().GetSymbolic()

    def get_supported_pixel_formats(self):
        """Gets a string of the pixel formats available to the camera"""

        # Get available pixel formats
        node_map = self.cam.GetNodeMap()
        pixel_format_node = PySpin.CEnumerationPtr(node_map.GetNode("PixelFormat"))
        pixel_format_entries = pixel_format_node.GetEntries()

        # Convert to string and check if available
        pxl_formats = []
        for entry in pixel_format_entries:
            entry = PySpin.CEnumEntryPtr(entry)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                pxl_formats.append(str(entry.GetSymbolic()))

        # Get the pixel format that we want the camera to use.
        pixel_format = next(
            (fmt["Internal"] for fmt in self.pixel_format_map.values() if fmt["Internal"] in pxl_formats),
            None,
        )

        if pixel_format is None:
            raise ValueError("No supported pixel format available.")

        return pixel_format

    # Configure Camera for external acqusition

    def set_acqusition_mode(self, external_trigger: bool):

        if external_trigger:
            # Ensure trigger mode is off before configuring
            trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("TriggerMode"))
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("Off").GetValue())

            # Set TriggerSelector to FrameStart
            trigger_selector = PySpin.CEnumerationPtr(self.nodemap.GetNode("TriggerSelector"))
            trigger_selector.SetIntValue(trigger_selector.GetEntryByName("FrameStart").GetValue())

            # Configure the trigger source to the specified line
            trigger_source = PySpin.CEnumerationPtr(self.nodemap.GetNode("TriggerSource"))
            trigger_source.SetIntValue(trigger_source.GetEntryByName("Line" + str(self.trigger_line)).GetValue())

            # Set the trigger activation to RisingEdge
            trigger_activation = PySpin.CEnumerationPtr(self.nodemap.GetNode("TriggerActivation"))
            trigger_activation.SetIntValue(trigger_activation.GetEntryByName("RisingEdge").GetValue())

            # Turn trigger mode back on
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("On").GetValue())

        else:  # Internal triggering
            # Ensure that the trigger mode is off so manual camera control is enabled
            trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("TriggerMode"))
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("Off").GetValue())
            # Set frame rate control to manual.
            if self.device_model == "Chameleon3":
                frc_node = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnabled"))
                frc_node.SetValue(True)
                fra_node = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionFrameRateAuto"))
                fra_node.SetIntValue(fra_node.GetEntryByName("Off").GetValue())
            else:
                fra_node = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnable"))
                fra_node.SetValue(True)

    def get_trigger_lines(self):
        """Get a list of the GPI lines that can be used to trigger frame acquisition"""
        trigger_lines = []
        try:
            line_selector = PySpin.CEnumerationPtr(self.nodemap.GetNode("LineSelector"))
            for entry in line_selector.GetEntries():
                entry = PySpin.CEnumEntryPtr(entry)
                if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                    line_name = entry.GetSymbolic()
                    if "Line" in line_name:
                        trigger_lines.append(line_name)
        except PySpin.SpinnakerException as e:
            print(f"Error retrieving trigger lines: {e}")
        return trigger_lines

    # Functions to set camera paramteters ------------------------------------------------------------------------

    def configure_settings(self, CameraConfig):
        """Configure all settings from CameraConfig."""
        self.set_acqusition_mode(CameraConfig.external_trigger)
        if CameraConfig.external_trigger:
            pass
        else:
            self.set_frame_rate(CameraConfig.fps)
        self.set_gain(CameraConfig.gain)
        self.set_exposure_time(CameraConfig.exposure_time)

    def set_frame_rate(self, frame_rate):
        """Set the frame rate of the camera in Hz."""
        PySpin.CFloatPtr(self.nodemap.GetNode("AcquisitionFrameRate")).SetValue(int(frame_rate))
        self.inter_frame_interval = int(1e9 // int(frame_rate))  # (nanoseconds)

    def set_exposure_time(self, exposure_time: float) -> None:
        """Set the exposure time of the camera in microseconds."""
        PySpin.CFloatPtr(self.nodemap.GetNode("ExposureTime")).SetValue(float(exposure_time))

    def set_gain(self, gain: float):
        """Set gain (dB)"""
        PySpin.CFloatPtr(self.nodemap.GetNode("Gain")).SetValue(float(gain))

    def set_pixel_format(self, pixel_format: str):
        """Set the pixel format. The extra lines of code for checking the availablility of the node is for the BlackFlyS camera
        since  beta firmware is being used for this camera"""
        pxf_node = PySpin.CEnumerationPtr(self.nodemap.GetNode("PixelFormat"))
        if PySpin.IsAvailable(pxf_node) and PySpin.IsWritable(pxf_node):
            pxf_node.SetIntValue(pxf_node.GetEntryByName(pixel_format).GetValue())
        else:
            print(f"Current pixel format: {self.camera_pixel_format()}")

    # Functions to control the camera streaming and check status.

    def begin_capturing(self, CameraConfig=None) -> None:
        """Start camera streaming images."""
        # If the camera need be set for external trigger do it here.
        # It should only happen if it needs to.

        if not self.cam.IsInitialized():
            self.cam.Init()
        if not self.cam.IsStreaming():
            self.cam.BeginAcquisition()
        self.frame_timestamp = 0
        self.previous_frame_number = 0

        if CameraConfig:
            self.configure_settings(CameraConfig)

    def stop_capturing(self) -> None:
        """Stop the camera from streaming"""
        if self.cam.IsStreaming():
            self.cam.EndAcquisition()
        if self.cam.IsInitialized():
            self.cam.DeInit()

    def close_api(self):
        """Close the PySpin API and release resources."""
        self.stop_capturing()
        self.cam = None
        self.cam_list.Clear()

    def get_available_images(self):
        """Gets all available images from the buffer and return images GPIO pinstate data and timestamps."""
        img_buffer = []
        timestamps_buffer = []
        gpio_buffer = []
        dropped_frames = 0

        try:
            while True:
                next_image = self.cam.GetNextImage(0)  # Raises exception if buffer empty.
                img_buffer.append(next_image.GetData())  # Image pixels as bytes.
                chunk_data = next_image.GetChunkData()  # Additional image data.
                timestamps_buffer.append(chunk_data.GetTimestamp())  # Image timestamp (nanoseconds)
                if self.previous_frame_number != (chunk_data.GetFrameID() - 1):  # Frame IDs
                    dropped_frames += 1
                self.previous_frame_number = chunk_data.GetFrameID()
                if self.device_model == "Chameleon3":
                    img_data = img_buffer[-1]
                    gpio_buffer.append([(img_data[32] >> 4) & 1, (img_data[32] >> 5) & 1, (img_data[32] >> 7) & 1])
                else:
                    gpio_binary = format(chunk_data.GetExposureEndLineStatusAll(), "04b")
                    gpio_buffer.append([int(gpio_binary[3]), int(gpio_binary[1]), int(gpio_binary[0])])
                next_image.Release()  # Clears image from buffer.
        except PySpin.SpinnakerException:  # Buffer is empty.
            if len(img_buffer) == 0:
                return
            else:
                return {
                    "images": img_buffer,
                    "gpio_data": gpio_buffer,
                    "timestamps": timestamps_buffer,
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
            cam.Init()
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
    pyspin_cam_list.Clear()
    pyspin_system.ReleaseInstance()
    return unique_id_list


def initialise_camera_api(CameraConfig):
    """Instantiate the SpinnakerCamera object"""
    return SpinnakerCamera(CameraConfig=CameraConfig)
