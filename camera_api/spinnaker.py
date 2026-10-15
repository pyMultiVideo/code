import PySpin
import numpy as np
from math import floor, ceil
from .generic_camera import FrameData, GenericCamera

PYSPINSYSTEM = PySpin.System.GetInstance()  # One PySpin system instance per pMV

# Spinnaker camera class --------------------------------------------------------------------------------------------


class SpinnakerCamera(GenericCamera):
    """Inherits from GenericCamera class and adds spinnaker specific functions from the PySpin library"""

    def __init__(self, serial_number):
        super().__init__(serial_number)

        # Options for camera -----------------------------------------------------------
        self.N_GPIO = 3  # Number of GPIO pins
        self.has_manual_control = {"fps": True, "exposure": True, "gain": True, "trigger": True}
        self.pixel_format_aliases = {  # Maps GUI pixel format names to spinnaker pixel format names.
            "bayer_rggb8": "BayerRG8",
            "mono8": "Mono8",
        }
        self._trigger_line = 0  # Optically isolated input.

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

        # Configure image metadata to include GPIO pinstate, frame IDs and image timestamp.
        self._configure_image_metadata()

        # Set continuous acquisition mode
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

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Get the min and max frame rate (Hz)."""
        node = PySpin.CFloatPtr(self._cam.GetNodeMap().GetNode("AcquisitionFrameRate"))
        return ceil(node.GetMin()), floor(node.GetMax())

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""
        return float(PySpin.CFloatPtr(self._nodemap.GetNode("ExposureTime")).GetValue())

    def get_exposure_time_range(self) -> tuple[int, int]:
        """Get the min and max exposure time (us)"""
        node = PySpin.CFloatPtr(self._cam.GetNodeMap().GetNode("ExposureTime"))
        return ceil(node.GetMin()), floor(node.GetMax())

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

    # Functions used in initial camera configuration ------------------------------------------------------------------

    def _configure_image_metadata(self):
        """Configure camera to include GPIO pinstate, frame IDs, and image timestamp in image metadata."""
        chunk_selector = PySpin.CEnumerationPtr(self._nodemap.GetNode("ChunkSelector"))
        for chunk_name in ("Timestamp", "ExposureEndLineStatusAll"):
            chunk_selector.SetIntValue(chunk_selector.GetEntryByName(chunk_name).GetValue())
            self._cam.ChunkEnable.SetValue(True)
        self._cam.ChunkModeActive.SetValue(True)

    def _enable_manual_frame_rate_control(self):
        """Enable manual frame-rate control for non-Chameleon Spinnaker cameras."""
        fra_node = PySpin.CBooleanPtr(self._nodemap.GetNode("AcquisitionFrameRateEnable"))
        fra_node.SetValue(True)

    # Functions to set camera parameters ------------------------------------------------------------------------------

    def set_frame_rate(self, frame_rate):
        """Set the frame rate of the camera in Hz."""
        PySpin.CFloatPtr(self._nodemap.GetNode("AcquisitionFrameRate")).SetValue(int(frame_rate))

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

    def set_external_trigger_enable(self, enable: bool):
        """Configure whether camera uses external triggering for frame acquisition."""
        if enable:  # Enable external triggering
            # Ensure external trigger mode is off before configuring settings
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

            # Enable trigger overlap mode.
            trigger_overlap = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerOverlap"))
            trigger_overlap.SetIntValue(trigger_overlap.GetEntryByName("ReadOut").GetValue())

        else:  # Internal triggering
            # Ensure that the trigger mode is off so manual camera control is enabled
            trigger_mode = PySpin.CEnumerationPtr(self._nodemap.GetNode("TriggerMode"))
            trigger_mode.SetIntValue(trigger_mode.GetEntryByName("Off").GetValue())
            # Set frame rate control to manual.
            self._enable_manual_frame_rate_control()

    # Functions to control camera streaming and acquire images -------------------------------------------------------------------

    def begin_capturing(self) -> None:
        """Start camera streaming images."""
        if not self._cam.IsInitialized():
            self._cam.Init()
        if not self._cam.IsStreaming():
            self._cam.BeginAcquisition()

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

    def get_available_images(self) -> list[FrameData]:
        """Gets all available images from the buffer and returns FrameData objects."""
        frames = []
        try:
            while True:
                image = self._cam.GetNextImage(0)  # Raises exception if buffer empty.
                img_data = image.GetData()
                chunk_data = image.GetChunkData()
                frames.append(FrameData(image=img_data, **self._get_image_metadata(img_data, chunk_data)))
                image.Release()  # Clears image from buffer.
        except PySpin.SpinnakerException:  # Buffer is empty.
            return frames

    def _get_image_metadata(self, img_data, chunk_data):
        """Get the image metadata chunk_data."""
        gpio_binary = format(chunk_data.GetExposureEndLineStatusAll(), "04b")
        gpio_pinstate = np.array([int(gpio_binary[3]), int(gpio_binary[1]), int(gpio_binary[0])], dtype=bool)
        return {
            "GPIO_pinstate": gpio_pinstate,
            "timestamp": chunk_data.GetTimestamp() // 1000,  # convert to microseconds
            "number": chunk_data.GetFrameID(),
        }


# Gen2 camera class --------------------------------------------------------------------------------------------

gen2_cameramodels = ("Blackfly BFLY-U3", "Grasshopper3 GS3-U3", "Flea3 FL3-U3", "Chameleon3 CM3-U3")


class Gen2Camera(SpinnakerCamera):
    """Spinnaker camera implementation for older Gen2 FLIR cameras which do not support
    getting GPIO pinstates and frame IDs from chunk data."""

    def _enable_manual_frame_rate_control(self):
        frc_node = PySpin.CBooleanPtr(self._nodemap.GetNode("AcquisitionFrameRateEnabled"))
        frc_node.SetValue(True)
        fra_node = PySpin.CEnumerationPtr(self._nodemap.GetNode("AcquisitionFrameRateAuto"))
        fra_node.SetIntValue(fra_node.GetEntryByName("Off").GetValue())

    def _configure_image_metadata(self):
        """Chameleon3 cameras do not suppot reading GPIO pinstate or frame IDs from chunk data. We instead
        configure these to be embedded in the image data. Timestamps are still read from chunk data."""
        # Confiure chunk data to include timestamp as normal.
        chunk_selector = PySpin.CEnumerationPtr(self._nodemap.GetNode("ChunkSelector"))
        chunk_selector.SetIntValue(chunk_selector.GetEntryByName("Timestamp").GetValue())
        self._cam.ChunkEnable.SetValue(True)
        self._cam.ChunkModeActive.SetValue(True)
        # Configure embedding GPIO pinstates and frame ID number in image data.
        FRAME_INFO_REG = 0xFFFFF0F012F8
        reg_value = self._cam.ReadPort(FRAME_INFO_REG)
        reg_value = (reg_value & 0xFFFF0000) | 0x140
        self._cam.WritePort(FRAME_INFO_REG, reg_value)

    def _get_image_metadata(self, img_data, chunk_data):
        """Get the image metadata from chunk_data and embedded image data."""
        gpio_pinstate = np.array([(img_data[4] >> 4) & 1, (img_data[4] >> 5) & 1, (img_data[4] >> 7) & 1], dtype=bool)
        frame_id = (int(img_data[0]) << 24) | (int(img_data[1]) << 16) | (int(img_data[2]) << 8) | int(img_data[3])
        return {
            "GPIO_pinstate": gpio_pinstate,
            "timestamp": chunk_data.GetTimestamp() // 1000,  # convert to microseconds
            "number": frame_id,
        }


# Camera system functions -------------------------------------------------------------------------------


def list_available_cameras(VERBOSE=False) -> list[str]:
    """PySpin specific implementation of getting a list of serial numbers from all the pyspin cameras"""
    serial_number_list = []
    pyspin_system = PySpin.System.GetInstance()
    pyspin_cam_list = pyspin_system.GetCameras()

    if VERBOSE:
        print(f"Number of cameras detected: {pyspin_cam_list.GetSize()}")

    for cam in pyspin_cam_list:
        try:
            cam.Init()
            serial_number: str = str(cam.DeviceSerialNumber())
            if VERBOSE:
                print(f"Serial number: {serial_number}")
            serial_number_list.append(serial_number)
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
    return serial_number_list


def initialise_camera(serial_number):
    """Instantiate the model-appropriate Spinnaker camera object."""
    cam_list = PYSPINSYSTEM.GetCameras()
    cam = next((cam for cam in cam_list if cam.TLDevice.DeviceSerialNumber.GetValue() == serial_number))
    cam_list.Clear()
    model = cam.TLDevice.DeviceModelName.GetValue()
    if model.startswith(gen2_cameramodels):
        return Gen2Camera(serial_number=serial_number)
    else:
        return SpinnakerCamera(serial_number=serial_number)
