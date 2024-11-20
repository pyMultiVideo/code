from time import sleep
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
from api.data_classes import ExperimentConfig, CameraSetupConfig
from tools.load_camera import load_saved_setups, init_camera, get_unique_ids
from GUI.CameraWidget import CameraWidget
import db as database
from dialogues.error_message import show_info_message

# TODO: Implement the  load_saved_steups from the database... thinking about new and old setups, renaming unique id. can the camearconfig datastruct be passed deeper into the function to reduce the number of arguments being sent through the functions
# also 


class ViewFinderTab(QWidget):
    '''Widget for the for viewing the camera feed live'''
    def __init__(self, parent=None):
        super(ViewFinderTab, self).__init__(parent)
        self.GUI = parent
        self.logging = logging.getLogger(__name__)
        # self.default_config_path = 'experiments/default_config.json'

        self.camera_groupboxes: List[CameraWidget] = []
        self.connected_cameras: list[str] = self.GUI.setups_tab.get_setups_labels()
        self.camera_database= load_saved_setups(database) # list of camera_configs

        self._init_header_groupbox()
        self._init_viewfinder_groupbox()
        self._page_layout()
        self._init_timers()
        

        
        # List of camera groupbox names that are currently being displayed

        
    def _init_header_groupbox(self):
        # Initialise the configuration widget
        self.header_groupbox = QGroupBox()
        self.header_groupbox.setMaximumHeight(100)
        
        self._init_aquire_groupbox()
        self._init_config_groupbox()
        self._init_save_dir_groupbox()
        self._init_control_all_groupbox()
        
        
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
        'List of encoders that are available'
        self.encoder_settings_group_box = QGroupBox("FFMPEG Settings")
        # dropdown for camera selection
        self.encoder_selection = QComboBox()
        self.encoder_selection.addItems(database.this.encoder_dict['ffmpeg']) # replace with camera names
        self.encoder_selection.setCurrentText('h264_nvenc')
        self.encoder = self.encoder_selection.currentText()
        self.encoder_selection.currentIndexChanged.connect(self.change_encoder)
        self._set_aquire_layout()
                
    def _set_aquire_layout(self):
        
        self.aquire_hlayout = QHBoxLayout()
        self.aquire_hlayout.addWidget(self.encoder_selection)
        self.encoder_settings_group_box.setLayout(self.aquire_hlayout)
        
    def _init_config_groupbox(self):
        
        self.config_groupbox = QGroupBox("Experiment Configuration")
        
        # Text box for displaying the number of camera
        self.camera_config_textbox_label = QLabel('Cameras:')
        
        self.camera_quantity_spin_box = QSpinBox()
        self.camera_quantity_spin_box.setFont(QFont('Courier', 12))
        self.camera_quantity_spin_box.setReadOnly(False)
        maxCameras = len(self.GUI.setups_tab.setups.keys())
        self.camera_quantity_spin_box.setRange(1,maxCameras)
        self.camera_quantity_spin_box.setSingleStep(1) 
        self.camera_quantity_spin_box.valueChanged.connect(self.change_camera_config)
        self.camera_quantity_spin_box.setValue(1)
    
        # 
        self.save_camera_config_button = QPushButton('Save Layout')
        self.save_camera_config_button.setIcon(QIcon('assets/icons/save.svg'))
        self.save_camera_config_button.setFixedHeight(30)
        self.save_camera_config_button.clicked.connect(self.save_experiment_config)
        
        # Button for loading camera configuration
        self.load_experiment_config_button = QPushButton('Load Layout')
        # self.load_camera_config_button.setFixedWidth(30)
        self.load_experiment_config_button.setFixedHeight(30)
        self.load_experiment_config_button.clicked.connect(self.load_experiment_config)
        self._set_config_layout()
        
    def _set_config_layout(self):
        
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_camera_config_button)
        self.config_hlayout.addWidget(self.load_experiment_config_button)
        self.config_hlayout.addWidget(self.camera_config_textbox_label)
        self.config_hlayout.addWidget(self.camera_quantity_spin_box)
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
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(1000)
        
    def update_display(self):
        for camera in self.camera_groupboxes:
            camera.fetch_image_data()
            camera.display_frame(camera.image_data)
    
    def encode_buffer(self):
        for camera in self.camera_groupboxes:
            camera.fetch_image_data()
    
    def _init_viewfinder_groupbox(self):

        self.camera_layout = QGridLayout()
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        self.viewfinder_groupbox.setLayout(self.camera_layout)
        

        useable_cameras = sorted(list(set(self.connected_cameras) - set(self.camera_groupbox_labels())), key=str.lower)
        print('useable_cameras - init', useable_cameras)
        for camera_index, camera_label in enumerate(useable_cameras[:1]): # One camera by default
            self.initialize_camera_widget(label=camera_label)

        
    def change_camera_config(self):
        '''
        Function to change the number of camera groupboxes being displayed in the viewfinder tab
        '''
        # Get the set of useable cameras
        useable_cameras = sorted(list(set(self.connected_cameras) - set(self.camera_groupbox_labels())), key=str.lower)
        print('useable_cameras', useable_cameras)
        
        # value of spinbox

        if self.camera_quantity_spin_box.value() > len(self.camera_groupboxes): # If the number of cameras is being reduced
            label = useable_cameras[0]
            self.initialize_camera_widget(label=label)
        
        elif self.camera_quantity_spin_box.value() <= len(self.camera_groupboxes):
            for i in range(len(self.camera_groupboxes) - self.camera_quantity_spin_box.value()):
                self.camera_groupboxes[-1].disconnect()

        self.refresh()

    def initialize_camera_widget(self, label, subject_id=None):
        '''Create a new camera widget and add it to the viewfinder tab'''
        self.camera_groupboxes.append(
                CameraWidget(
                    parent = self,
                    label = label,
                    subject_id = subject_id
                )
            )
        position = len(self.camera_groupboxes) - 1
        self.camera_layout.addWidget(
                self.camera_groupboxes[-1], 
                position%2, 
                position//2
            )


    def change_encoder(self):
        'Function to change the encoder'
        encoder = self.encoder_selection.currentText()
        self.logging.info('Encoder changed to {}'.format(encoder))
        
    ### Functions
            
    def get_page_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            data_dir = self.save_dir_textbox.toPlainText(),
            encoder = self.encoder_selection.currentText(),
            num_cameras = self.camera_quantity_spin_box.value(),
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
        file_tuple = QFileDialog.getOpenFileName(self, 'Open File', 'experiments', 'JSON Files (*.json)')
        with open(file_tuple[0], 'r') as config_file:
            config_data = json.load(config_file)
            config_data['cameras'] = [CameraSetupConfig(**camera) for camera in config_data['cameras']]
        experiment_config = ExperimentConfig(**config_data)
        # Removes all the cameras that are currently being displayed
        
        
        # check if config file contains cameras that are in the database
        for camera in experiment_config.cameras:
            if camera.label not in self.GUI.setups_tab.get_setups_labels():
                show_info_message(f'Camera {camera.label} is not connected')
                return
        self.set_experiment_config(experiment_config)
        

    def set_experiment_config(self, experiment_config: ExperimentConfig):
        '''Function to set the experiment configuration'''
        self.save_dir_textbox.setPlainText(experiment_config.data_dir)
        self.encoder_selection.setCurrentText(experiment_config.encoder)
        self.camera_quantity_spin_box.setValue(experiment_config.num_cameras)

        self.disconnect()
        for camera in experiment_config.cameras:
            self.initialize_camera_widget(label=camera.label, subject_id=camera.subject_id)




    def update_camera_dropdowns(self):
        '''Update the camera dropdowns'''
        for camera in self.camera_groupboxes:
            camera.update_camera_dropdown()
    
    def refresh(self):
        '''Refresh the viewfinder tab'''
        self.check_to_enable_global_start_recording()
        self.check_to_enable_global_stop_recording()
        for camera_label in self.camera_groupboxes:
            camera_label.refresh()
        
        # Check the setups_changed flag
        if self.GUI.setups_tab.setups_changed:
            self.GUI.setups_tab.setups_changed = False
            # Handle the renamed cameras
            self.handle_camera_renamed()
                    
    def handle_camera_renamed(self):
        '''Handle the renamed cameras by renaming the relevent attributes of the camera groupboxes'''
        # Set of new camera labels
        
        old_cameras = self.connected_cameras # is it possible to remove the self.connected cameras list and call the function directly from somewhere else?
        new_cameras = self.GUI.setups_tab.get_setups_labels()


        
        # list of only the old camera labels
        removed_cameras = list(set(old_cameras) - set(new_cameras))
        # list of only the new camera labels
        added_cameras = list(set(new_cameras) - set(old_cameras))
        for cam in removed_cameras:
            if cam in self.camera_groupbox_labels():
                camera_widget = [camera for camera in self.camera_groupboxes if camera.label == cam][0]
                camera_widget.rename(new_label = added_cameras[0])

        self.connected_cameras = new_cameras
        
        
    def get_save_dir(self):
        '''Return the save directory'''
        save_directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        self.save_dir_textbox.setPlainText(save_directory)

    def camera_groupbox_labels(self) -> List[str]:
        '''Return the labels of the camera groupboxes'''
        return [camera.label for camera in self.camera_groupboxes]

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
            else:
                self.stop_recording_button.setEnabled(False)


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
