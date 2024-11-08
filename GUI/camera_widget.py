# core python
import numpy as np
import os
import json, csv
import logging
from datetime import datetime

# src
# from GUI.ViewFinder_Tab import ViewFinder_Tab
from utils.recording_utils import configure_camera_from_config
from api.load_camera import init_camera
from utils.data_classes import CameraConfig, ExperimentConfig
from utils.recording_utils import EnterKeyFilter
from api.camera import SpinnakerCamera as CameraObject
from dialogues.error_message import show_error_message



# gui
from PyQt6.QtWidgets import (
    QGroupBox, 
    QGridLayout,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTextEdit
    )
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QIcon
    )
from PyQt6.QtCore import (
    QTimer
)
# video
import PySpin
import ffmpeg
import cv2


class CameraWidget(QWidget):
    'widget for each camera to be viewed'
    def __init__(self, unique_id, api,  camera_config: CameraConfig = None, parent=None):
        super(CameraWidget, self).__init__(parent)

        self.view_finder = parent
        self.GUI_Main= self.view_finder.GUI
        
        
        self.unique_id = unique_id
        self.api = api
        
        
        self.camera_object: CameraObject = init_camera(unique_id, api)
        self.camera_config: CameraConfig = camera_config
        self.logger = logging.getLogger(__name__)
        
        
        # Layout
        self._init_camera_setup_groupbox()
        self._set_camera_setup_layout()
        self._page_layout()
        # Recording setup 
        self._init_recording()
        self._init_timers()

    def _page_layout(self):
        self.setLayout(self.camera_setup_hlayout)
        
        
    def _init_camera_setup_groupbox(self):
        self.camera_setup_groupbox = QGroupBox(f"{self.camera_config.name}")
        
        # Header Layout for groupbox
        self.camera_header_layout = QHBoxLayout()
        
        # Subject ID
        self.subject_id_label = QLabel('Subject ID:')
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.camera_config.subject_ID)
         # when text is changed, change the colour of the text field
        self.subject_id_text.textChanged.connect(self.change_subject_id_text_colour)
        self.subject_id_update_button = QPushButton('Update')
        self.subject_id_update_button.setFixedHeight(30)
        self.subject_id_update_button.setFixedWidth(60) 
        self.subject_id_update_button.clicked.connect(self.update_subject_id)

        # Button for starting video output
        self.start_playing_video_button = QPushButton('')
        self.start_playing_video_button.setIcon(QIcon('assets/icons/play.svg'))
        self.start_playing_video_button.setFixedWidth(30)
        self.start_playing_video_button.setFixedHeight(30)
        self.start_playing_video_button.clicked.connect(self.toggle_playing_video)
        self.start_playing_video_button.setStyleSheet('background-color: yellow')
        
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
        # camera_user_ids = [database.this.camera_data.user_id]
        for camera in self.view_finder.unique_ids:
            self.camera_dropdown.addItem(camera[0])
        self.camera_dropdown.setCurrentText(self.unique_id)
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        
        # Add the widgets to the layout
        self.camera_header_layout.addWidget(self.camera_id_label)
        self.camera_header_layout.addWidget(self.camera_dropdown)
        self.camera_header_layout.addWidget(self.subject_id_label)
        self.camera_header_layout.addWidget(self.subject_id_text)
        self.camera_header_layout.addWidget(self.subject_id_update_button)
        self.camera_header_layout.addWidget(self.start_playing_video_button)
        self.camera_header_layout.addWidget(self.start_recording_button)
        self.camera_header_layout.addWidget(self.stop_recording_button)
        
        # set with of header layout
        # Set the layout for the groupbox
        self.camera_setup_groupbox.setLayout(self.camera_header_layout)
        # Label for displaying the camera feed
        self.image_label = QLabel()


    def _set_camera_setup_layout(self):
        self.camera_setup_hlayout = QVBoxLayout()
        
        self.camera_setup_hlayout.addWidget(self.camera_setup_groupbox)
        self.camera_setup_hlayout.addWidget(self.image_label)
        # add the recording status label ontop of the image label
        # self.camera_setup_hlayout.addWidget(self.recording_status_label)
        
    def _init_timers(self): 
        # Frame capture timer
        self.timer = QTimer()
        self.timer.start(int(1000 / self.camera_config.fps))   
        
        # Create a variable to store the image data
        self.image_data = None
        # Display Update timer
        self.display_timer = QTimer()
        self.display_timer.start(int(1000  / self.camera_config.display_update_ps))
        
        
    ### Displaying the camera feed functions

    def _init_recording(self):
        # Set the recording flag to False
        self.recording = False
        self.playing = False

        self.camera_object.begin_capturing()
        # Set the widget width and height
        self.width  = self.camera_config.width    
        self.height = self.camera_config.height
        # set one frame to display
        self.display_frame(self.camera_object.get_next_image())
        


    def fetch_image_data(self) -> None:
        '''
        The `fetch_image_data` function retrieves the latest image from a camera and converts the image
        data to a format suitable for PyQt6 and OpenCV.
        
        image_result is returned as Mono8 Pixel format
        
        :return: The `fetch_image_data` method is returning the image data in a format suitable for
        PyQt6 and OpenCV after retrieving the latest image from the camera.
        '''
        try:
            # Retrieve the latest image from the camera
            self.image_data = self.camera_object.get_next_image()

            if self.recording == True:
                # encode the frames
                self.encode_frame_ffmpeg_process(frame=self.image_data)
                # self.encode_frame_pynvidia_api(frame=image_data)
                with open(self.GPIO_filename, mode = 'a', newline='') as self.file:
                    writer = csv.writer(self.file)
                    # get the GPIO data
                    self.get_GPIO_data()     
                                   
                    # write the GPIO data to a file
                    writer.writerow(self.GPIO_data)
                    
                


            # return image_data
    
        except PySpin.SpinnakerException as e:
            print(f"Error fetching image data: {e}")


    def get_mp4_filename(self) -> str:
        
        if os.path.exists(self.view_finder.experiment_config.data_dir) == True:
            pass
        else:
            os.makedirs(self.view_finder.experiment_config.data_dir)    
        
            
        self.recording_filename = \
            self.view_finder.experiment_config.data_dir + \
            + '/' + f"{self.camera_config.subject_ID}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
       
        
        print(f'Saving recording to: {type(self.recording_filename)}')
        
        
    def get_gpio_filename(self, header: list = [str(f'Line{i}' for i in range(1,5))]) -> str:
        """
        This Python function creates a CSV file with a specified header containing GPIO data.
        
        :param header: The `header` parameter in the `get_gpio_filename` function is a list of strings
        that represent the column headers for the CSV file that will be created. In this case, the
        default header list is `['Line1', 'Line2', 'Line3', 'Line4']`, but
        :type header: list
        """
        
        self.GPIO_filename = \
            self.view_finder.experiment_config.data_dir + \
            f"{self.camera_config.subject_ID}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_GPIO_data.csv"
            
        
        with open(self.GPIO_filename, mode = 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
        
    def display_frame(self, image_data: np.array) -> None:
        
        try:
            # Convert the image data to a format suitable for PyQt6 and OpenCV
            if image_data.ndim == 3:
                # Convert BGR to RGB for displaying in PyQt
                # image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                image_format = QImage.Format.Format_RGB888
                bytes_per_line = 3 * self.width
            elif image_data.ndim == 1 or image_data.ndim == 2:
                image_format = QImage.Format.Format_Grayscale8
                bytes_per_line = self.width
                            
            # Downscale the image to fit the GUI
            image_data = cv2.resize(image_data, (self.width, self.height))

            # Display the image in the GUI
            image = QImage(image_data.data, self.width, self.height, bytes_per_line, image_format)
            pixmap = QPixmap.fromImage(image)
            # scale down pixmap
            # pixmap = pixmap.scaled(640, 480)
            pixmap = pixmap.scaled(int(640*0.8), int(480*0.8))
            self.image_label.setPixmap(pixmap)
            
            # Update the recording status label
            if self.recording == True:
                image = QPixmap('assets/icons/record.svg')
                # self.recording_status_label.setPixmap(image)
                
            
        except Exception as e:
            print(f"Error displaying image: {e}")
            
    def display_paused_overlay(self):
        '''Display an overlayed image to show that the video is not playing'''
        
        
        
        
            
    def recording_loop(self):
        '''Function Called by the parent class every FPS (as defined in parent class)'''

        # Fetch the image data
        self.fetch_image_data()
        # Displaying on GUI

    def refresh_display(self):
        '''Function to refresh the display. Called by the parent class '''
        
        if self.playing == True:
            # The gui displays the images from the camera each function call
            self.display_frame(self.image_data)
        elif self.playing == False:
            # The gui does not update
            # TODO: add an overlayed image to show that the video is not playing 
            self.display_paused_overlay()
            pass
        
        
    def _init_ffmpeg_process(self) -> None:
        
        self.get_mp4_filename()
        self.get_gpio_filename()
        print(f'GPIO file: {self.GPIO_filename}' + '\n'
              f'MP4 file: {self.recording_filename}')  
        # Set up an ffmpeg encoding pipline
        self.ffmpeg_process = (
            ffmpeg
            .input(
                'pipe:', 
                format='rawvideo', 
                pix_fmt='gray', 
                s=f'{self.camera_config.width}x{self.camera_config.height}', 
                framerate=self.camera_config.fps
                )
            .output(
                self.recording_filename, 
                vcodec=self.view_finder.experiment_config.encoder, 
                pix_fmt=self.camera_config.pixel_format, 
                preset='fast', 
                crf=23
                )
            .run_async(
                pipe_stdin=True
                )
        )
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
        
    def get_GPIO_data(self):
        '''Write the GPIO data to a file
        
        Note: Line1, Line2, Line3, Line4, are as defined in the Chameleon3 camera PIN IO diagram
        '''
        try:
            self.GPIO_data = self.camera_object.get_GPIO_data().values()
            # convert list of booleans to list of ints
            self.GPIO_data = [int(x) for x in self.GPIO_data]

        except PySpin.SpinnakerException as ex:
            print(f"Error: {ex}")
            return None
        
    
    def update_subject_id(self):
        '''Update the subject ID'''
        self.camera_config.subject_ID = self.subject_id_text.toPlainText()
        self.logger.info(f'Subject ID changed to: {self.camera_config.subject_ID}')
        self.change_subject_id_text_colour()
        
    def change_subject_id_text_colour(self):
        '''Change the colour of the subject ID text field'''
        if self.subject_id_text.toPlainText() == self.camera_config.subject_ID:
            self.subject_id_text.setStyleSheet('background-color: white')
        else:
            self.subject_id_text.setStyleSheet('background-color: orange')
        
    def toggle_playing_video(self):
        '''Start the video playing in the GUI'''
        self.playing = not self.playing
        if self.playing == True:
            self.logger.info('Playing Video')
            
            # Connect the timers to the functions
            self.timer.timeout.connect(self.recording_loop)
            self.display_timer.timeout.connect(self.refresh_display)
            self.start_playing_video_button.setStyleSheet('background-color: orange')
    
            # Set other buttons to now be enabled
            self.start_recording_button.setEnabled(True)
            self.stop_recording_button.setEnabled(False)
            self.start_recording_button.setStyleSheet('background-color: green')
            
        elif self.playing == False:
            self.logger.info('Stopping Video')
            self.timer.timeout.disconnect(self.recording_loop)
            self.display_timer.timeout.disconnect(self.refresh_display)
            # Change color of the button
            self.start_playing_video_button.setStyleSheet('background-color: yellow')
            self.start_recording_button.setStyleSheet('background-color: red')
            
            self.start_recording_button.setEnabled(False)
            self.stop_recording_button.setEnabled(False)
            

    def start_recording(self):
        '''Start recording the video'''
        # Set the recording flag to True
        self.recording = True
        
        self.logger.info('Recording Started')
        self.stop_recording_button.setEnabled(True)
        self.start_recording_button.setEnabled(False)
        self.start_playing_video_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        
        self._init_ffmpeg_process()
        self.toggle_playing_video.setText('Stop Recording')
        self.toggle_playing_video.setStyleSheet('background-color: red')
        # button logic
        print('Changing button states')
        
    def stop_recording(self):
        
        self.recording = False  
        
        # Set other buttons to now be enabledf
        print('Changing button states')
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.start_playing_video_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        
        self.file.close()
        self.logger.info('Recording Stopped')
        
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()
        
        
    def change_camera(self):
        'Function to change which camera is being viewed'
        self.logger.info('Changing camera')
        
        # Get the new camera ID
        new_camera_id = self.camera_dropdown.currentText()
        self.logger.info(f'New camera ID: {new_camera_id}')
        # TODO: self.api must come from the new camera id's corresponding api
        # Get the new camera 
        new_camera = init_camera(new_camera_id, self.api)
        
        # shut down old camera
        self.camera_object.end_recording()
        
        # Set the new camera object
        self.camera_object = new_camera
        
        # Call the display function once
        self.camera_object.begin_capturing()
        self.fetch_image_data()
        self.display_frame(self.image_data)
        
    def de_init_camera(self):
        self.camera_object.end_recording()
        

    def on_destroyed(self):
        'Function that is called when the camera widget is being closed by the "self.deleteLater() method'
        self.logger.info('Camera Widget Destroyed')
        print('Camera Widget Destroyed')
        # deinit the camera
        self.camera_object.end_recording()