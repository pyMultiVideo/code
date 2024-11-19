# core python
import numpy as np
import os
import json, csv
import logging
import sys
from datetime import datetime

from GUI.SetupsTab import SetupsTab
from tools.load_camera import init_camera
from tools.camera_options import cbox_update_options
from api.camera import SpinnakerCamera as CameraObject
from api.data_classes import CameraSetupConfig
# gui

from PyQt6.QtWidgets import (
    QGroupBox, 
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
    QStackedLayout
    )
import pyqtgraph as pg
from PyQt6.QtGui import (
    # QImage,
    QPixmap,
    QPainter,
    QIcon,
    QColor,
    QFont,
    QBrush
    )
import PyQt6.QtCore as QtCore
from PyQt6.QtCore import (
    QTimer,
    Qt
)
# video
import PySpin
import ffmpeg
import cv2


class CameraWidget(QWidget):
    '''
    Widget for each camera to be viewed
    '''
    def __init__(self, 
        parent,
        label, 
        subject_id=None,
        fps=30,
        pixel_format='yuv420p'
        ):
        super(CameraWidget, self).__init__(parent)
        self.view_finder = parent
        self.setups_tab: SetupsTab = self.view_finder.GUI.setups_tab
        # Camera object is the camera api that is being used that has generic versions of the core functions
        self.logger = logging.getLogger(__name__)
        # Camera attributes
        self.label = label
        self.subject_id = subject_id
        self.fps = fps
        self.pixel_format = pixel_format
        self.unique_id = self.setups_tab.get_camera_unique_id_from_label(self.label)
        print('unique_id', self.unique_id)
        self.camera_object: CameraObject = init_camera(self.unique_id)
        self.resolution_width  = self.camera_object.width
        self.resolution_height = self.camera_object.height
        

        # Layout
        print('Camera Widget Created')
        self._init_camera_setup_groupbox()
        self._set_camera_setup_layout()
        self._page_layout()

        self._init_recording()


    def _page_layout(self):
        self.setLayout(self.camera_setup_hlayout)

    def _init_camera_setup_groupbox(self):
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
        # self.camera_dropdown.addItem(self.label)
        # self.camera_dropdown.setCurrentText(self.label)
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)

        self.update_camera_dropdown()

        
        # Add the widgets to the layout
        self.camera_header_layout.addWidget(self.camera_id_label)
        self.camera_header_layout.addWidget(self.camera_dropdown)
        self.camera_header_layout.addWidget(self.downsampling_factor_label)
        self.camera_header_layout.addWidget(self.downsampling_factor_text)
        self.camera_header_layout.addWidget(self.subject_id_label)
        self.camera_header_layout.addWidget(self.subject_id_text)
        self.camera_header_layout.addWidget(self.start_recording_button)
        self.camera_header_layout.addWidget(self.stop_recording_button)
        # set the hieght of the header layou
        # set with of header layout
        # Set the layout for the groupbox
        self.camera_setup_groupbox.setLayout(self.camera_header_layout)
        self.camera_setup_groupbox.setFixedHeight(100)
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
        self.width  = self.resolution_width
        self.height = self.resolution_height
        # Set one frame to display
        # Run funciton to check if the text field is empty
        self.text_field_update()
        
        # Intialise the camera to begin capturing
        if self.camera_object != None:
            self.camera_object.begin_capturing()
            self.display_frame(self.camera_object.get_next_image())
        else:
            self.display_frame(np.zeros((self.height, self.width), dtype=np.uint8))

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
                # for image in self.image_list:
                # encode the frames
                self.encode_frame_ffmpeg_process(frame=self.image_data)
                self.recorded_frames += 1
                # self.encode_frame_pynvidia_api(frame=image_data)
                with open(self.GPIO_filename, mode = 'a', newline='') as self.f:
                    writer = csv.writer(self.f)
                    # get the GPIO data
                    self.get_GPIO_data()                           
                    # write the GPIO data to a file
                    writer.writerow(self.GPIO_data)
    
        except PySpin.SpinnakerException as e:
            print(f"Error fetching image data: {e}")
            
    def get_mp4_filename(self) -> str:
        
        self.subject_id = self.subject_id_text.toPlainText()
        
        self.recording_filename = \
            self.view_finder.save_dir_textbox.toPlainText() + \
            '/' + f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
        
        
        print(f'Saving recording to: {type(self.recording_filename)}')
        
        
    def update_camera_dropdown(self):
        '''Update the camera options'''
        # disconnect self.camera_dropdown from the current function
        self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        cbox_update_options(cbox = self.camera_dropdown, 
                            options = self.setups_tab.get_camera_labels(), 
                            used_cameras_labels = list([cam.label for cam in self.view_finder.camera_groupboxes]),
                            selected = self.label)
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
        
        self.subject_id = self.subject_id_text.toPlainText()
        
        self.metadata_filename = \
            self.view_finder.save_dir_textbox.toPlainText() + \
            '/' + f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_metadata.json"
        
        
    def display_frame(self, image_data: np.array) -> None:
        
        try:
            # Display the image on the GUI
            self.video_feed.setImage(image_data.T)
            # Display the GPIO data on the image
            self.get_GPIO_data()
            self.draw_GPIO_overlay()
            # # Recording status overlay
            self.draw_status_overlay()
            
        except Exception as e:
            print(f"Error displaying image: {e}")
    def draw_status_overlay(self):
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
        ALLIGNMENT = Qt.AlignmentFlag.AlignTop
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

    def recording_loop(self):
        '''Function Called by the parent class every FPS (as defined in parent class)'''
        # Fetch the image data
        self.fetch_image_data()
        # Displaying on GUI

    def refresh(self):
        # update the labels of the camera dropdown
        self.update_camera_dropdown()
        pass

    def refresh_display(self):
        '''Function to refresh the display. Called by the parent class'''
        self.fetch_image_data()
        self.display_frame(self.image_data)
        
    def _init_ffmpeg_process(self) -> None:
        self.get_mp4_filename()
        self.get_gpio_filename()
        print(f'GPIO file: {self.GPIO_filename}' + '\n'
            f'MP4 file: {self.recording_filename}')  

        # Calculate downsampled width and height
        downsampled_width = int(self.resolution_width / self.downsampling_factor)
        downsampled_height = int(self.resolution_height / self.downsampling_factor)
        
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
                pix_fmt=self.pixel_format, 
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
        if self.camera_object == None:
            return None
        try:
            self.GPIO_data = self.camera_object.get_GPIO_data().values()
            # convert list of booleans to list of ints
            self.GPIO_data = [int(x) for x in self.GPIO_data]

        except PySpin.SpinnakerException as ex:
            print(f"Error: {ex}")
            return None
        
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
        self.text_field_update()
        
    def text_field_update(self):
        '''Change the colour of the subject ID text field'''
        if self.subject_id_text.toPlainText() == '':
            self.start_recording_button.setEnabled(False)
        else:
            self.start_recording_button.setEnabled(True)

    def start_recording(self):
        '''Start recording the video'''
        # Get the filenames
        self.get_mp4_filename()
        self.get_gpio_filename()
        self.get_metadata_filename()
        
        # Initalise ffmpeg process
        print('Starting recording')
        self._init_ffmpeg_process()   
        self.recording = True
        self.recorded_frames = 0
        
        self.create_metadata_file()
        # update label
        
        self.stop_recording_button.setEnabled(True)
        self.camera_dropdown.setEnabled(False)
        self.downsampling_factor_label.setEnabled(False)
        self.start_recording_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        # Tabs can't be changed
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(False)
        
    def stop_recording(self):
        
        self.recording = False  
        self.close_metadata_file()
        
        # Set other buttons to now be enabledf
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        self.camera_dropdown.setEnabled(True)
        self.downsampling_factor_label.setEnabled(True)
        # Tabs can be changed
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(True)
        
        self.logger.info('Recording Stopped')
        
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()
        
    def change_camera(self):
        'Function to change which camera is being viewed'
        self.logger.info('Changing camera')
        # shut down old camera
        if self.camera_object != None:
            self.camera_object.end_recording()
        # Get the new camera ID
        new_camera_label = str(self.camera_dropdown.currentText())
        print('new_camera_label', new_camera_label)
        # from the setups tab, get the unique id of the camera
        camera_unique_id = self.setups_tab.get_camera_unique_id_from_label(
            new_camera_label
            )
        # Get the new camera object 
        print(f'Changing camera to: {camera_unique_id}')
        
        self._change_camera(camera_unique_id, new_camera_label)

    def _change_camera(self, new_unique_id, new_camera_label):
        print('unique_id', new_unique_id)
        # Set the new camera object
        self.camera_object = init_camera(new_unique_id)
        # Set the new camera name
        self.unique_id = new_unique_id
        self.label = new_camera_label
        # Call the display function once
        self.camera_object.begin_capturing()
        self.fetch_image_data()
        self.display_frame(self.image_data)
        #  Update the list cameras that are currently being used. 

        self.camera_setup_groupbox.setTitle(self.label)

        
    def change_downsampling_factor(self):
        '''Change the downsampling factor of the camera'''
        self.logger.info('Changing downsampling factor')
        # Get the new downsampling factor
        downsampling_factor = int(self.downsampling_factor_text.currentText())
        # Set the new downsampling factor
        self.downsampling_factor = downsampling_factor
        
    def get_camera_config(self):
        '''Get the camera configuration'''
        return CameraSetupConfig(
            label = self.label,
            downsample_factor = self.downsampling_factor,
            subject_id = self.subject_id
        )
            
    def set_camera_config(self, camera_config: CameraSetupConfig):
        '''Set the camera configuration'''
        # Check if the camera label is in the database
        if camera_config.label not in self.setups_tab.get_camera_labels():
            self.logger.error(f'Camera label {camera_config.label} not found in database')
            return
        
        self.label = camera_config.label
        self.downsampling_factor = camera_config.downsample_factor
        self.unique_id = self.setups_tab.get_camera_unique_id_from_label(self.label)
        self.subject_id = camera_config.subject_id
        self._change_camera(new_unique_id = self.unique_id, new_camera_label = self.label)
        self.logger.info(f'Camera configuration set to: {camera_config}')

    def rename(self, new_label):
        '''Function to rename the camera'''
        # remove the current label from the camera_dropdown widget
        # self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        self.camera_dropdown.removeItem(self.camera_dropdown.findText(self.label))

        self.label = new_label
        self.camera_dropdown.setCurrentText(new_label)        
        self.camera_setup_groupbox.setTitle(new_label)

        
    def disconnect(self):
        # deinit the camera from recording
        self.camera_object.end_recording()
       

    def on_destroyed(self):
        'Function that is called when the camera widget is being closed by the "self.deleteLater() method'
        self.logger.info('Camera Widget Destroyed')
        print('Camera Widget Destroyed')
        # deinit the camera
        self.camera_object.end_recording()