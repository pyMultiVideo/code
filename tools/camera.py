
import numpy as np
from datetime import datetime
import logging
import PySpin
import cv2_enumerate_cameras
import cv2
# Import the dataclass
from tools.data_classes import CameraSettingsConfig

# Documentation for the Camera Object

class GenericCamera():
    '''
    Parent class for implementing new cameras. This class will include generic versions if the functions that will need to be implemented for implementing new cameras with specific requirements 
    '''
    def __init__(self, camera):
    
        self.camera = camera
        self.logger = logging.getLogger(__name__)
        self.buffer_list = []
    def is_initialized(self) -> bool:
        return False
    
    def is_streaming(self) -> bool:
        return False
        
    def get_GPIO_data(self) -> dict[str, bool]:
        'Get the GPIO data from the camera as a dictionary of the GPIO lines and their associated states'
        return {'GPIO1': False, 'GPIO2': False, 'GPIO3': False, 'GPIO4': False}

    def begin_capturing(self) -> None:
        pass
    
    def stop_capturing(self) -> None:
        pass
    
    def getCameraSettingsConfig(self) -> CameraSettingsConfig: 
        '''
        Function that returns the CameraSettingsConfig datastructure. 
        '''
        return CameraSettingsConfig(
            name = 'GenericCamera',
            unique_id = self.get_unique_id(),
            fps = self.get_frame_rate(),
            pxl_fmt = self.get_pixel_format()
        )

