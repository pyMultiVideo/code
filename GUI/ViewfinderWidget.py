# core python
import numpy as np
import cv2
import json, csv, time
import logging
from datetime import datetime

from GUI.CameraSetupTab import CamerasTab
from tools.load_camera import init_camera
from tools.camera_options import cbox_update_options
from tools.camera import SpinnakerCamera as CameraObject
from tools.data_classes import CameraSetupConfig
# gui

from PyQt6.QtWidgets import (
    QGroupBox, 
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTextEdit
    )
import pyqtgraph as pg
from PyQt6.QtGui import (
    QIcon
    )
from PyQt6.QtCore import (
    Qt
)
# video
import ffmpeg


class Viewfinder(QWidget):
    '''
    Widget for each camera to be viewed
    '''
    def __init__(self, 
        parent,
        label, 
        subject_id,
        ):
        super(Viewfinder, self).__init__(parent)
        self.view_finder = parent
        self.camera_setup_tab: CamerasTab = self.view_finder.GUI.camera_setup_tab
        # Camera object is the camera api that is being used that has generic versions of the core functions
        self.logger = logging.getLogger(__name__)
        # Camera attributes
        self.label = label
        self.subject_id = subject_id
        
        # Check if the camera label is in the database. If is it, we can use the Settings Config information 
        # to set the camera settings. 
        
        if self.label in self.camera_setup_tab.get_camera_labels():
            self.camera_settings = self.camera_setup_tab.getCameraSettingsConfig(self.label)
        self.fps        = self.camera_settings.fps
        self.pxl_fmt    = self.camera_settings.pxl_fmt
        self.unique_id = self.camera_settings.unique_id
        
        self.camera_object: CameraObject = init_camera(
            self.unique_id, self.camera_settings)
        
        self.cam_width  = self.camera_object.width
        self.cam_height = self.camera_object.height
        

        # Layout
        self._init_camera_setup_groupbox()
        self._set_camera_setup_layout()
        self._page_layout()
        self._init_recording()


    def _page_layout(self):
        self.setLayout(self.camera_setup_hlayout)

    def _init_camera_setup_groupbox(self):
        
        self._initialise_video_feed()
        
        
        self.camera_setup_groupbox = QGroupBox(f"{self.label}")
        
        # Header Layout for groupbox
        self.camera_header_layout = QHBoxLayout()
        
        # Downsampling factor
        self.downsampling_factor_label = QLabel('Downsampling Factor:')
        self.downsampling_factor_text = QComboBox()
        self.downsampling_factor_text.addItems(['1', '2', '4', '8'])
        self.downsampling_factor_text.setCurrentText('1')
        self.downsampling_factor = 1
        self.downsampling_factor_text.currentTextChanged.connect(self.change_downsampling_factor)
        
        # Pxl fmt
        self.pxl_fmt_label = QLabel('Pixel Format:')
        self.pxl_fmt_cbox = QComboBox()
        self.pxl_fmt_cbox.addItems(['yuv420p', 'bgr24'])
        self.pxl_fmt_cbox.setCurrentText('yuv420p') # default settings
        self.pxl_fmt_cbox.currentTextChanged.connect(self.change_pxl_fmt)
        self.pxl_fmt_cbox.setEnabled(False)
        
        # FPS
        self.fps_label = QLabel('FPS:')
        self.fps_text = QComboBox()
        self.fps_text.addItems(['30', '60', '120'])
        self.fps_text.setCurrentText('30')
        self.fps_text.currentTextChanged.connect(self.change_fps)
        self.fps_text.setEnabled(False)
        
        # Subject ID
        self.subject_id_label = QLabel('Subject ID:')
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.subject_id)
        self.subject_id_text.textChanged.connect(self.update_subject_id)

        # Button for recording video 
        self.start_recording_button = QPushButton('')
        self.start_recording_button.setIcon(QIcon('assets/icons/record.svg'))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.setEnabled(False)
        self.start_recording_button.clicked.connect(self.start_recording)
        
        # Button for stopping recording
        self.stop_recording_button = QPushButton('')
        self.stop_recording_button.setIcon(QIcon('assets/icons/stop.svg'))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        
        self.camera_id_label = QLabel('Camera ID:')
        # Dropdown for selecting the camera
        self.camera_dropdown = QComboBox()
        # set the current text to the camera label
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        self.update_camera_dropdown()
        self.camera_dropdown.setCurrentText(self.label)
        # Add the widgets to the layout
        self.camera_header_layout.addWidget(self.camera_id_label)
        self.camera_header_layout.addWidget(self.camera_dropdown)
        self.camera_header_layout.addWidget(self.downsampling_factor_label)
        self.camera_header_layout.addWidget(self.downsampling_factor_text)
        self.camera_header_layout.addWidget(self.fps_label)
        self.camera_header_layout.addWidget(self.fps_text)
        self.camera_header_layout.addWidget(self.pxl_fmt_label)
        self.camera_header_layout.addWidget(self.pxl_fmt_cbox)
        self.camera_header_layout.addWidget(self.subject_id_label)
        self.camera_header_layout.addWidget(self.subject_id_text)
        self.camera_header_layout.addWidget(self.start_recording_button)
        self.camera_header_layout.addWidget(self.stop_recording_button)
        # Set the layout for the groupbox
        self.camera_setup_groupbox.setLayout(self.camera_header_layout)
        self.camera_setup_groupbox.setFixedHeight(100)
        
    def _initialise_video_feed(self):
        self.video_feed = pg.ImageView()
        self.video_feed.ui.histogram.hide()
        self.video_feed.ui.roiBtn.hide()
        self.video_feed.ui.menuBtn.hide()
        # Disable zoom and pan
        self.video_feed.view.setMouseEnabled(x=False, y=False)
        self.text = pg.TextItem()
        self.text.setPos(10, 10)
        self.video_feed.addItem(self.text)
        self.text.setText('NOT RECORDING', color='r')
        self._init_GPIO_overlay()
        
    def _set_camera_setup_layout(self):
        self.camera_setup_hlayout = QVBoxLayout()
        
        self.camera_setup_hlayout.addWidget(self.camera_setup_groupbox)
        self.camera_setup_hlayout.addWidget(self.video_feed)

    def _init_recording(self):
        # Set the recording flag to False
        self.recording = False
        # Default width and hieght for the camera widget
        self.width  = self.cam_width
        self.height = self.cam_height

        self.validate_subject_id_input()
        
        self.camera_object.begin_capturing()
        # self.display_frame(self.camera_object.get_next_image())

        
    def fetch_image_data(self) -> None:
        '''
        Function that gets both the GPIO and the image data from the camera and sends them 
        to the encodeing function to be saved to disk.
        '''

        try:
            # Retrieve the latest image from the camera
            self.img_buffer, self.gpio_buffer = self.camera_object.retrieve_buffered_data()
            if len(self.img_buffer) == 0:
                return # exit the function and wait to be called by the viewfinder tab. 
            # Assign the first image of to the data to be displayed
            self._image_data = self.img_buffer[0]
            # If the recording flag is True
            if self.recording == True:
                self.recorded_frames += len(self.img_buffer)
                # encode the frames
                self.encode_frame_from_camera_buffer(
                    frame_buffer = self.img_buffer
                    )
                # encode the GPIO data
                self.write_gpio_data_from_buffer(
                    gpio_buffer = self.gpio_buffer
                    )
        except Exception as e:
            # print(f"Error fetching image data: {e}")
            # print(self.camera_object.buffer_list)
            pass

                

    def get_mp4_filename(self) -> str:
        '''Get the filename for the mp4 file. This is done using GUI information'''
        self.subject_id = self.subject_id_text.toPlainText()
        
        self.recording_filename = \
            self.view_finder.save_dir_textbox.toPlainText() + \
            '/' + f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
        
        self.logger.info(f'Saving recording to: {type(self.recording_filename)}')
        
    def update_camera_dropdown(self):
        '''Update the camera options
        NOTE: this function is wrapped in functions to disconnect and reconnect the signal to the dropdown when the function changes the text in the dropdown
        the combobox is filled with the other camera label and the correct camera is not an option in the dropdown. 
        '''
        # disconnect self.camera_dropdown from the current function
        self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        cbox_update_options(
            cbox = self.camera_dropdown, 
            options = self.camera_setup_tab.get_camera_labels(), 
            used_cameras_labels = list([cam.label for cam in self.view_finder.camera_groupboxes]),
            selected = self.label
            )
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        
        
    def get_gpio_filename(self, header= None) -> str:
        """
        This Python function creates a CSV file with a specified header containing GPIO data.
        
        :param header: The `header` parameter in the `get_gpio_filename` function is a list of strings
        that represent the column headers for the CSV file that will be created. In this case, the
        default header list is `['Line1', 'Line2', 'Line3', 'Line4']`, but
        :type header: list
        """
        # Get the subject ID from the text field
        self.subject_id = self.subject_id_text.toPlainText()
        
        self.GPIO_filename = \
            self.view_finder.save_dir_textbox.toPlainText() + \
            '/' + f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_GPIO_data.csv"
        if header == None:    
            header = ['Line1', 'Line2', 'Line3', 'Line4']
        with open(self.GPIO_filename, mode = 'w', newline='') as self.f:
            writer = csv.writer(self.f)
            writer.writerow(header)
    
    def get_metadata_filename(self) -> str:
        '''Get the filename for the metadata file'''
        self.subject_id = self.subject_id_text.toPlainText()
        
        self.metadata_filename = \
            self.view_finder.save_dir_textbox.toPlainText() + \
            '/' + f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_metadata.json"
        
        
    def display_frame(self, image_data: np.array) -> None:
        '''
        Display the image on the GUI
        
        This function also calls the the relevent functions to add overlays on the image.
        '''
        try:
            # Display the image on the GUI
            self.video_feed.setImage(image_data.T)
            # Display the GPIO data on the image
            # self.get_GPIO_data()
            # self.draw_GPIO_overlay()
            # # # Recording status overlay
            self.draw_status_overlay()
            
        except Exception as e:
            
            print(f"Error displaying image: {e}")
            
            
    def draw_status_overlay(self):
        '''
        Draw the status of the recording on the image. This simply changes the color of an attribute that is been placed
        onto the image during initialisation.
        '''
        if self.recording == True:
            status = 'RECORDING'
            color = 'g'
        elif self.recording == False:
            status = 'NOT RECORDING'
            color = 'r'
        self.text.setText(status, color=color)  
        
    def _init_GPIO_overlay(self):
        '''Initialise the GPIO data'''
        
        # Initial state of the colour painted to the image
        self.gpio_over_lay_color: list[int, int, int] = [0, 0, 0]
        
        x_position = 100
        y_position = 100
        self.ellipse = pg.EllipseROI([x_position, y_position], [50,50], 
                                    pen=pg.mkPen(color=self.gpio_over_lay_color, 
                                                width=2),
                                    movable     =False,
                                    rotatable   =False,
                                    resizable   =False,
                                    aspectLocked=True,
                                    )
        self.video_feed.addItem(self.ellipse)
        
    def draw_GPIO_overlay(self) -> None:
        '''Draw the GPIO data on the image'''
        DECAY = 0.9
        if self.GPIO_data == None:
            self.gpio_over_lay_color = DECAY * np.array(self.gpio_over_lay_color)
        elif self.GPIO_data != None:
            for i, line in enumerate(self.GPIO_data):
                if i == 3:
                    # skip the last line
                    continue
                new_color = self.gpio_over_lay_color.copy()
                if line == 1:
                    new_color[i] = 255
                elif line == 0:
                    new_color[i] = 0
            self.gpio_over_lay_color = DECAY * np.array(new_color) + (1 - DECAY) * np.array(self.gpio_over_lay_color)

        # update the color of the ellipse
        self.ellipse.setPen(pg.mkPen(color=self.gpio_over_lay_color, width=2))

    def refresh(self):
        '''Refresh the camera widget'''
        self.update_camera_dropdown()

        

        
    def _init_ffmpeg_process(self) -> None:
        '''
        This function initalising the ffmpeg process.
        
        This uses the ffmpeg-python API. This api does little more than make the syntax for ffmpeg nicer.
        
        The FFMPEG process is a separate process (according to task-manager) that is running in the background.
        It runs on the GPU (if you let the encoder be a GPU encoder) and is not blocking the main thread.
        
        '''
        
        self.get_mp4_filename()
        self.get_gpio_filename()

        
        # Calculate downsampled width and height. The preset value is one. 
        downsampled_width = int(self.cam_width / self.downsampling_factor)
        downsampled_height = int(self.cam_height / self.downsampling_factor)
        

        # Set up an ffmpeg encoding pipeline
        self.ffmpeg_process = (
            ffmpeg
            .input(
                'pipe:', 
                format='rawvideo', 
                pix_fmt='gray', 
                s=f'{downsampled_width}x{downsampled_height}', 
                framerate=self.fps
                )
            .output(
                self.recording_filename, 
                vcodec=self.view_finder.encoder,
                pix_fmt=self.pxl_fmt, 
                preset='fast', 
                crf=23
                )
            .run_async(
                pipe_stdin=True
                )
        )
        print('FFmpeg pipeline initialized')
        self.logger.info('FFmpeg pipeline initialized')

        
    
    def encode_frame_ffmpeg_process(self, frame: np.array) -> None:
        '''
        The `encode_frame_ffmpeg_process` function encodes the frame using the ffmpeg pgrocess.
        
        :param frame: np.array - frame to be encoded
        '''
        try:
            # Write the frame to the ffmpeg process
            self.ffmpeg_process.stdin.write(frame.tobytes())
            
        except Exception as e:
            print(f"Error encoding frame: {e}")
        
        
    def encode_frame_from_camera_buffer(self, frame_buffer: list[np.ndarray]) -> None:    
        '''
        Encodes the frames from the camera buffer and writes them to the file. 
        '''
        try: 
            while frame_buffer:
                # Get the frame from the buffer (front of the queue)
                frame = frame_buffer.pop(0)
                # Encode the frame
                self.encode_frame_ffmpeg_process(frame)
                
        except Exception as e:
            print(f"Error encoding frame: {e}")
        
    def write_gpio_data_to_csv(self, gpio_data: list[bool]) -> None:
        """
        The function `encode_gpio_data` writes GPIO data to a file in CSV format.
        
        :param gpio_data: The `gpio_data` parameter is a list of boolean values representing the GPIO
        data that needs to be encoded and written to a file. The `encode_gpio_data` method takes this
        list of boolean values and writes them to a file specified by `self.GPIO_filename`. If an error
        occurs during the encoding
        :type gpio_data: list[bool]
        """
        try:
            # Converts the list of bools to a list of ints, because writing ints takes a smaller number of charaters than 
            # writing the string 'True' or 'False'. 
            gpio_data = [int(x) for x in gpio_data]
            # Write the GPIO data to the file
            with open(self.GPIO_filename, mode = 'a', newline='') as self.f:
                writer = csv.writer(self.f)
                writer.writerow(gpio_data)
                
        except Exception as e:
            print(f"Error encoding GPIO data: {e}")
        
    def write_gpio_data_from_buffer(self, gpio_buffer: list[list[bool]]) -> None:
        '''
        This function is used to write the GPIO data to a file from the buffer. 
        The buffer will return a list of list of booleans. 
        The length of the outer list is the number of frames that were emptied from the buffer. 
        
        This function is a wrapper for the `encode_gpio_data` function.
        
        Parameters:
        - buffer_list: list[list[bool]] - list of GPIO data to be written to the file
        
        '''
        try:
            for gpio_data in gpio_buffer:
                self.write_gpio_data_to_csv(gpio_data)
        except Exception as e:
            print(f"Error encoding GPIO data: {e}")
        

    def create_metadata_file(self):
        '''Function to creat the metadata file and write its initial information to json'''
        #create metadata file
        self.get_metadata_filename()
        
        self.metadata = {
            'subject_ID': self.subject_id,
            'camera_unique_id': self.unique_id,
            'recording_filename': self.recording_filename,
            'GPIO_filename': self.GPIO_filename,
            'recorded_frames': self.recorded_frames,
            'begin_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recorded_frames': None,
            'end_time': None
        }

        with open(self.metadata_filename, 'w') as self.meta_data_file:
            json.dump(self.metadata, self.meta_data_file, indent=4)

    def close_metadata_file(self):
        '''Function to close the metadata file'''
        self.metadata['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.metadata['recorded_frames'] = self.recorded_frames
        with open(self.metadata_filename, 'w') as self.meta_data_file:
            # add the end time to the metadata file
            json.dump(self.metadata, self.meta_data_file, indent=4)
    
    def update_subject_id(self):
        '''Update the subject ID'''
        self.subject_id = self.subject_id_text.toPlainText()
        self.logger.info(f'Subject ID changed to: {self.subject_id}')
        self.validate_subject_id_input()
        # call the refresh function from th viewfinder class
        self.view_finder.refresh()
        
    def validate_subject_id_input(self):
        '''Change the colour of the subject ID text field'''
        if self.subject_id_text.toPlainText() == '':
            self.start_recording_button.setEnabled(False)
        else:
            self.start_recording_button.setEnabled(True)
    ### Recording Controls

    def start_recording(self) -> None:
        '''
        Function to start the recording of the video.
        
        - Set the recording flag to True
        - Initalise the ffmpeg process
        - Create the metadata file
        - Update the GUI buttons to the correct state
        '''    
        # Get the filenames
        self.get_mp4_filename()
        self.get_gpio_filename()
        self.get_metadata_filename()
        
        # Initalise ffmpeg process
        self._init_ffmpeg_process()   
        # Set the recording flag to True
        self.recording = True
        # Reset the number of recorded frames to zero
        self.recorded_frames = 0
        # Create the metadata file
        self.create_metadata_file()
        # update labels on GUI
        self.stop_recording_button.setEnabled(True)
        self.camera_dropdown.setEnabled(False)
        self.downsampling_factor_label.setEnabled(False)
        self.start_recording_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        self.fps_label.setEnabled(False)
        self.pxl_fmt_label.setEnabled(False)
        self.downsampling_factor_text.setEnabled(False)
        # Tabs can't be changed
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(False)
        
    def stop_recording(self) -> None:
        '''
        Function to stop the recording of the video.
        
        - Set the recording flag to False
        - Closes the metadata file (by writing the relevent information to it and saving it)
        - Sets the GUI buttons to the correct state
        - De-inits the ffmpeg process        
        '''        
        self.recording = False  
        self.close_metadata_file()
        # Set other buttons to now be enabled
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        self.camera_dropdown.setEnabled(True)
        self.downsampling_factor_label.setEnabled(True)
        self.fps_label.setEnabled(True)
        self.pxl_fmt_label.setEnabled(True)
        self.downsampling_factor_text.setEnabled(True)
        # Tabs can be changed
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(True)        
        self.logger.info('Recording Stopped')
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()

    def change_camera(self) -> None:

        self.logger.info('Changing camera')
        # shut down old camera
        if self.camera_object != None:
            self.camera_object.stop_capturing()
        # Get the new camera ID
        new_camera_label = str(self.camera_dropdown.currentText())
        # from the setups tab, get the unique id of the camera
        camera_unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(
            new_camera_label
            )
        self._change_camera(camera_unique_id, new_camera_label)

    def _change_camera(self, new_unique_id, new_camera_label) -> None:
        # Set the new camera name
        self.unique_id  = new_unique_id
        self.label      = new_camera_label
        # Get the new camera settings
        camera_settings = self.camera_setup_tab.getCameraSettingsConfig(self.label)        
        # Set the new camera object
        self.camera_object = init_camera(
            new_unique_id, camera_settings)
        self.camera_object.begin_capturing()
        # Call the display function once
        self.display_frame(self.camera_object.get_next_image())
        #  Update the list cameras that are currently being used. 
        self.camera_setup_groupbox.setTitle(self.label)
        
    def change_downsampling_factor(self) -> None:
        '''Change the downsampling factor of the camera'''
        self.logger.info('Changing downsampling factor')
        # Get the new downsampling factor
        downsampling_factor = int(self.downsampling_factor_text.currentText())
        # Set the new downsampling factor
        self.downsampling_factor = downsampling_factor

        
    ### Config related functions.
        
    def get_camera_config(self):
        '''Get the camera configuration'''
        return CameraSetupConfig(
            label = self.label,
            downsample_factor = self.downsampling_factor,
            subject_id = self.subject_id,
            
        )
            
    def set_camera_widget_config(self, camera_config: CameraSetupConfig):
        '''Set the settings assocaitd with the camera widget into the GUI'''
        # Check if the camera label is in the database
        if camera_config.label not in self.camera_setup_tab.get_camera_labels():
            self.logger.error(f'Camera label {camera_config.label} not found in database')
            return
        
        self.label = camera_config.label
        self.downsampling_factor = camera_config.downsample_factor
        self.unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(self.label)
        self.subject_id = camera_config.subject_id
        self._change_camera(new_unique_id = self.unique_id, new_camera_label = self.label)
        self.logger.info(f'Camera configuration set to: {camera_config}')

    ### Functions for changing the camera settings for a camera

    def rename(self, new_label):
        '''Function to rename the camera'''
        # remove the current label from the camera_dropdown widget
        # self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        self.camera_dropdown.removeItem(self.camera_dropdown.findText(self.label))
        self.label = new_label
        self.camera_dropdown.setCurrentText(new_label)        
        self.camera_setup_groupbox.setTitle(new_label)

    def change_fps(self):
        '''Change the FPS of the camera'''
        self.logger.info('Changing FPS')
        # Get the new FPS
        fps = int(self.fps_text.currentText())
        # Set the new FPS
        self.fps = fps
        # This function requires reinitalisation of the camera with the new FPS
        self.camera_object.set_frame_rate(fps)
        
    def change_pxl_fmt(self):
        '''Change the pixel format of the camera'''
        self.logger.info('Changing pixel format')
        # Get the new pixel format
        pxl_fmt = str(self.pxl_fmt_cbox.currentText())
        # Set the new pixel format
        self.pxl_fmt = pxl_fmt
        # This function requires reinitalisation of the camera with the new pixel format
        self.camera_object.set_pixel_format(pxl_fmt)
    
    ### Visibility Controls 

    def toggle_control_visibility(self) -> None:
        '''
        Toggle the visibility of the camera controls
        '''
        # add a button to connect to this funciton. 
        is_visible = self.camera_setup_groupbox.isVisible()
        self.camera_setup_groupbox.setVisible(not is_visible)

    ### Functions for disconnecting the camera from the GUI
    
    def disconnect(self):
        '''Function for disconnecting the camera from the GUI. 
        This function does the following:
        - Ends the recording from the camera object
        - Removes the camera from the grid layout
        - Deletes the camera widget when PyQt6 is ready to delete it
        It should be possible to also remove the camera from the groupboxes list from this function, however
        I have done this after this function is called, in the other places this function is called. 
        '''
        self.camera_object.stop_capturing()
        self.view_finder.camera_layout.removeWidget(self)
        self.deleteLater()