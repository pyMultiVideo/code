import time
import json
import logging
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
    QSpinBox,
    QLabel,
    QCheckBox
    )
from PyQt6.QtGui import (
    QFont,
    QIcon
    
    )
from PyQt6.QtCore import (
    QTimer
)

from dataclasses import asdict
from tools.data_classes import ExperimentConfig, CameraSetupConfig
from tools.load_camera import load_saved_setups
from GUI.ViewfinderWidget import ViewfinderWidget
from GUI.CameraSetupTab import CamerasTab
from GUI.dialogs import show_info_message
import db as database


class VideoCaptureTab(QWidget):
    '''Tab used to display the viewfinder and control the cameras'''
    def __init__(self, parent=None):
        super(VideoCaptureTab, self).__init__(parent)
        self.GUI = parent
        self.camera_setup_tab: CamerasTab = self.GUI.camera_setup_tab
        self.logging = logging.getLogger(__name__)
        self.camera_groupboxes: List[ViewfinderWidget] = []
        self.camera_database = load_saved_setups(database) # list of camera_configs
        self._init_header_groupbox()
        self._init_viewfinder_groupbox()
        # self._init_visibility_control_groupbox()
        self._page_layout()
        self._init_timers()
        print('Viewfinder tab initialised')
        
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
        self.encoder_selection.setCurrentIndex(0)
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
        maxCameras = len(self.camera_setup_tab.setups.keys())
        self.camera_quantity_spin_box.setRange(1,maxCameras)
        self.camera_quantity_spin_box.setSingleStep(1) 
        self.camera_quantity_spin_box.valueChanged.connect(self.spinbox_add_remove_cameras)
        self.camera_quantity_spin_box.setValue(1)
        # 
        self.save_camera_config_button = QPushButton('Save Layout')
        self.save_camera_config_button.setIcon(QIcon('assets/icons/save.svg'))
        self.save_camera_config_button.setFixedHeight(30)
        self.save_camera_config_button.clicked.connect(self.save_experiment_config)
        
        # Button for loading camera configuration
        self.load_experiment_config_button = QPushButton('Load Layout')
        self.load_experiment_config_button.setFixedHeight(30)
        self.load_experiment_config_button.clicked.connect(self.load_experiment_config)
        
        # Check box for changing the layout of the camera widgets
        self.layout_checkbox = QCheckBox('Grid Layout')
        self.layout_checkbox.stateChanged.connect(self.change_layout)
        self.layout_checkbox.setChecked(True)
        # This feature does not work. disable the checkbox
        self.layout_checkbox.setEnabled(False)
        
        self._set_config_layout()
        
    def _set_config_layout(self):
        
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_camera_config_button)
        self.config_hlayout.addWidget(self.load_experiment_config_button)
        self.config_hlayout.addWidget(self.camera_config_textbox_label)
        self.config_hlayout.addWidget(self.camera_quantity_spin_box)
        self.config_hlayout.addWidget(self.layout_checkbox)
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
    
### Visibility Controls 
    
    def toggle_control_header_visibilty(self):
        '''Toggle the visibility of the control groupbox'''
        is_visible = self.header_groupbox.isVisible()
        self.header_groupbox.setVisible(not is_visible)
        
    def toggle_all_viewfinder_control_visiblity(self):
        '''Function that toggles the visibility of all the camera control widgets'''
        for camera in self.camera_groupboxes:
            camera.toggle_control_visibility()

