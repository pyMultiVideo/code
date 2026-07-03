import PySpin
import numpy as np
from math import floor, ceil
from .generic_camera import GenericCamera

PYSPINSYSTEM = PySpin.System.GetInstance()  # One PySpin system instance per pMV


class SpinnakerCamera(GenericCamera):
    """Inherits from the camera class and adds the spinnaker specific functions from the PySpin library"""

    def __init__(self, unique_id):
        super().__init__(unique_id)

        # Options for camera -----------------------------------------------------------
        self.serial_number, self._api = self.unique_id.rsplit("-", 1)
        self.N_GPIO = 3  # Number of GPIO pins
        self.manual_control_enabled = True
        self.pixel_format_aliases = {  # Maps GUI pixel format names to spinnaker pixel format names.
            "bayer_rggb8": "BayerRG8",
            "mono8": "Mono8",
        }

        self._trigger_line = 2  # Trigger line name
        self._previous_frame_number = 0
        self._inter_frame_interval = 1
        self._frame_timestamp = None

        # Initialise camera -------------------------------------------------------------------------------------------
        self._cam_list = PYSPINSYSTEM.GetCameras()
        self._cam = next(
            (cam for cam in self._cam_list if cam.TLDevice.DeviceSerialNumber.GetValue() == self.serial_number), None
        )
        self.device_model = self._cam.TLDevice.DeviceModelName.GetValue()
        self._cam.Init()
        self._nodemap = self._cam.GetNodeMap()
        self._stream_nodemap = self._cam.GetTLStreamNodeMap()
        self.image_width = PySpin.CIntegerPtr(self._nodemap.GetNode("Width")).GetValue()
        self.image_height = PySpin.CIntegerPtr(self._nodemap.GetNode("Height")).GetValue()

        # Select and apply the first supported pixel format from the shared priority list.
        self.initialize_preferred_pixel_format()

        # Configure camera settings -----------------------------------------------------------------------------------

        # Set Buffer handling mode to OldestFirst and buffer size to 100 frames.
        bh_node = PySpin.CEnumerationPtr(self._stream_nodemap.GetNode("StreamBufferHandlingMode"))
        bh_node.SetIntValue(bh_node.GetEntryByName("OldestFirst").GetValue())
        sbc_node = PySpin.CIntegerPtr(self._stream_nodemap.GetNode("StreamBufferCountManual"))
        sbc_node.SetValue(100)

        # Configure image metadata to include GPIO pinstate and image timestamp.

        chunk_selector = PySpin.CEnumerationPtr(self._nodemap.GetNode("ChunkSelector"))

        self._configure_gpio(chunk_selector)

        chunk_selector.SetIntValue(chunk_selector.GetEntryByName("Timestamp").GetValue())
        self._cam.ChunkEnable.SetValue(True)
        self._cam.ChunkModeActive.SetValue(True)

        # Acqusition mode continuous
        acq_mode = PySpin.CEnumerationPtr(self._nodemap.GetNode("AcquisitionMode"))
        acq_mode.SetIntValue(acq_mode.GetEntryByName("Continuous").GetValue())

        # Set Exposure to manual
        exc_node = PySpin.CEnumerationPtr(self._nodemap.GetNode("ExposureAuto"))
        exc_node.SetIntValue(PySpin.ExposureAuto_Off)

        # Set Gain to manual
        gnc_node = PySpin.CEnumerationPtr(self._nodemap.GetNode("GainAuto"))
        gnc_node.SetIntValue(PySpin.GainAuto_Off)

        print(f"Spinnaker camera {self.serial_number} initialised")

    # Functions to get the camera parameters --------------------------------------------------------------------------

    def get_frame_rate_range(self, *exposure_time) -> tuple[int, int]:
        """Get the min and max frame rate (Hz)."""
        try:
            node = PySpin.CFloatPtr(self._cam.GetNodeMap().GetNode("AcquisitionFrameRate"))
            return ceil(node.GetMin()), floor(node.GetMax())
        except PySpin.SpinnakerException:
            if exposure_time:
                max_frame_rate = 1e6 / exposure_time[0]  # Use the first value of the tuple
                return ceil(1), floor(max_frame_rate)
            else:
                raise ValueError("Exposure time must be provided to calculate frame rate range.")

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""
        return float(PySpin.CFloatPtr(self._nodemap.GetNode("ExposureTime")).GetValue())

    def get_exposure_time_range(self, *fps) -> tuple[int, int]:
        """Get the min and max exposure time (us)"""
        try:
            node = PySpin.CFloatPtr(self._cam.GetNodeMap().GetNode("ExposureTime"))
            return ceil(node.GetMin()), floor(node.GetMax())
        except PySpin.SpinnakerException:
            max_exposure_time = 1e6 / fps[0] + 8  # Underestimate maximum since init will fail if too big
            return ceil(7), floor(max_exposure_time)

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        return PySpin.CFloatPtr(self._nodemap.GetNode("Gain")).GetValue()

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        node = PySpin.CFloatPtr(self._cam.GetNodeMap().GetNode("Gain"))
        return ceil(node.GetMin()), floor(node.GetMax())

    def _get_camera_pixel_format(self) -> str:
        """Get string specifying camera pixel format using its spinnaker-native name."""
        return PySpin.CEnumerationPtr(self._nodemap.GetNode("PixelFormat")).GetCurrentEntry().GetSymbolic()

    def _get_supported_pixel_formats(self) -> list[str]:
        """Return the spinnaker-native pixel formats available to the camera."""
        # Get available pixel formats
        node_map = self._cam.GetNodeMap()
        pixel_format_node = PySpin.CEnumerationPtr(node_map.GetNode("PixelFormat"))
        pixel_format_entries = pixel_format_node.GetEntries()
        # Convert to string and check if available
        pxl_formats = []
        for entry in pixel_format_entries:
            entry = PySpin.CEnumEntryPtr(entry)
            if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                pxl_formats.append(str(entry.GetSymbolic()))
        return pxl_formats

    # Configure Camera for external acqusition

    def set_acqusition_mode(self, external_trigger: bool):
        if external_trigger:
            # Ensure trigger mode is off before configuring
            trigger_mode = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerMode"))
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("Off").GetValue())

            # Set TriggerSelector to FrameStart
            trigger_selector = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerSelector"))
            trigger_selector.SetIntValue(trigger_selector.GetEntryByName("FrameStart").GetValue())

            # Configure the trigger source to the specified line
            trigger_source = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerSource"))
            trigger_source.SetIntValue(trigger_source.GetEntryByName("Line" + str(self._trigger_line)).GetValue())

            # Set the trigger activation to RisingEdge
            trigger_activation = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerActivation"))
            trigger_activation.SetIntValue(trigger_activation.GetEntryByName("RisingEdge").GetValue())

            # Turn trigger mode back on
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("On").GetValue())

        else:  # Internal triggering
            # Ensure that the trigger mode is off so manual camera control is enabled
            trigger_mode = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerMode"))
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("Off").GetValue())
            # Set frame rate control to manual.
            self._enable_manual_frame_rate_control()

    def _configure_gpio(self, chunk_selector):
        """Configure camera to include GPIO pinstates in image metadata."""
        chunk_selector.SetIntValue(chunk_selector.GetEntryByName("ExposureEndLineStatusAll").GetValue())
        self._cam.ChunkEnable.SetValue(True)

    def _enable_manual_frame_rate_control(self):
        """Enable manual frame-rate control for non-Chameleon Spinnaker cameras."""
        fra_node = PySpin.CBooleanPtr(self._nodemap.GetNode("AcquisitionFrameRateEnable"))
        fra_node.SetValue(True)

    def _extract_gpio_data(self, _img_data, chunk_data):
        """Extract GPIO pin states from chunk data, return as numpy boolean array."""
        gpio_binary = format(chunk_data.GetExposureEndLineStatusAll(), "04b")
        return np.array([int(gpio_binary[3]), int(gpio_binary[1]), int(gpio_binary[0])], dtype=bool)

    def _get_trigger_lines(self):
        """Get a list of the GPI lines that can be used to trigger frame acquisition"""
        trigger_lines = []
        try:
            line_selector = PySpin.CEnumerationPtr(self._nodemap.GetNode("LineSelector"))
            for entry in line_selector.GetEntries():
                entry = PySpin.CEnumEntryPtr(entry)
                if PySpin.IsAvailable(entry) and PySpin.IsReadable(entry):
                    line_name = entry.GetSymbolic()
                    if "Line" in line_name:
                        trigger_lines.append(line_name)
        except PySpin.SpinnakerException as e:
            print(f"Error retrieving trigger lines: {e}")
        return trigger_lines

    # Functions to set camera paramteters -----------------------------------------------------------------------------

    def set_frame_rate(self, frame_rate):
        """Set the frame rate of the camera in Hz."""
        PySpin.CFloatPtr(self._nodemap.GetNode("AcquisitionFrameRate")).SetValue(int(frame_rate))
        self._inter_frame_interval = int(1e6 // int(frame_rate))  # Microsecconds.

    def set_exposure_time(self, exposure_time: float) -> None:
        """Set the exposure time of the camera in microseconds."""
        PySpin.CFloatPtr(self._nodemap.GetNode("ExposureTime")).SetValue(float(exposure_time))

    def set_gain(self, gain: float):
        """Set gain (dB)"""
        PySpin.CFloatPtr(self._nodemap.GetNode("Gain")).SetValue(float(gain))

    def _set_pixel_format(self, pixel_format: str):
        """Set the pixel format using a spinnaker-native format name."""
        pxf_node = PySpin.CEnumerationPtr(self._nodemap.GetNode("PixelFormat"))
        if PySpin.IsAvailable(pxf_node) and PySpin.IsWritable(pxf_node):
            pxf_node.SetIntValue(pxf_node.GetEntryByName(pixel_format).GetValue())
        else:
            print(f"Unable to set pixel format. Current format: {self._get_camera_pixel_format()}")

    # Functions to control the camera streaming and check status. -----------------------------------------------------

    def begin_capturing(self) -> None:
        """Start camera streaming images."""
        if not self._cam.IsInitialized():
            self._cam.Init()
        if not self._cam.IsStreaming():
            self._cam.BeginAcquisition()
        self._frame_timestamp = None
        self._previous_frame_number = 0

    def stop_capturing(self) -> None:
        """Stop the camera from streaming"""
        if self._cam.IsStreaming():
            self._cam.EndAcquisition()

    def close(self):
        """Close the PySpin API and release resources."""
        if self._cam is not None:
            if self._cam.IsStreaming():
                self._cam.EndAcquisition()
            if self._cam.IsInitialized():
                self._cam.DeInit()
        self._cam = None
        self._cam_list.Clear()

    def get_available_images(self):
        """Gets all available images from the buffer and return images GPIO pinstate data and timestamps."""
        img_buffer = []
        timestamps_buffer = []
        gpio_buffer = []
        dropped_frames = 0

        try:
            while True:
                next_image = self._cam.GetNextImage(0)  # Raises exception if buffer empty.
                img_buffer.append(next_image.GetData())  # Image pixels as 1D numpy array of image bytes.
                chunk_data = next_image.GetChunkData()  # Additional image data.
                timestamps_buffer.append(chunk_data.GetTimestamp() // 1000)  # Image timestamp (microseconds)
                # Frame timestamps
                if self._frame_timestamp is None:
                    self._frame_timestamp = timestamps_buffer[-1]
                else:
                    elapsed_frames = round(
                        (timestamps_buffer[-1] - self._frame_timestamp) / self._inter_frame_interval
                    )
                    self._frame_timestamp = timestamps_buffer[-1]
                    dropped_frames += elapsed_frames - 1
                gpio_buffer.append(self._extract_gpio_data(img_buffer[-1], chunk_data))
                next_image.Release()  # Clears image from buffer.
        except PySpin.SpinnakerException:  # Buffer is empty.
            if len(img_buffer) == 0:
                return
            else:
                return {
                    "images": img_buffer,
                    "gpio_data": gpio_buffer,
                    "timestamps": timestamps_buffer,
                    "dropped_frames": dropped_frames,
                }


class Chameleon3Camera(SpinnakerCamera):
    """Spinnaker camera implementation for Chameleon3 model-specific behavior."""

    def _configure_gpio(self, chunk_selector):
        """Configure camera to include GPIO pinstates in image data. Getting GPIO pinstate
        from chunk data is not supported on Chameleon3 cameras."""
        FRAME_INFO_REG = 0xFFFFF0F012F8
        reg_read = self._cam.ReadPort(FRAME_INFO_REG)
        reg_write = (reg_read & 0xFFFFFC00) + 0x3FF
        self._cam.WritePort(FRAME_INFO_REG, reg_write)

    def _enable_manual_frame_rate_control(self):
        frc_node = PySpin.CBooleanPtr(self._nodemap.GetNode("AcquisitionFrameRateEnabled"))
        frc_node.SetValue(True)
        fra_node = PySpin.CEnumerationPtr(self._nodemap.GetNode("AcquisitionFrameRateAuto"))
        fra_node.SetIntValue(fra_node.GetEntryByName("Off").GetValue())

    def _extract_gpio_data(self, img_data, chunk_data):
        """Extract GPIO pin states from image data, return as numpy boolean array."""
        return np.array(
            [
                (img_data[32] >> 4) & 1,
                (img_data[32] >> 5) & 1,
                (img_data[32] >> 7) & 1,
            ],
            dtype=bool,
        )


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


def initialise_camera_api(unique_id):
    """Instantiate the model-appropriate Spinnaker camera object."""
    serial_number, _ = unique_id.rsplit("-", 1)
    cam_list = PYSPINSYSTEM.GetCameras()
    cam = next((cam for cam in cam_list if cam.TLDevice.DeviceSerialNumber.GetValue() == serial_number))
    cam_list.Clear()
    model = cam.TLDevice.DeviceModelName.GetValue()[:10]
    if model[:10] == "Chameleon3":
        return Chameleon3Camera(unique_id=unique_id)
    else:
        return SpinnakerCamera(unique_id=unique_id)
