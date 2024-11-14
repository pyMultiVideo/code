
import numpy as np


import json
import logging
import serial

import PySpin
import cv2


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
    
    def get_next_image(self) -> list[np.ndarray]:
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
    def __init__(self, unique_id: str, CameraConfig = None):
        super().__init__(self)
        self.camera_config = CameraConfig
        # Logger
        self.logger = logging.getLogger(__name__)
        self.system = PySpin.System.GetInstance()
        self.serial_number, self.api = unique_id.split('-')
        self.cam = self.system.GetCameras().GetBySerial(self.serial_number)
        
        print('Camera:', self.cam)
        self.cam.Init()

        if self.camera_config is not None:
            self.set_exposure_time(self.camera_config.exposure_time)
            self.set_gain(self.camera_config.gain)
            self.set_frame_rate(self.camera_config.fps)
            self.set_width(self.camera_config.width)
            self.set_height(self.camera_config.height)
                
        else:   
            self.exposure_time  = self.get_exposure_time()
            self.width          = self.get_width()
            self.height         = self.get_height()
            self.fps            = self.get_frame_rate()
            self.gain           = self.get_gain()
            self.pixel_format   = self.get_pixel_format()
            self.bitrate        = self.get_bitrate()
    # Functions to get the camera parameters
    
    def get_exposure_time(self) -> int:
        nodemap = self.cam.GetNodeMap()       
        return PySpin.CFloatPtr(nodemap.GetNode("ExposureTime")).GetValue()
    
    def get_width(self) -> int:
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("Width")).GetValue()
    
    def get_height(self) -> int:
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("Height")).GetValue()
    
    def get_frame_rate(self) -> int:
        nodemap = self.cam.GetNodeMap()
        return PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate")).GetValue()
    
    def get_gain(self) -> int:
        nodemap = self.cam.GetNodeMap()
        return PySpin.CFloatPtr(nodemap.GetNode("Gain")).GetValue()
    
    def get_pixel_format(self) -> str:
        nodemap = self.cam.GetNodeMap()
        return PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat")).GetCurrentEntry().GetSymbolic()
    
    def get_bitrate(self) -> int:
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("DeviceLinkThroughputLimit")).GetValue()
    
    # Functions to set the camera parameters

    def set_exposure_time(self, exposure_time: int) -> None:
        if self.cam.ExposureAuto and self.cam.ExposureAuto.GetAccessMode() == PySpin.RW:
            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        if self.cam.ExposureTime and self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
            self.cam.ExposureTime.SetValue(exposure_time)
            
    def set_gain(self, gain: int) -> None:
        if self.cam.GainAuto and self.cam.GainAuto.GetAccessMode() == PySpin.RW:
            self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
        if self.cam.Gain and self.cam.Gain.GetAccessMode() == PySpin.RW:
            self.cam.Gain.SetValue(gain)
            
    def set_frame_rate(self, frame_rate: int) -> None:
        if self.cam.AcquisitionFrameRateEnable and self.cam.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            self.cam.AcquisitionFrameRateEnable.SetValue(True)
        if self.cam.AcquisitionFrameRate and self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.cam.AcquisitionFrameRate.SetValue(frame_rate)
            
    def set_width(self, width: int) -> None:
        if self.cam.Width and self.cam.Width.GetAccessMode() == PySpin.RW:
            self.cam.Width.SetValue(width)
        
    def set_height(self, height: int) -> None:
        if self.cam.Height and self.cam.Height.GetAccessMode() == PySpin.RW:
            self.cam.Height.SetValue(height)
            
    def set_frame_rate(self, frame_rate: int) -> None:
        if self.cam.AcquisitionFrameRateEnable and self.cam.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            self.cam.AcquisitionFrameRateEnable.SetValue(True)
        if self.cam.AcquisitionFrameRate and self.cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.cam.AcquisitionFrameRate.SetValue(frame_rate)

    # Function to aquire images from the camera
          
    def begin_capturing(self) -> None:
        # initialize the camera if it is not already initialized
        if not self.cam.IsInitialized():
            self.cam.Init()
        self.cam.BeginAcquisition()
            
    def get_next_image(self) -> np.ndarray:
        
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
        
        next_image.Release()
        # Return the image
        return self.next_image
    
    def get_next_image_list(self) -> list[np.ndarray]:
        '''Get all the images in the buffer'''
        # Delete all images from the image list
        self.image_list = []
        # check if the camera is in acquisition mode
        if not self.cam.IsStreaming():
            raise Exception(f"Camera {self.serial_number} is not in acquisition mode.")
        # get the next image
        next_image = self.cam.GetNextImage()
        # Get all images in the buffer
        while not next_image.IsIncomplete():
            self.image_list.append(next_image.GetNDArray())
            next_image.Release()
            next_image = self.cam.GetNextImage()
        
        return self.image_list
        
    def end_recording(self) -> None:
        self.cam.EndAcquisition()
        self.cam.DeInit()
        # make sure to release the camera
            
            
    def get_GPIO_data(self) -> dict:
        'Get the GPIO data from the camera'
        
        try:
            node_line_selector = PySpin.CEnumerationPtr(self.cam.GetNodeMap().GetNode('LineSelector'))
            if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsReadable(node_line_selector):
                raise Exception("LineSelector node not available.")
            
            line_entries = node_line_selector.GetEntries()
            
            self.GPIO_data = {}
            for line_entry in line_entries:
                line_name = line_entry.GetName()
                
                node_line_status = PySpin.CBooleanPtr(self.cam.GetNodeMap().GetNode("LineStatus"))
                if not PySpin.IsAvailable(node_line_status) or not PySpin.IsReadable(node_line_status):
                    raise Exception("LineStatus node not available.")

                line_state = node_line_status.GetValue()
                self.GPIO_data[line_name] = line_state  
        
        except Exception as e:
            self.logger.error(f"Error getting GPIO data: {e}")
        
        return self.GPIO_data
class USBCamera(CameraTemplate):
    'Example use of a USB camera instead of the spinnaker camera'
    def __init__(self, unique_id: str):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)
        serial_number, api = unique_id.split('-')
        self.usb_id = int(serial_number)
        self._init_camera()
        
    def _init_camera(self):
        self.capture = cv2.VideoCapture(self.usb_id, cv2.CAP_DSHOW)
    
    def begin_capturing(self):
        # self.capture.open(self.usb_id)
        pass
    
    def get_next_image(self) -> np.ndarray:
        ret, frame = self.capture.read()
        # convert the frame to monochrome
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame
    
    
if __name__ == '__main__':
    # load the camera config
    # Testing functions here
    
    
    
    spinnaker_camera = SpinnakerCamera("18360350-spinnaker")
    
    
    
    pass