### Timer Functions
    
    def _init_timers(self):
        '''Initialise the timers for the viewfinder tab'''
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self.update_display)
        self.display_update_timer.start(int(1000 / 30))  # 30 fps
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(1000)
        
    def update_display(self):
        '''
        Function that calls the required functions to collect, encode and display the images from the camera. 
        '''
        TESTING = False
        if TESTING is True:
            for camera in self.camera_groupboxes:
                # check if the camera is in the performance_table as a column
                if camera.unique_id not in self.GUI.performance_table.columns:
                    self.GUI.performance_table[camera.unique_id] = []
        
        for camera in self.camera_groupboxes:
            if TESTING is True:
                start_time = time.time()
            camera.fetch_image_data()
            camera.display_frame(camera._image_data)
            camera.update_gpio_overlay()
            if TESTING is True:
                end_time = time.time()
                # Append the time taken to the performance table
                self.GUI.performance_table.loc[time.time(), camera.unique_id] = end_time - start_time
    
    def _init_viewfinder_groupbox(self):

        self.camera_layout = QGridLayout()
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        self.viewfinder_groupbox.setLayout(self.camera_layout)

        if self.GUI.startup_config is None:         
            useable_cameras = sorted(list(set(self.connected_cameras()) - set(self.camera_groupbox_labels())), key=str.lower)
            print('useable_cameras - init', useable_cameras)
            for camera_label in useable_cameras[:1]: # One camera by default
                self.initialize_camera_widget(
                    label=camera_label,
                    )
        else:
            # Load the default config file
            with open(self.GUI.startup_config, 'r') as config_file:
                config_data = json.load(config_file)
                config_data['cameras'] = [CameraSetupConfig(**camera) for camera in config_data['cameras']]
            experiment_config = ExperimentConfig(**config_data)
            
            self.load_from_config_dir(experiment_config)
            
    def spinbox_add_remove_cameras(self):
        '''
        Function attached to the spinbox that adds or removes cameras from the viewfinder tab
        '''
        # Get the set of useable cameras
        useable_cameras = sorted(list(set(self.connected_cameras()) - set(self.camera_groupbox_labels())), key=str.lower)
        print('useable_cameras', useable_cameras)
        
        # value of spinbox
        if self.camera_quantity_spin_box.value() > len(self.camera_groupboxes): # If the number of cameras is being reduced
            label = useable_cameras[0]
            self.initialize_camera_widget(
                label=label,
                )
        
        elif self.camera_quantity_spin_box.value() <= len(self.camera_groupboxes):
            for i in range(len(self.camera_groupboxes) - self.camera_quantity_spin_box.value()):
                camera = self.camera_groupboxes.pop()
                camera.disconnect()
                
        self.refresh()

    def initialize_camera_widget(
            self, 
            label,
            subject_id=None
            ):
        '''Create a new camera widget and add it to the viewfinder tab'''
        self.camera_groupboxes.append(
                ViewfinderWidget(
                    parent      = self,
                    label       = label,
                    subject_id  = subject_id,
                )
            )
        self.add_widget_to_layout()
    
    def add_widget_to_layout(self):
        '''Add the camera widget to the layout'''
        
        position = len(self.camera_groupboxes) - 1
        self.camera_layout.addWidget(
            self.camera_groupboxes[-1], 
            position%2,
            position//2
        )       
        self.refresh()
    
    def change_layout(self):
        '''Function to change the layout of the camera widgets'''
        pass
    
    def change_encoder(self):
        'Function to change the encoder'
        self.encoder = self.encoder_selection.currentText()
        self.logging.info('Encoder changed to {}'.format(self.encoder))
    
    ### Functions
            
    def get_page_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            data_dir    = self.save_dir_textbox.toPlainText(),
            encoder     = self.encoder_selection.currentText(),
            num_cameras = self.camera_quantity_spin_box.value(),
            grid_layout = self.layout_checkbox.isChecked(),
            cameras     = [camera.get_camera_config() for camera in self.camera_groupboxes]
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
        # Check if the config file is valid
        self.check_valid_config(experiment_config)
        # Load the camera configuration
        self.load_from_config_dir(experiment_config)

    def check_valid_config(self, experiment_config: ExperimentConfig):
        '''
        Function to hold the logic for checking if the config file is valid
        '''
        # Check if config file contains cameras that are in the database
        for camera in experiment_config.cameras:
            if camera.label not in self.camera_setup_tab.get_setups_labels():
                show_info_message(f'Camera {camera.label} is not connected')
                return


    def load_from_config_dir(self, experiment_config: ExperimentConfig):
        '''
        Load the camera configuration from the experiment config dataclass
        '''
        
        # Remove all the cameras that are currently being displayed
        for i in range(len(self.camera_groupboxes)):
            camera = self.camera_groupboxes.pop()
            camera.disconnect()
            
        # Initialise the cameras from the config file
        for camera in experiment_config.cameras:
            self.initialize_camera_widget(
                label=camera.label, 
                subject_id=camera.subject_id
                )
        # Set the values of the spinbox and encoder selection based on config file
        self.camera_quantity_spin_box.setValue(experiment_config.num_cameras)
        self.encoder_selection.setCurrentText(experiment_config.encoder)
        self.save_dir_textbox.setPlainText(experiment_config.data_dir)
        self.layout_checkbox.setChecked(experiment_config.grid_layout)


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
        if self.camera_setup_tab.setups_changed:
            self.camera_setup_tab.setups_changed = False
            # Handle the renamed cameras
            self.handle_camera_setups_modified()
                    
    def handle_camera_setups_modified(self):
        '''
        Handle the renamed cameras by renaming the relevent attributes of the camera groupboxes
        
        TODO: Add the ability to change the camera settings of a CameraWidget (i.e. fps, pxl_fmt).
        This requires changing the display of these attributes further to changing how the camera is actually recording.         
        '''
        for label in self.connected_cameras(): # New list of camera labels
            # if the label not in the initialised list of cameras (either new or not initialised)
            if label not in self.camera_groupbox_labels():
                # get the unique id of the camera of the queried label
                unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(label)
                # if the unique id is not in the list of camera groupboxes is it a uninitialized camera
                if unique_id in [camera.unique_id for camera in self.camera_groupboxes]:
                    print('camera unique id', [camera.unique_id for camera in self.camera_groupboxes], 'queried unique id', unique_id)
                    camera_widget = [camera for camera in self.camera_groupboxes if camera.unique_id == unique_id][0]
                    # Rename the camera with the queried label
                    camera_widget.rename(new_label = label)
                else:
                    # Camera is uninitialized
                    continue
            else:
                # Camera hasn't been renamed
                continue
        
        
    def get_save_dir(self):
        '''Return the save directory'''
        save_directory = QFileDialog.getExistingDirectory(self, 'Select Directory')
        self.save_dir_textbox.setPlainText(save_directory)

    def camera_groupbox_labels(self) -> List[str]:
        '''Return the labels of the camera groupboxes'''
        return [camera.label for camera in self.camera_groupboxes]

    def connected_cameras(self) -> List[str]:
        '''Return the labels of cameras connected to the PC'''
        return self.camera_setup_tab.get_setups_labels()

    def check_to_enable_global_start_recording(self):
        '''Check if all the cameras are ready to start recording. If any camera is not ready to start, 
        disable the global start recording button'''
        for camera in self.camera_groupboxes:
            # If any camera is not ready to start recording, turn off the global start recording button
            if camera.start_recording_button.isEnabled() is False:
                self.start_recording_button.setEnabled(False)
            else:
                self.start_recording_button.setEnabled(True)
    
    def check_to_enable_global_stop_recording(self):
        '''Check if any camera is recording. If so enable the stop recording button'''
        for camera in self.camera_groupboxes:
            if camera.recording is True:
                self.stop_recording_button.setEnabled(True)
            else:
                self.stop_recording_button.setEnabled(False)

    def disconnect(self):
        '''Disconnect all cameras'''
        print('disconnecting the following cameras', [cam.unique_id for cam in self.camera_groupboxes])
        while self.camera_groupboxes:
            camera = self.camera_groupboxes.pop()
            camera.disconnect()


    def start_recording(self):
        for camera in self.camera_groupboxes:
            camera.start_recording()
    
    def stop_recording(self):
        for camera in self.camera_groupboxes:
            camera.stop_recording()
