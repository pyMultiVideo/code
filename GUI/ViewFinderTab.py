import json, os, logging
from typing import List
import numpy as np
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
    QSpinBox,
    QLabel
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

from dataclasses import dataclass, asdict
from api.data_classes import CameraConfig, ExperimentConfig
from tools.load_camera import load_saved_setups, init_camera, get_unique_ids
from GUI.CameraWidget import CameraWidget

import db as database

# TODO: Implement the  load_saved_steups from the database... thinking about new and old setups, renaming unique id. can the camearconfig datastruct be passed deeper into the function to reduce the number of arguments being sent through the functions
# also 


class ViewFinder_Tab(QWidget):
    '''Widget for the for viewing the camera feed live'''
    def __init__(self, parent=None):
        super(ViewFinder_Tab, self).__init__(parent)
        self.GUI = parent
        self.logging = logging.getLogger(__name__)
        # self.default_config_path = 'experiments/default_config.json'

        self.connected_cameras: list[str] = get_unique_ids() # list of unique camera as ids
        self.camera_database= load_saved_setups(database) # list of camera_configs

        self._init_header_groupbox()
        self._init_viewfinder_groupbox()
        self._page_layout()
        self._init_timers()
        
        
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
        # set default encoder
        self.encoder_selection.setCurrentText('h264_nvenc')
        self.encoder = self.encoder_selection.currentText()
        self.encoder_selection.currentIndexChanged.connect(self.change_encoder)
        self._set_aquire_layout()
                
    def _set_aquire_layout(self):
        
        self.aquire_hlayout = QHBoxLayout()
        self.aquire_hlayout.addWidget(self.encoder_selection)
        self.encoder_settings_group_box.setLayout(self.aquire_hlayout)
        
    def _init_config_groupbox(self):
        
        self.config_groupbox = QGroupBox("Camera Configuration")
        
        # Text box for displaying the number of camera
        self.camera_config_textbox_label = QLabel('Cameras:')
        
        self.camera_config_textbox = QSpinBox()
        self.camera_config_textbox.setFont(QFont('Courier', 12))
        self.camera_config_textbox.setReadOnly(False)
        maxCameras = len(self.GUI.setups_tab.setups.keys())
        self.camera_config_textbox.setRange(1,maxCameras)
        self.camera_config_textbox.setSingleStep(1) 
        self.camera_config_textbox.valueChanged.connect(self.change_camera_config)
        self.camera_config_textbox.setValue(1)
    
        # 
        self.save_camera_config_button = QPushButton('Save Layout')
        self.save_camera_config_button.setIcon(QIcon('assets/icons/save.svg'))
        self.save_camera_config_button.setFixedHeight(30)
        self.save_camera_config_button.clicked.connect(self.save_experiment_config)
        
        # Button for loading camera configuration
        self.load_camera_config_button = QPushButton('Load Layout')
        # self.load_camera_config_button.setFixedWidth(30)
        self.load_camera_config_button.setFixedHeight(30)
        self.load_camera_config_button.clicked.connect(self.load_experiment_config)
        self._set_config_layout()
        
    def _set_config_layout(self):
        
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_camera_config_button)
        self.config_hlayout.addWidget(self.load_camera_config_button)
        self.config_hlayout.addWidget(self.camera_config_textbox_label)
        self.config_hlayout.addWidget(self.camera_config_textbox)
        self.config_groupbox.setLayout(self.config_hlayout)
        
        
    def _init_save_dir_groupbox(self):
        
        self.save_dir_groupbox = QGroupBox("Save Directory")
        
        # Buttons for saving and loading camera configurations
        self.save_dir_button = QPushButton('')
        self.save_dir_button.setIcon(QIcon('assets/icons/folder.svg'))
        self.save_dir_button.setFixedWidth(30)
        self.save_dir_button.setFixedHeight(30)
        self.save_dir_button.clicked.connect(
            self.get_save_dir
        )
                
        # Display the save directory
        self.save_dir_textbox = QPlainTextEdit()
        self.save_dir_textbox.setMaximumBlockCount(1)
        self.save_dir_textbox.setFont(QFont('Courier', 12))
        self.save_dir_textbox.setReadOnly(True)
        
        self.save_dir_textbox.setPlainText(database.this.paths['data_dir']) 
    
        self._set_save_dir_layout()
        
    def _set_save_dir_layout(self):
            
        self.save_dir_hlayout = QHBoxLayout()
        self.save_dir_hlayout.addWidget(self.save_dir_textbox)
        self.save_dir_hlayout.addWidget(self.save_dir_button)
        self.save_dir_groupbox.setLayout(self.save_dir_hlayout)
    
    def _init_control_all_groupbox(self):
            
        self.control_all_groupbox = QGroupBox("Control All")
            
        
        # Button for recording video 
        self.start_recording_button = QPushButton('')
        self.start_recording_button.setIcon(QIcon('assets/icons/record.svg'))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.clicked.connect(self.start_recording)
        
        # Button for stopping recording
        self.stop_recording_button = QPushButton('')
        self.stop_recording_button.setIcon(QIcon('assets/icons/stop.svg'))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        
        self._set_control_all_layout()
        
    def _set_control_all_layout(self):
        
        self.control_all_hlayout = QHBoxLayout()
        self.control_all_hlayout.addWidget(self.start_recording_button)
        self.control_all_hlayout.addWidget(self.stop_recording_button)
        self.control_all_groupbox.setLayout(self.control_all_hlayout)
    
    def _init_timers(self):
        '''Initialise the timers for the viewfinder tab'''
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self.update_display)
        self.display_update_timer.start(int(1000 / 30))  # 30 fps
        
        self.recording_update_timer = QTimer()
        self.recording_update_timer.timeout.connect(self.encode_buffer)
        self.recording_update_timer.start(int(1000 / 30))
        
    def update_display(self):
        for camera in self.camera_groupboxes:
            camera.fetch_image_data()
            camera.display_frame(camera.image_data)
    
    def encode_buffer(self):
        for camera in self.camera_groupboxes:
            camera.fetch_image_data()
    
    def _init_viewfinder_groupbox(self):
    
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        
        self.camera_groupboxes: List[CameraWidget] = []
        for camera_index in range(1): # One camera by default
            self.camera_groupboxes.append(
                    CameraWidget(
                        parent = self,
                        unique_id = self.connected_cameras[camera_index]                  
                                )
                        )
            self.logging.info('Camera {} added to viewfinder'.format(camera_index))
                                
        # add to layout in a grid
            # Add to the list of camera groupboxes
        self.camera_layout = QGridLayout()
        for i, camera in enumerate(self.camera_groupboxes):
            self.camera_layout.addWidget(camera, i//2, i%2)
        
        self.viewfinder_groupbox.setLayout(self.camera_layout)

    def _remove_camera_groupboxes(self):
        '''Remove the camera groupboxes'''
        for camera in self.camera_groupboxes:
            camera.deleteLater()
        
        self.camera_groupboxes = []

    def change_encoder(self):
        'Function to change the encoder'
        encoder = self.encoder_selection.currentText()
        self.logging.info('Encoder changed to {}'.format(encoder))
        
    ### Functions
            
    def get_page_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            data_dir = self.save_dir_textbox.toPlainText(),
            encoder = self.encoder_selection.currentText(),
            num_cameras = self.camera_config_textbox.value(),
            cameras = [camera.get_camera_config() for camera in self.camera_groupboxes]
        )
    
    def save_experiment_config(self):
        '''Save the camera configuration to a json file'''
        # Open folder selection dialog for which file to save to 
        file_path = QFileDialog.getSaveFileName(self, 'Save File', 'experiments', 'JSON Files (*.json)')
        # save the experiment to a json file

        with open(file_path[0], 'w') as config_file:
            config_file.write(json.dumps(asdict(self.get_page_config()), indent=4))
        
    def load_experiment_config(self):
        '''Function to load a camera configuration from a json file'''
        # deinitialise all cameras that are currently running
        self.disconnect()
        file_path = QFileDialog.getOpenFileName(self, 'Open File', 'experiments', 'JSON Files (*.json)')
        with open(file_path, 'r') as config_file:
            experiment_config = ExperimentConfig(**json.load(config_file))
        self.set_experiment_config(experiment_config)

    def set_experiment_config(self, experiment_config: ExperimentConfig):
        '''Function to set the experiment configuration'''
        self.save_dir_textbox.setPlainText(experiment_config.data_dir)
        self.encoder_selection.setCurrentText(experiment_config.encoder)
        self.camera_config_textbox.setValue(experiment_config.num_cameras)
        
        for box, setup_config_dict in zip(self.camera_groupboxes, experiment_config.cameras):
            # Note: all the cameras have already been disconnected
            box.set_camera_config(setup_config_dict)
        
  
    def _update_available_camera_ids(self):
        for camera_widget in self.camera_groupboxes:
            camera_widget.refresh_camera_widget()
        
    ## Get Attributes    
    
    def get_save_dir(self):
        '''Return the save directory'''
        save_directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        self.save_dir_textbox.setPlainText(save_directory)
        
    def get_available_camera_ids(self):
        '''Return a list of camera ids that are have not yet been used for recording.
        This function must be called every time a camera is added or removed from the list of cameras'''
        self.available_cameras = self.connected_cameras.copy()
        for camera_widget in self.camera_groupboxes:
            # Get the unique id of the camera widget
            camera_widget_unique_id = camera_widget.unique_id
            for camera_config in self.available_cameras:
                if camera_config == camera_widget_unique_id:
                    self.available_cameras.remove(camera_config)
                    
        return self.available_cameras
    
    def get_camera_id(self, unique_id):
        '''Return the unique id of a camera given its name from the saved setups int he viewfinder tab'''
        for camera in self.camera_database:
            if camera.unique_id == unique_id:
                output =  camera.name
            else: 
                output = unique_id 
        return output       
    
    ##
     
    def get_useable_cameras(self) -> list[str]:
        '''Function to get a list of the useable cameras'''
        # Get the list of cameras that are currently active
        active_camera_list = []
        for connected_camera in self.GUI.setups_tab.setups.keys():
            for camera_groupbox in self.camera_groupboxes:
                if camera_groupbox.unique_id == connected_camera:
                    active_camera_list.append(connected_camera)
        return sorted(list(set(self.GUI.setups_tab.setups.keys()) - set(active_camera_list)))
     
    def change_camera_config(self):
        '''
        Function to change the number of camera groupboxes being displayed in the viewfinder tab
        '''
        # Get the number of cameras that are currently being displayed
        current_num_cameras = len(self.camera_groupboxes)
        # Get the number of cameras that the user wants to display
        new_num_cameras = self.camera_config_textbox.value()
        # Get useable cameras
        useable_cameras = self.get_useable_cameras()
        if current_num_cameras < new_num_cameras:
            # Add cameras
            for i in range(new_num_cameras - current_num_cameras):
                self.camera_groupboxes.append(
                    CameraWidget(
                        parent = self,
                        unique_id = useable_cameras[i]
                    )
                )
                
            # Display the new cameras
            self.camera_layout.addWidget(self.camera_groupboxes[-1], 
                                         new_num_cameras%2, 
                                         new_num_cameras//2)
            
        elif current_num_cameras > new_num_cameras:
            # Remove cameras
            for i in range(current_num_cameras - new_num_cameras):
                self.camera_groupboxes[-1].deleteLater()
                box = self.camera_groupboxes.pop()
                box.disconnect()
        pass
    ## Global Controls 
    
    def check_to_enable_global_start_recording(self):
        '''Check if all the cameras are ready to start recording. If any camera is not ready to start, 
        disable the global start recording button'''
        for camera in self.camera_groupboxes:
            # If any camera is not ready to start recording, turn off the global start recording button
            if camera.start_recording_button.isEnabled() == False:
                self.start_recording_button.setEnabled(False)
            else:
                self.start_recording_button.setEnabled(True)
    
    def check_to_enable_global_stop_recording(self):
        '''Check if any camera is recording. If so enable the stop recording button'''
        for camera in self.camera_groupboxes:
            if camera.recording == True:
                self.stop_recording_button.setEnabled(True)
                break
       
    def disconnect(self):
        '''Disconnect all cameras'''
        for camera in self.camera_groupboxes:
            camera.disconnect()
    
    def start_recording(self):
        for camera in self.camera_groupboxes:
            camera.start_recording()
    
    def stop_recording(self):
        for camera in self.camera_groupboxes:
            camera.stop_recording()
