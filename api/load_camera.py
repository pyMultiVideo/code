'Functions for loading the camera IDs'
import PySpin
import logging
# import serial.tools.list_ports as list_ports

from api.camera import (
    CameraTemplate,
    SpinnakerCamera
    )

def get_unique_ids() -> list[tuple[str, str]]:
    'Get a list of unique camera IDs for all the different types of cameras connected to the machine'
    
    unique_id_list = []
    
    # PySpin system
    pyspin_system = PySpin.System.GetInstance()
    pyspin_cam_list = pyspin_system.GetCameras()
    for cam in pyspin_cam_list:
        # Get cam serial number
        cam.Init()
        
        
        cam_tuple: tuple[str, str] = (cam.DeviceSerialNumber(), 'spinnaker')
        unique_id_list.append(cam_tuple)

    # USB system
    # usb_ports = list_ports.comports()
    # for port in usb_ports:
    #     usb_tuple: tuple[str, str] = (port.device, 'usb')
    #     unique_id_list.append(usb_tuple)
    
    
    return unique_id_list

def init_camera(unique_id: str, api: str) -> CameraTemplate:
    
    if api == 'spinnaker':
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        cam = cam_list.GetBySerial(unique_id)
        cam.Init()
        return SpinnakerCamera(cam, None)
    # if api == 'usb':
    #     return USB_Camera()
