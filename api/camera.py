
import PySpin
import numpy as np
import json
import logging 
import serial

from utils.data_classes import CameraConfig

# Documentation for the Camera Object

class CameraTemplate():
    'Wrapper around the camera class. This exists for allowing more flexibility for different, unsupported cameras.'
    def __init__(self, camera):
    
        self.camera = camera
        self.logger = logging.getLogger(__name__)

    def set_exposure_time(self, exposure_time):
        'Set the exposure time of the camera'
        pass
    
    def set_gain(self, gain: int) -> None:
        'Set the gain of the camera'
        pass

    def set_frame_rate(self, frame_rate: int) -> None:
        'Set the frame rate of the camera'
        pass
    
    def set_width(self, width: int) -> None:
        'Set the width of the camera'
        pass
    
    def set_height(self, height: int) -> None:
        'Set the height of the camera'
        pass
    
    def begin_capturing(self) -> None:
        'Begin recording from the camera'
        pass
    
    def set_serial_number(self, serial_number: str) -> None:
        'Set the serial number of the camera'
        pass
    
    def get_next_image(self) -> np.ndarray:
        'Gets the next image from the camera'
        pass
    
    def end_recording(self) -> None:
        'End recording from the camera'
        pass
        
    def get_GPIO_data(self) -> dict:
        'Get the GPIO data from the camera as a dictionary of the GPIO lines and their associated states'
        pass

class SpinnakerCamera(CameraTemplate):
    'Inherits from the camera class and adds the spinnaker specific functions from the PySpin library'
    def __init__(self, camera: PySpin.Camera, config: CameraConfig):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)
        self.pyspin_camera = camera
        self.camera_config: CameraConfig = config
        # self._init_camera()
    
    def _init_camera(self) -> None:
    
        # Set the camera parameters
        self.set_exposure_time(self.camera_config.exposure_time)
        self.set_gain(self.camera_config.gain)
        self.set_frame_rate(self.camera_config.fps)
        self.set_width(self.camera_config.width)
        self.set_height(self.camera_config.height)
        
        # Set the serial number
        self.set_serial_number(self.camera_config.serial_number)
  
    # Functions to set the camera parameters

    def set_exposure_time(self, exposure_time: int) -> None:
        if self.pyspin_camera.ExposureAuto and self.pyspin_camera.ExposureAuto.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        if self.pyspin_camera.ExposureTime and self.pyspin_camera.ExposureTime.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.ExposureTime.SetValue(exposure_time)
            
    def set_gain(self, gain: int) -> None:
        if self.pyspin_camera.GainAuto and self.pyspin_camera.GainAuto.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.GainAuto.SetValue(PySpin.GainAuto_Off)
        if self.pyspin_camera.Gain and self.pyspin_camera.Gain.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.Gain.SetValue(gain)
            
    def set_frame_rate(self, frame_rate: int) -> None:
        if self.pyspin_camera.AcquisitionFrameRateEnable and self.pyspin_camera.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.AcquisitionFrameRateEnable.SetValue(True)
        if self.pyspin_camera.AcquisitionFrameRate and self.pyspin_camera.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.AcquisitionFrameRate.SetValue(frame_rate)
            
    def set_width(self, width: int) -> None:
        if self.pyspin_camera.Width and self.pyspin_camera.Width.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.Width.SetValue(width)
        
    def set_height(self, height: int) -> None:
        if self.pyspin_camera.Height and self.pyspin_camera.Height.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.Height.SetValue(height)
            
    def set_frame_rate(self, frame_rate: int) -> None:
        if self.pyspin_camera.AcquisitionFrameRateEnable and self.pyspin_camera.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.AcquisitionFrameRateEnable.SetValue(True)
        if self.pyspin_camera.AcquisitionFrameRate and self.pyspin_camera.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.pyspin_camera.AcquisitionFrameRate.SetValue(frame_rate)
         
    def set_config(self, config: CameraConfig) -> None:
        'Function to set the camera configuration'
        self.set_exposure_time(config.exposure_time)
        self.set_gain(config.gain)
        self.set_frame_rate(config.fps)
        self.set_width(config.width)
        self.set_height(config.height)
        self.set_serial_number(config.serial_number)
        
    # Function to aquire images from the camera
          
    def begin_capturing(self) -> None:
        self.pyspin_camera.Init()
        self.pyspin_camera.BeginAcquisition()
            
    def get_next_image(self) -> np.ndarray:
        
        # Check if the camera is not in aquistion mode
        if not self.pyspin_camera.IsStreaming():
            raise Exception("Camera is not in acquisition mode.")
        
        # Get the next image
        next_image = self.pyspin_camera.GetNextImage()
        
        # Check if the image is incomplete
        if next_image.IsIncomplete():
            raise Exception("Image is incomplete.")
        
        # Convert the image to a numpy array
        self.next_image = next_image.GetNDArray()
        
        next_image.Release()
        # Return the image
        return self.next_image
        
    def end_recording(self) -> None:
        self.pyspin_camera.EndAcquisition()
        self.pyspin_camera.DeInit()
            
            
    def get_GPIO_data(self) -> dict:
        'Get the GPIO data from the camera'
        
        try:
            node_line_selector = PySpin.CEnumerationPtr(self.pyspin_camera.GetNodeMap().GetNode('LineSelector'))
            if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsReadable(node_line_selector):
                raise Exception("LineSelector node not available.")
            
            line_entries = node_line_selector.GetEntries()
            
            self.GPIO_data = {}
            for line_entry in line_entries:
                line_name = line_entry.GetName()
                
                node_line_status = PySpin.CBooleanPtr(self.pyspin_camera.GetNodeMap().GetNode("LineStatus"))
                if not PySpin.IsAvailable(node_line_status) or not PySpin.IsReadable(node_line_status):
                    raise Exception("LineStatus node not available.")

                line_state = node_line_status.GetValue()
                self.GPIO_data[line_name] = line_state  
        
        except Exception as e:
            self.logger.error(f"Error getting GPIO data: {e}")
        
        return self.GPIO_data
class USBCamera(CameraTemplate):
    'Example use of a USB camera instead of the spinnaker camera'
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    def _init_camera(self):
        capture = cv2.VideoCapture(0)
    
    
    
if __name__ == '__main__':
    # load the camera config
    # Testing functions here
    pass