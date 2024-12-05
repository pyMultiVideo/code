'Functions for loading the camera IDs'
# Different imports for running the script from different places
if __name__ == '__main__':
    from camera import (
        SpinnakerCamera,
        USBCamera
        )
    from data_classes import CameraSettingsConfig
else:   
    from tools.camera import (
        SpinnakerCamera,
        USBCamera
        )
    from tools.data_classes import CameraSettingsConfig

import cv2_enumerate_cameras
import PySpin
import logging
logging.basicConfig(level=logging.INFO)

# Library for handling usb cameras

def get_usb_cameras_list() -> list[str]:
    'Get a list of the USB cameras connected to the machine'
    usb_cam_list = cv2_enumerate_cameras.enumerate_cameras()
    # Preprocess this list because it returns duplicates sometimtes
    for cam1 in usb_cam_list:
        for cam2 in usb_cam_list:
            if cam1.path == cam2.path:
                usb_cam_list.remove(cam2)

    return usb_cam_list

def get_unique_ids(VERBOSE:bool = False) -> list[str]:
    """Get a list of unique camera IDs for all the different types of cameras connected to the machine."""
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
    # pyspin_system.ReleaseInstance()
    
    # # USB CAMERAS
    # usb_cam_list = get_usb_cameras_list()
    # for cam in usb_cam_list:
    #     cam_id: str = f"{cam.pid}-usb"
    #     if VERBOSE:
    #         print(f"Camera ID: {cam_id}")
    #     unique_id_list.append(cam_id)
    
    
    
    return sorted(unique_id_list)

def init_camera(unique_id: str, CameraSettingsConfig: CameraSettingsConfig = None):
    if unique_id is None:
        logging.error('No camera selected')
        return None
    # split the unique_id into the api and the unique id
    try:
        serial_number, api = unique_id.split('-')
    except ValueError:
        raise ValueError('Invalid unique_id')
    if api == 'spinnaker':
        return SpinnakerCamera(unique_id, CameraSettingsConfig)
    if api == 'usb':
        return USBCamera(unique_id, CameraSettingsConfig)

def load_saved_setups(database) -> list[CameraSettingsConfig]:
    '''Function to load the saved setups from the database as a list of Setup objects'''
    setups_from_database = []
    for cam in database.camera_dict: 
        setups_from_database.append(
            CameraSettingsConfig(
                name      = cam['name'],
                unique_id = cam['unique_id'],
                fps       = cam['fps'],
                pxl_fmt   = cam['pxl_fmt']
                )
            )
    return setups_from_database



if __name__ =='__main__':
    # print(get_usb_cameras_list())
    print(get_unique_ids())