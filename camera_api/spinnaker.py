import PySpin
from math import floor, ceil
from . import GenericCamera


PYSPINSYSTEM = PySpin.System.GetInstance()


class SpinnakerCamera(GenericCamera):
    """Inherits from the camera class and adds the spinnaker specific functions from the PySpin library"""

    def __init__(self, CameraConfig=None):
        super().__init__(self)
        self.unique_id = CameraConfig.unique_id
        # Initialise camera -------------------------------------------------

        self.serial_number, self.api = self.unique_id.split("-")
        self.cam_list = PYSPINSYSTEM.GetCameras()
        # self.cam = next(
        #     (cam for cam in self.cam_list if cam.TLDevice.DeviceSerialNumber.GetValue() == self.serial_number), None
        # )
        self.cam = PYSPINSYSTEM.GetCameras().GetBySerial(self.serial_number)
        self.camera_model = self.cam.TLDevice.DeviceModelName.GetValue()[:10]
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        self.stream_nodemap = self.cam.GetTLStreamNodeMap()

        # Configure camera --------------------------------------------------

        # Set Buffer handling mode to Oldest First Overwrite and buffer size to 100 frames.
        bh_node = PySpin.CEnumerationPtr(self.stream_nodemap.GetNode("StreamBufferHandlingMode"))
        bh_node.SetIntValue(bh_node.GetEntryByName("OldestFirst").GetValue())
        sbc_node = PySpin.CIntegerPtr(self.stream_nodemap.GetNode("StreamBufferCountManual"))
        sbc_node.SetValue(50)  # Set to maximum buffer size
        # Configure ChunkData to include frame count and timestamp.
        chunk_selector = PySpin.CEnumerationPtr(self.nodemap.GetNode("ChunkSelector"))
        if self.camera_model == "Chameleon3":
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

        # Set frame rate control to manual.
        if self.camera_model == "Chameleon3":
            frc_node = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnabled"))
            frc_node.SetValue(True)
            fra_node = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionFrameRateAuto"))
            fra_node.SetIntValue(fra_node.GetEntryByName("Off").GetValue())
        else:
            fra_node = PySpin.CBooleanPtr(self.nodemap.GetNode("AcquisitionFrameRateEnable"))
            fra_node.SetValue(True)

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

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Get the min and max frame rate in Hz."""
        node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("AcquisitionFrameRate"))
        return ceil(node.GetMin()), floor(node.GetMax())

    def get_exposure_time(self) -> float:
        """Get exposure of camera"""
        return float(PySpin.CFloatPtr(self.nodemap.GetNode("ExposureTime")).GetValue())

    def get_exposure_time_range(self) -> tuple[int, int]:
        node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("ExposureTime"))
        return ceil(node.GetMin()), floor(node.GetMax())

    def get_gain(self) -> int:
        """Get camera gain setting in dB."""
        return PySpin.CFloatPtr(self.nodemap.GetNode("Gain")).GetValue()

    def get_gain_range(self) -> tuple[int, int]:
        """Get range of gain"""
        node = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("Gain"))
        return ceil(node.GetMin()), floor(node.GetMax())

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
            available_pxl_fmts.append(str(entry.GetSymbolic()))

        # Return list
        return available_pxl_fmts

    # Functions to set camera paramteters.

    def configure_settings(self, CameraConfig):
        """Configure all settings from CameraConfig."""
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

    # Functions to control the camera streaming and check status.

    def begin_capturing(self, CameraConfig=None) -> None:
        """Start camera streaming images."""

        if not self.cam.IsInitialized():
            self.cam.Init()
        if not self.cam.IsStreaming():
            self.cam.BeginAcquisition()
        self.last_frame_number = -1
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
        # Get all available images from camera buffer.
        try:
            while True:
                next_image = self.cam.GetNextImage(0)  # Raises exception if buffer empty.
                img_buffer.append(next_image.GetNDArray())  # Image pixels as numpy array.
                chunk_data = next_image.GetChunkData()  # Additional image data.
                timestamps_buffer.append(chunk_data.GetTimestamp())  # Image timestamp (nanoseconds)
                # frame_number = chunk_data.GetFrameID() # Does not work correctly in 'OldestFirst' buffer mode.
                frame_number = round(timestamps_buffer[-1] / self.inter_frame_interval)
                dropped_frames += max(frame_number - self.last_frame_number - 1, 0)
                self.last_frame_number = frame_number
                if self.camera_model == "Chameleon3":
                    img_data = next_image.GetData()
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
                    "dropped_frames": dropped_frames,
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


def initialise_camera_api(CameraSettingsConfig):
    """Instantiate the SpinnakerCamera object based on the unique-id"""
    return SpinnakerCamera(CameraConfig=CameraSettingsConfig)
