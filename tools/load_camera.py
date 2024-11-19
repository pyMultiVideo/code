'Functions for loading the camera IDs'
import PySpin
import cv2
import logging
from api.data_classes import CameraSettingsConfig

logging.basicConfig(level=logging.INFO)

# import serial.tools.list_ports as list_ports
from api.camera import (
    SpinnakerCamera,
    USBCamera
    )

def get_unique_ids() -> list[str]:
    'Get a list of unique camera IDs for all the different types of cameras connected to the machine'
    
    unique_id_list = []
    
    # PySpin system
    pyspin_system = PySpin.System.GetInstance()
    pyspin_cam_list = pyspin_system.GetCameras()
    for cam in pyspin_cam_list:
        # Get cam serial number
        cam.Init()
        cam_id: tuple[str] = f"{cam.DeviceSerialNumber()}-spinnaker"
        unique_id_list.append(cam_id)

    
    return sorted(unique_id_list)

def init_camera(unique_id: str):
    if unique_id is None:
        logging.error('No camera selected')
        return None
    # split the unique_id into the api and the unique id
    try:
        serial_number, api = unique_id.split('-')
    except ValueError:
        raise ValueError('Invalid unique_id')
    if api == 'spinnaker':
        return SpinnakerCamera(unique_id)
    if api == 'usb':
        return USBCamera(int(unique_id), None)

def load_saved_setups(database) -> list[CameraSettingsConfig]:
    '''Function to load the saved setups from the database as a list of Setup objects'''
    setups_from_database = []
    for cam in database.camera_dict: 
        setups_from_database.append(
            CameraSettingsConfig(
                name      = cam['name'],
                unique_id = cam['unique_id'],
                )
            )
    return setups_from_database



if __name__ =='__main__':
    get_unique_ids()