class SpinnakerCamera(GenericCamera):
    'Inherits from the camera class and adds the spinnaker specific functions from the PySpin library'
    def __init__(self, unique_id: str, CameraConfig = None):
        super().__init__(self)
        self.camera_config = CameraConfig
        # Logger
        self.logger = logging.getLogger(__name__)
        self.system = PySpin.System.GetInstance()
        self.unique_id = unique_id
        self.serial_number, self.api = unique_id.split('-')
        self.cam = self.system.GetCameras().GetBySerial(self.serial_number)
        
        print('Camera:', self.cam)
        self.cam.Init()
        self.set_buffer_handling_mode()
        self.stream_nodemap = self.cam.GetTLStreamNodeMap()

        self.setupChunkSelector()

        if self.camera_config is not None:
            self.set_frame_rate(self.camera_config.fps)
            self.set_pixel_format(self.camera_config.pxl_fmt)
        else:   
            self.fps            = self.get_frame_rate()
            
        self.exposure_time  = self.get_exposure_time()
        self.width          = self.get_width()
        self.height         = self.get_height()
        self.gain           = self.get_gain()
        self.pxl_fmt        = self.get_pixel_format()
        self.bitrate        = self.get_bitrate()
    
    def setupChunkSelector(self):
        """
        Setup the Chunk selector         
        """
        self.cam.ChunkSelector.SetValue(PySpin.ChunkSelector_Timestamp)
        self.cam.ChunkEnable.SetValue(True)
        self.cam.ChunkModeActive.SetValue(True)
    
    # Functions to get the camera parameters
    
    
    def get_exposure_time(self) -> int:
        """
        This Python function retrieves the exposure time value from a camera node map.
        :return: The `get_exposure_time` function returns an integer value representing the exposure
        time of a camera.
        """
        nodemap = self.cam.GetNodeMap()       
        return PySpin.CFloatPtr(nodemap.GetNode("ExposureTime")).GetValue()
    
    def get_width(self) -> int:
        """
        This Python function retrieves the width value from a node map using the PySpin library.
        :return: The `get_width` method returns the width value of the camera image as an integer. It
        retrieves the width node from the camera node map and returns its integer value.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("Width")).GetValue()
    
    def get_height(self) -> int:
        """
        This Python function retrieves the height value from a camera node map.
        :return: The `get_height` method returns the height value of the camera image as an integer. It
        retrieves the height node from the camera node map and returns its integer value.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("Height")).GetValue()
    
    def get_frame_rate(self) -> int:
        """
        This Python function retrieves the frame rate value from a camera node map.
        :return: The `get_frame_rate` method returns the frame rate value as an integer.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate")).GetValue()
    
    def get_frame_rate_range(self) -> tuple[int, int]: 
        """
        Function that returns a tuple of ints that describes the minimum and maximum framerate

        Returns:
            tuple[int, int]: Minimum framerate and Maximum Frame rate 
        """
        
        node_frame_rate = PySpin.CFloatPtr(self.cam.GetNodeMap().GetNode("AcquisitionFrameRate"))
        if PySpin.IsAvailable(node_frame_rate) and PySpin.IsReadable(node_frame_rate):
            min_frame_rate = node_frame_rate.GetMin()
            max_frame_rate = node_frame_rate.GetMax()
        else:
            print("Frame rate node is not readable.")

        return min_frame_rate, max_frame_rate
    
    def get_gain(self) -> int:
        """
        This Python function retrieves the gain value from a camera node map using the PySpin library.
        :return: The `get_gain` method returns the current gain value of the camera.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CFloatPtr(nodemap.GetNode("Gain")).GetValue()
    
    def get_pixel_format(self) -> str:
        """
        This Python function retrieves the current pixel format of an image using the PySpin library.
        :return: The `get_pixel_format` method returns a string representing the current pixel format of
        the camera. It retrieves the pixel format from the camera's node map and returns the symbolic
        representation of the current pixel format.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat")).GetCurrentEntry().GetSymbolic()
    
    def get_bitrate(self) -> int:
        """
        This Python function retrieves the bitrate value from a camera node map using the PySpin
        library.
        :return: The `get_bitrate` method returns an integer value representing the bitrate obtained
        from the node "DeviceLinkThroughputLimit" in the camera's node map.
        """
        nodemap = self.cam.GetNodeMap()
        return PySpin.CIntegerPtr(nodemap.GetNode("DeviceLinkThroughputLimit")).GetValue()
    
    def get_unique_id(self) -> str:
        '''Returns the unique id of the camera that is used in the pyMultiVideo application'''
        return self.unique_id
    
    
    ## Buffer handling functions
    
    def set_buffer_handling_mode(self, mode: str = 'OldestFirst') -> None:
        '''
        Sets the buffer handling mode.
        
        By default, the buffer handling mode is set to 'OldestFirst'. This means that the oldest image in the buffer is the first to be retrieved.
        
        Alternative modes are:
        - NewestFirst
        - NewestOnly
        - OldestFirstOverwrite
        
        See: https://www.teledynevisionsolutions.com/en-gb/support/support-center/application-note/iis/accessing-the-on-camera-frame-buffer/
        
        For this implementation, use of oldest first is important as the camera releases the images in the order they are collected.
        If the buffer is not emptied in this order then the images will be encoded in the wrong order which is bad
        
        '''
        if mode not in ['OldestFirst']:
            # Raise a warning if the mode is not set to 'OldestFirst'
            self.logger.warning(f"Buffer handling mode '{mode}' is not 'OldestFirst'.")
        
        try:
            
            # Access the Transport Layer Stream (TLStream) node map
            stream_nodemap = self.cam.GetTLStreamNodeMap()

            # Set buffer handling mode
            node_buffer_handling_mode = PySpin.CEnumerationPtr(stream_nodemap.GetNode("StreamBufferHandlingMode"))

            # Check if the node exists and is writable
            if PySpin.IsAvailable(node_buffer_handling_mode) and PySpin.IsWritable(node_buffer_handling_mode):
                node_mode_value = node_buffer_handling_mode.GetEntryByName(mode)  # Change to desired mode
                if PySpin.IsAvailable(node_mode_value) and PySpin.IsReadable(node_mode_value):
                    node_buffer_handling_mode.SetIntValue(node_mode_value.GetValue())
                    print(f"Buffer Handling Mode set to: {node_mode_value.GetSymbolic()}")
    
        except PySpin.SpinnakerException as ex:
            print(f"Error setting buffer handling mode: {ex}")

    def get_buffer_handling_mode(self) -> str:
        '''Function that returns the current buffer handling mode'''
        try:
            # Access the Transport Layer Stream (TLStream) node map
            stream_nodemap = self.cam.GetTLStreamNodeMap()

            # Get buffer handling mode
            node_buffer_handling_mode = PySpin.CEnumerationPtr(stream_nodemap.GetNode("StreamBufferHandlingMode"))

            # Check if the node exists and is readable
            if PySpin.IsAvailable(node_buffer_handling_mode) and PySpin.IsReadable(node_buffer_handling_mode):
                mode = node_buffer_handling_mode.GetCurrentEntry().GetSymbolic()
                print(f"Buffer Handling Mode: {mode}")
                return mode
            
        except PySpin.SpinnakerException as ex:
            print(f"Error getting buffer handling mode: {ex}")
            return None
        

    def get_current_buffer_count(self) -> int:
        '''
        Function that returns the total number of images in the buffer at the moment.
        '''
        
        node_buffer_count = PySpin.CIntegerPtr(self.stream_nodemap.GetNode("StreamAnnouncedBufferCount"))
        try:
            if PySpin.IsAvailable(node_buffer_count) and PySpin.IsReadable(node_buffer_count):
                buffer_count = node_buffer_count.GetValue()
                # print(f"Total number of images in buffer: {buffer_count}")
            else:
                # print("Unable to retrieve the number of images in the buffer.")
                pass
        except PySpin.SpinnakerException as ex:
            print(f"Error retrieving buffer count: {ex}")

        return buffer_count

    def get_buffer_count(self) -> int:
        
        
        buffer_queued = PySpin.CIntegerPtr(self.stream_nodemap.GetNode("StreamBufferCountQueued"))
        try:
            # if PySpin.IsAvailable(buffer_queued) and PySpin.IsReadable(buffer_queued):
            print(f"Current frames in buffer: {buffer_queued.GetValue()}")

        except PySpin.SpinnakerException as ex:
            print(f"Error retrieving buffer count: {ex}")
            
    def getCameraSettingsConfig(self) -> CameraSettingsConfig:
        '''
        Returns the camera settings as a CameraSettingsConfig object.        
        '''
        return CameraSettingsConfig(
            name = 'Config returned from SpinnakerCamera wrapper. This does not have access to the name variable. Consider implementing.',
            unique_id = self.get_unique_id(),
            fps = self.get_frame_rate(),
            pxl_fmt = self.get_pixel_format()
        )
    
    # Functions to set the camera parameters

    def set_frame_rate(self, frame_rate: int) -> None:
        '''
        Function to set the frame rate of the camera.
        '''
        ## Make sure that frame rate is an int
        if type(frame_rate) is str:
            frame_rate = int(frame_rate)
        
        nodemap = self.cam.GetNodeMap()
        
        try: 
            # Disable automatic frame rate control if applicable
            if PySpin.IsAvailable(nodemap.GetNode('AcquisitionFrameRateEnable')) and PySpin.IsWritable(nodemap.GetNode('AcquisitionFrameRateEnable')):
                node_acquisition_frame_rate_enable = PySpin.CBooleanPtr(nodemap.GetNode('AcquisitionFrameRateEnable'))
                node_acquisition_frame_rate_enable.SetValue(True)
                print("Frame rate control enabled.")
            
            # Set frame rate value
            node_frame_rate = PySpin.CFloatPtr(nodemap.GetNode('AcquisitionFrameRate'))
            if PySpin.IsAvailable(node_frame_rate) and PySpin.IsWritable(node_frame_rate):
                node_frame_rate.SetValue(frame_rate)
                print(f"Frame rate set to {frame_rate} FPS.")
            else:
                print("Frame rate control is not available.")
        
        except PySpin.SpinnakerException as ex:
            print(f"Error Setting Frame Rate: {ex}")
        
        
    def set_pixel_format(self, pxl_fmt:str) -> None:
        '''Function to set the format of the camera'''


        
    def get_available_pixel_fmt(self) -> list[str]:
        '''Gets a string of the pixel formats available to the camera'''
        
        available_pxl_fmts = []
        
        node_map = self.cam.GetNodeMap()
        pixel_format_node = PySpin.CEnumerationPtr(node_map.GetNode("PixelFormat"))

        if not PySpin.IsAvailable(pixel_format_node) or not PySpin.IsReadable(pixel_format_node):
            print("PixelFormat node is not available or readable.")
        else:
            pixel_format_entries = pixel_format_node.GetEntries()
            for entry in pixel_format_entries:
                entry = PySpin.CEnumEntryPtr(entry)
                if PySpin.IsReadable(entry):
                    available_pxl_fmts.append(entry.GetSymbolic())
        print(available_pxl_fmts)
        return available_pxl_fmts
    # Function to aquire images from the camera
          
    def begin_capturing(self) -> None:
        '''BUG: without the try except block, the program crashes when a config file is loaded for the second time.
        The except loops fixes this problem. however, the error is not caught.
        '''
        try:
            # initialize the camera if it is not already initialized
            if not self.cam.IsInitialized():
                self.cam.Init()
                print(f'Camera {self.serial_number} has been initialized.')
            if not self.cam.IsStreaming():
                self.cam.BeginAcquisition()
                print(f'Camera {self.serial_number} is in acquisition mode.')
            print(f'Begin capturing: {self.serial_number}')
        except PySpin.SpinnakerException as e:
            self.logger.error(f"Error during begin capturing: {e}")
            print(f"Error during begin capturing: {e}")
            raise
            
    def get_next_image(self) -> np.ndarray:
        '''
        Function to get the next image from the camera (one at a time).
        
        In the PySpin API, this function is a blocking function. i.e. running this function will stop the rest of the program
        running until is has completed its own task. 
        '''
        
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

        # This function is not going to release data from the buffer since it will only be used to display the current image.
        next_image.Release()

        # Return the image
        return self.next_image

    def retrieve_buffered_data(self) -> dict[list[np.ndarray], list[dict[str, bool]], list[int]]:
        '''
        This function returns a list of images and a corresponding list of the GPIO data
        This is passed to a function that will saved the data to a file in batches of the lengths of theses lists. 


        How this function works 
        =======================
        self.cam.GetNextImage() is a blocking function. This means that it will wait until the next image is available before returning.
        The '0' argument in the GetNextImage() function is the timeout. This is set to 0 to make the function non-blocking.
        It will therefore get images as fast as possible. If there are no images available, the function will raise an exception.
        This is the signal that the buffer is empty.
        
        We handle the exception and return the buffer of images (and corresponding GPIO data). This is sent the encoder in the main logic of the GUI.
        

        The format of the GPIO pin states is a dictionary. Therefore the data itself is the dict.value() of this dictionary.
        The current implemenation requires that you are just sending the GPIO data to the function that saves it to disk. 
        The writer function requires a list of bools to be passed to it.
        '''
        self.img_buffer=[]
        self.gpio_buffer=[]
        self.timestamps_buffer=[]
        try:
            while True:
                # Get the next image
                next_image = self.cam.GetNextImage(0)
                # Get information about the image

                
                next_image.Release()
                self.img_buffer.append(
                    next_image.GetNDArray()
                    )
                # Get the GPIO data
                self.gpio_buffer.append(
                    list(self.get_GPIO_data().values())
                    )
                # Get chunk data
                self.timestamps_buffer.append(
                    self.get_image_time_stamp(
                        next_image = next_image
                    )
                )
                
        except PySpin.SpinnakerException as e:
            # When the buffer is empty, the 'GetNextImage' function will raise an exception.
            # This marks the end of the buffer.
            # print(f'PySpin Exeception Raised {e}. The buffer has been emptied.')
            pass
        finally:
            return {
                "images": self.img_buffer,
                "gpio_data": self.gpio_buffer,
                "timestamps": self.timestamps_buffer
            }


    def get_image_time_stamp(self, next_image) -> datetime:
        '''Function for getting the timestamp of an image as a datetime object'''
        chunk_data = next_image.GetChunkData()
        # Convert to datetime-readable number
        time_stamp_int = chunk_data.GetTimestamp() / 1e9
        # return the datetime object
        return datetime.fromtimestamp(time_stamp_int)  
              
    def stop_capturing(self) -> None:
        if self.cam.IsStreaming():
            print(f'Camera {self.serial_number} has stopped aquisiton.')
            self.cam.EndAcquisition()
        if self.cam.IsInitialized():
            self.cam.DeInit()
            print(f'Camera {self.serial_number} has been deinitialized.')
        # make sure to release the camera

            
    def isStreaming(self) -> bool:
        return self.cam.IsStreaming()
            
    def get_GPIO_data(self) -> dict[str, bool]:
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
    
    def is_initialized(self) -> bool:
        return self.cam.IsInitialized()
        
    def is_streaming(self) -> bool:
        return self.cam.IsStreaming()
class USBCamera(GenericCamera):
    '''Class for handling USB cameras. This implementation used the cv2 and cv2_enumerate_cameras libraries'''

    def __init__(self, unique_id: str, color: bool = True):
        super().__init__(self)
        self.logger = logging.getLogger(__name__)
        pid, api = unique_id.split('-')
        self.pid = int(pid)
        self.color = color
        self._init_camera()
        self.get_camera_parameters()
        
        
    def _init_camera(self):
        '''For USB camera, this function initializes the cv2.VideoCapture object'''
        # Use cv2_enumerate_cameras to get the total list of usb cameras 
        usb_cam_list = cv2_enumerate_cameras.enumerate_cameras()
        # Search this list for the camera with the pid
        for cam in usb_cam_list:
            if cam.pid == self.pid:
                self.camera = cam
                break
        # Initialize the camera
        
        self.capture = cv2.VideoCapture(self.camera.index, self.camera.backend)
    
    def get_camera_parameters(self):
        '''Get the camera parameters'''
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f'Camera parameters: {self.fps}, {self.width}, {self.height}')


    def is_streaming(self) -> bool:
        '''Always recording'''
        return True
    
    def is_initialized(self) -> bool:
        '''Always initialized'''
        return True
    
    
    def get_next_image(self) -> np.ndarray:
        ret, frame = self.capture.read()
        # convert the frame to monochrome if the color is set to false
        if self.color:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else: 
            pass
        return frame
    
    def get_next_image_list(self) -> list[np.ndarray]:
        '''Get all the images in the buffer. Here there is no buffer so the only image that is returned is from the normal function call , just reformatted.'''
        return [self.get_next_image()]
    
if __name__ == '__main__':
    pass