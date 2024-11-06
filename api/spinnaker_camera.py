
import PySpin
import numpy as np
import json
import logging 


class SpinnakerCamera():
    'Inherits from the camera class and adds the spinnaker specific functions from the PySpin library'
    def __init__(self, camera: PySpin.Camera, *config: dict):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._init_camera(camera, config)
        

    def _init_camera(self, camera: PySpin.Camera, config: dict = None) -> None:
        self.camera = camera
        
        # Load the camera config
        if config != None:
            self._load_config(config)
                
            for key, value in config.items():
                if key == "exposure_time":
                    self.set_exposure_time(value)
                elif key == "gain":
                    self.set_gain(value)
                elif key == "frame_rate":
                    self.set_frame_rate(value)
                elif key == "width":
                    self.set_width(value)
                elif key == "height":
                    self.set_height(value)

        else: 
            raise Exception("No camera config provided. Camera will be initialised with default settings.")
            

    def _load_config(self, config: dict) -> None:
        self.config = json.load(config)

    # Functions to set the camera parameters

    def set_exposure_time(self, exposure_time: int) -> None:
        if self.camera.ExposureAuto and self.camera.ExposureAuto.GetAccessMode() == PySpin.RW:
            self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        if self.camera.ExposureTime and self.camera.ExposureTime.GetAccessMode() == PySpin.RW:
            self.camera.ExposureTime.SetValue(exposure_time)
            
    def set_gain(self, gain: int) -> None:
        if self.camera.GainAuto and self.camera.GainAuto.GetAccessMode() == PySpin.RW:
            self.camera.GainAuto.SetValue(PySpin.GainAuto_Off)
        if self.camera.Gain and self.camera.Gain.GetAccessMode() == PySpin.RW:
            self.camera.Gain.SetValue(gain)
            
    def set_frame_rate(self, frame_rate: int) -> None:
        if self.camera.AcquisitionFrameRateEnable and self.camera.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            self.camera.AcquisitionFrameRateEnable.SetValue(True)
        if self.camera.AcquisitionFrameRate and self.camera.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.camera.AcquisitionFrameRate.SetValue(frame_rate)
            
    def set_width(self, width: int) -> None:
        if self.camera.Width and self.camera.Width.GetAccessMode() == PySpin.RW:
            self.camera.Width.SetValue(width)
        
    def set_height(self, height: int) -> None:
        if self.camera.Height and self.camera.Height.GetAccessMode() == PySpin.RW:
            self.camera.Height.SetValue(height)
            
    def set_frame_rate(self, frame_rate: int) -> None:
        if self.camera.AcquisitionFrameRateEnable and self.camera.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
            self.camera.AcquisitionFrameRateEnable.SetValue(True)
        if self.camera.AcquisitionFrameRate and self.camera.AcquisitionFrameRate.GetAccessMode() == PySpin.RW:
            self.camera.AcquisitionFrameRate.SetValue(frame_rate)
            
    # Function to aquire images from the camera
          
    def begin_recording(self) -> None:
        self.camera.Init()
        self.camera.BeginAcquisition()
            
    def get_next_image(self) -> np.ndarray:
        
        # Check if the camera is not in aquistion mode
        if not self.camera.IsStreaming():
            raise Exception("Camera is not in acquisition mode.")
        
        # Get the next image
        next_image = self.camera.GetNextImage()
        
        # Check if the image is incomplete
        if next_image.IsIncomplete():
            raise Exception("Image is incomplete.")
        
        # Convert the image to a numpy array
        next_image = next_image.GetNDArray()
        
        # Return the image
        return next_image
        
    def end_recording(self) -> None:
        self.camera.EndAcquisition()
        self.camera.DeInit()
            

class SpinnakerCameraSystem():
    def __init__(self):
        self.system = PySpin.System.GetInstance()
        
    def get_camera_list(self) -> list[SpinnakerCamera]:

        # For each camera in the camera list, create a camera object
        self.cam_list = []
        cam_list = self.system.GetCameras()
        for cam in cam_list:
            self.cam_list.append(SpinnakerCamera(cam))
            
        self.numCameras = len(self.cam_list)
        
    
if __name__ == '__main__':
    # load the camera config
    system = SpinnakerCameraSystem()
    cam_list = system.get_camera_list()

    camera = cam_list[0]
    with open('configs/cam_api_config.json') as f:
        cam_config = json.load(f)

    # Settings for the camera do not work. 
    camera.set_exposure_time(100)
    camera.set_gain(10)
    camera.set_frame_rate(30)
    camera.set_width(1920)
    camera.set_height(1080)
    
    camera.begin_recording()
    next_image = camera.get_next_image()
    print(next_image.shape)
    camera.end_recording()