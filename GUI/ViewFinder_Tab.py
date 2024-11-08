import json, os
from typing import List

from PyQt6.QtWidgets import (
    QVBoxLayout, 
    QGroupBox, 
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QFileDialog,
    QFrame,
    QSpinBox
    
    )
from PyQt6.QtGui import (
    QFont,
    QImage,
    QPixmap,
    QIcon
    
    )
from PyQt6.QtCore import (
    QTimer,
    Qt
)

from dataclasses import dataclass
from api.load_camera import *
from GUI.camera_widget import CameraWidget
from utils.data_classes import CameraConfig, ExperimentConfig
import db as database

    

class ViewFinder_Tab(QWidget):
    'Widget for the for viewing the camera feed live'
    def __init__(self, parent=None):
        super(ViewFinder_Tab, self).__init__(parent)
        self.GUI = parent
        self.logging = logging.getLogger(__name__)
        # self.default_config_path = 'experiments/default_config.json'
        
        self.unique_ids: list  = get_unique_ids() # The camera IDs
        
        self._init_config()
        
        self._init_header_groupbox()
        self._init_viewfinder_groupbox()
        
        self._page_layout()
        
    def _init_config(self):
        'Initialise the configuration'
        
        # Without a config file, a default view will be created
        self._create_default_config()

        self.experiment_config: ExperimentConfig = self.default_config
        # Load the experiment json file into the experiment dataclass
        # self.experiment_config: ExperimentConfig = self.load_experiment_from_file_path(self.default_config_path)
                
    def _create_default_config(self):
        'On startup, create a default config file'
        
        self.default_config = ExperimentConfig(
            data_dir = os.path.join(database.this.paths['ROOT'],'data'),
            encoder = 'h264_nvenc',
            num_cameras = 1,
            cameras = [CameraConfig(
                name = 'Camera 1',
                subject_ID = 'Subject 1',
                width = 1280,
                height = 720,
                bitrate = '2M',
                fps = 30,
                pixel_format = 'yuv420p',
                exposure_time = 10000,
                gain = 5,
                display_update_ps = 30
                )]
            )
        
        
        # Create the default config file
        # ExperimentConfig(
        #     data_dir = 'data',
        #     encoder = 'H264',
        #     num_cameras = len(self.unique_ids),
        #     cameras = [CameraConfig(
        #         name = 'Camera {}'.format(i),
        #         subject_ID = 'Subject {}'.format(i),
        #         width = 1920,
        #         height = 1080,
        #         bitrate = '1000000',
        #         fps = 30,
        #         pixel_format = 'RGB8',
        #         exposure_time = 1000,
        #         gain = 0,
        #         display_update_ps = 30
        #         ) for i in range(len(self.unique_ids))]
        #     )

        
    def _init_header_groupbox(self):
        # Initialise the configuration widget
        self.header_groupbox = QGroupBox()
        self.header_groupbox.setMaximumHeight(100)
        
        self._init_aquire_groupbox()
        self._init_config_groupbox()
        self._init_save_dir_groupbox()
        self._init_control_all_groupbox()
        self._set_header_layout()
        
    def _set_header_layout(self):
        
        
        self.header_hlayout = QHBoxLayout()
        self.header_hlayout.addWidget(self.config_groupbox)
        self.header_hlayout.addWidget(self.encoder_settings_group_box)
        self.header_hlayout.addWidget(self.save_dir_groupbox)
        self.header_hlayout.addWidget(self.control_all_groupbox)
        self.header_groupbox.setLayout(self.header_hlayout)

    def _page_layout(self):        
        self.page_layout = QVBoxLayout()
        
        self.page_layout.addWidget(self.header_groupbox)
        self.page_layout.addWidget(self.viewfinder_groupbox)
        self.setLayout(self.page_layout)

    def _init_aquire_groupbox(self):
        'List of encoders that are available '
        self.encoder_settings_group_box = QGroupBox("Aquisition Settings")
        
        # dropdown for camera selection
        self.encoder_selection = QComboBox()
        self.encoder_selection.addItems(database.this.encoder_dict['ffmpeg']) # replace with camera names
        self.encoder_selection.currentIndexChanged.connect(self.change_encoder)
        self._set_aquire_layout()
        
    def _set_aquire_layout(self):
        
        self.aquire_hlayout = QHBoxLayout()
        self.aquire_hlayout.addWidget(self.encoder_selection)
        self.encoder_settings_group_box.setLayout(self.aquire_hlayout)
        
    def _init_config_groupbox(self):
        
        self.config_groupbox = QGroupBox("Camera Configuration")
        
        # Text box for displaying the number of camera
        self.camera_config_textbox = QSpinBox()
        self.camera_config_textbox.setFont(QFont('Courier', 12))
        self.camera_config_textbox.setReadOnly(False)
        self.camera_config_textbox.setRange(1,9)
        self.camera_config_textbox.setSingleStep(1) 
        self.camera_config_textbox.valueChanged.connect(self.change_camera_config)
        # set text from config file
        self.camera_config_textbox.setValue(self.experiment_config.num_cameras) # replace with data from database file
        
        
        # 
        self.save_camera_config_button = QPushButton('Save Layout')
        self.save_camera_config_button.setIcon(QIcon('assets/icons/save.svg'))
        # self.save_camera_config_button.setFixedWidth(30)
        self.save_camera_config_button.setFixedHeight(30)
        self.save_camera_config_button.clicked.connect(self.save_camera_config)
        
        # Button for loading camera configuration
        self.load_camera_config_button = QPushButton('Load Layout')
        # self.load_camera_config_button.setFixedWidth(30)
        self.load_camera_config_button.setFixedHeight(30)
        self.load_camera_config_button.clicked.connect(self.load_camera_config)
        self._set_config_layout()
        
    def _set_config_layout(self):
        
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_camera_config_button)
        self.config_hlayout.addWidget(self.load_camera_config_button)
        self.config_hlayout.addWidget(self.camera_config_textbox)
        self.config_groupbox.setLayout(self.config_hlayout)
        
        
    def _init_save_dir_groupbox(self):
        
        self.save_dir_groupbox = QGroupBox("Save Directory")
        
        # Buttons for saving and loading camera configurations
        self.save_dir_button = QPushButton('')
        self.save_dir_button.setIcon(QIcon('assets/icons/folder.svg'))
        self.save_dir_button.setFixedWidth(30)
        self.save_dir_button.setFixedHeight(30)
        self.save_dir_button.clicked.connect(self.select_save_name)
                
        # Display the save directory
        self.save_dir_textbox = QPlainTextEdit()
        self.save_dir_textbox.setMaximumBlockCount(1)
        self.save_dir_textbox.setFont(QFont('Courier', 12))
        self.save_dir_textbox.setReadOnly(True)
        
        self.save_dir_textbox.setPlainText('{}'.format(self.experiment_config.data_dir))
    
        self._set_save_dir_layout()
        
    def _set_save_dir_layout(self):
            
        self.save_dir_hlayout = QHBoxLayout()
        self.save_dir_hlayout.addWidget(self.save_dir_textbox)
        self.save_dir_hlayout.addWidget(self.save_dir_button)
        self.save_dir_groupbox.setLayout(self.save_dir_hlayout)
    
    def _init_control_all_groupbox(self):
            
        self.control_all_groupbox = QGroupBox("Control All")
            
        # Button for starting video output
        self.start_playing_video_button = QPushButton('')
        self.start_playing_video_button.setIcon(QIcon('assets/icons/play.svg'))
        self.start_playing_video_button.setFixedWidth(30)
        self.start_playing_video_button.setFixedHeight(30)
        self.start_playing_video_button.clicked.connect(self.start_all_playing_video)
        
        # Button for recording video 
        self.start_recording_button = QPushButton('')
        self.start_recording_button.setIcon(QIcon('assets/icons/record.svg'))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.clicked.connect(self.start_all_recording)
        
        # Button for stopping recording
        self.stop_recording_button = QPushButton('')
        self.stop_recording_button.setIcon(QIcon('assets/icons/stop.svg'))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.clicked.connect(self.stop_all_recording)
        
        self._set_control_all_layout()
        
    def _set_control_all_layout(self):
        
        self.control_all_hlayout = QHBoxLayout()
        self.control_all_hlayout.addWidget(self.start_playing_video_button)
        self.control_all_hlayout.addWidget(self.start_recording_button)
        self.control_all_hlayout.addWidget(self.stop_recording_button)
        self.control_all_groupbox.setLayout(self.control_all_hlayout)
    
    
    def _init_viewfinder_groupbox(self):
    
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        
        self.camera_groupboxes: List[CameraWidget] = []
        
        for camera_index in range(self.experiment_config.num_cameras):
            self.camera_groupboxes.append(
                    CameraWidget(
                                unique_id = self.unique_ids[camera_index][0],
                                api       = self.unique_ids[camera_index][1],  
                                parent    =self, 
                                camera_config    =self.experiment_config.cameras[camera_index]
                                )
                        )
            print('Setting up camera {}'.format(self.unique_ids[camera_index][0]))
            # Add to the list of camera groupboxes
            
        # add to layout in a grid
        self.camera_layout = QGridLayout()
        for i, camera in enumerate(self.camera_groupboxes):
            self.camera_layout.addWidget(camera, i//2, i%2)
        
        self.viewfinder_groupbox.setLayout(self.camera_layout)

    def _de_init_viewfinder_groupbox(self):
        'Remove the camera groupboxes'
        for camera in self.camera_groupboxes:
            camera.deleteLater()
        
        self.camera_groupboxes = []

    def change_encoder(self):
        'Function to change the encoder'
        encoder = self.encoder_selection.currentText()
        self.experiment_config.encoder = encoder
        self.logging.info('Encoder changed to {}'.format(self.experiment_config.encoder))
        
    ### Functions
    
    def change_camera_config(self):
        'Function to change the camera configuration. Note: max change from button click is 1 camera'
        num_cameras = self.camera_config_textbox.value()
        
        if num_cameras >= self.experiment_config.num_cameras:
            print('Adding camera')
            # Add a camera
            self.experiment_config.cameras.append(
                CameraConfig(
                    name = 'Camera {}'.format(num_cameras),
                    subject_ID = 'Subject {}'.format(num_cameras),
                    width = 1920,
                    height = 1080,
                    bitrate = '1000000',
                    fps = 30,
                    pixel_format = 'RGB8',
                    exposure_time = 1000,
                    gain = 0,
                    display_update_ps = 30
                    )
                )
            
            # Add a camera groupbox
            self.camera_groupboxes.append(
                    CameraWidget(
                                unique_id = self.unique_ids[num_cameras-1][0],
                                api       = self.unique_ids[num_cameras-1][1],  
                                parent    = self, 
                                camera_config    =self.experiment_config.cameras[num_cameras-1]
                                )
                        )
            
            # add to layout in a grid
            self.camera_layout.addWidget(
                self.camera_groupboxes[-1], 
                (num_cameras-1)//2, 
                (num_cameras-1)%2
            )
            # update the number of cameras to be the length of the cameras list
            self.experiment_config.num_cameras = len(self.experiment_config.cameras)
            self.camera_config_textbox.setValue(self.experiment_config.num_cameras)
        elif num_cameras <= self.experiment_config.num_cameras:
            print('Removing camera')
            box_config = self.experiment_config.cameras.pop()
            box_object = self.camera_groupboxes.pop()
            # box.set_parent(None)
            box_object.de_init_camera()
            box_object.deleteLater()
            
            # update the number of cameras to be the length of the cameras list
            self.experiment_config.num_cameras = len(self.experiment_config.cameras)
            self.camera_config_textbox.setValue(self.experiment_config.num_cameras)
            
        elif num_cameras == 1: 
            pass
            
        
    def save_camera_config(self):
        'This function will save the camera configuration by writing to a json file that stores the camera configuration, updating it'
        
        self.save_experiment(
            exp = self.experiment_config, 
            filename= self.experiment_dir
            )

    def load_camera_config(self):
        'Function to load a camera configuration from a json file'
        # Get the directory of a json file. Open the /experiments folder by default
        file_path = QFileDialog.getOpenFileName(self, 'Open File', 'experiments', 'JSON Files (*.json)')
        # Get the first element of the tuple
        file_path = file_path[0]
        # Load the camera configuration
        self.experiment_config = self.load_experiment_from_file_path(file_path)

        
        # Remove all the camera groupboxes and deinitilise all their cameras
        for camera_widget in self.camera_groupboxes:
            camera_widget.de_init_camera()
            camera_widget.deleteLater()

        # Remove all the camera groupboxes
        self.camera_groupboxes = []
        
        # Add the new camera groupboxes
        for camera_index in range(self.experiment_config.num_cameras):
            self.camera_groupboxes.append(
                    CameraWidget(
                                unique_id = self.unique_ids[camera_index][0],
                                api       = self.unique_ids[camera_index][1],  
                                parent    =self, 
                                camera_config    =self.experiment_config.cameras[camera_index]
                                )
                        )
            print('Setting up camera {}'.format(self.unique_ids[camera_index][0]))
            # Add to the list of camera groupboxes
            
        for i, camera in enumerate(self.camera_groupboxes):
            self.camera_layout.addWidget(camera, i//2, i%2)
            
        self._update_header_information()
            
        self.logging.info('Camera configuration loaded from {}'.format(file_path))
        
        
        
        pass
    def _update_header_information(self):
        'Function to update the header information'
        
        
        
        pass

    def load_experiment_from_file_path(self, file_path: str) -> ExperimentConfig:
        'Function to load an experiment from a json file'
        with open(file_path) as f:
            experiment_json = json.load(f)
        cameras = []
        for cam in experiment_json['cameras']:
            cameras.append(CameraConfig(**cam))
        return ExperimentConfig(
            data_dir=experiment_json['data_dir'],
            encoder=experiment_json['encoder'],
            num_cameras=experiment_json['num_cameras'],
            cameras=cameras          
                )
    
    def save_experiment(self, experiment_config: ExperimentConfig, file_path:str ) -> None:
        'Function to save an experiment to a json file'
        # save the experiment to a json file
        exp_dict = experiment_config.__dict__
        exp_dict['cameras'] = [cam.__dict__ for cam in exp_dict['cameras']]
        # save with new lines between the keys
        with open(os.path.join(self.experiment_config, file_path), 'w') as f:
            f.write(json.dumps(exp_dict, indent=4))
        
    
    def select_save_name(self):
        # Open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Select Folder", 
            self.experiment_config.data_dir
            )
        # Update the config
        self.experiment_config.data_dir = folder_path        
        # Update the text box
        self.save_dir_textbox.setPlainText(folder_path)
        
    ## Global Controls 
    
    def start_all_playing_video(self):
        for camera in self.camera_groupboxes:
            camera.toggle_playing_video()
    
    def start_all_recording(self):
        for camera in self.camera_groupboxes:
            camera.start_recording()
    
    def stop_all_recording(self):
        for camera in self.camera_groupboxes:
            camera.stop_recording()
    
        