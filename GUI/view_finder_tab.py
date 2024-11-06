import json
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
    QPixmap
    
    )
from PyQt6.QtCore import (
    QTimer,
    Qt
)

import PySpin

from GUI.camera_widget import camera_widget

class viewfinder_tab(QWidget):
    'Widget for the for viewing the camera feed live'
    def __init__(self, parent=None):
        super(viewfinder_tab, self).__init__(parent)
        self.GUI = parent
        
        self._init_timers()
        self._init_header_groupbox()
        self._init_viewfinder_groupbox()
        
        self._page_layout()
        
        
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
        self.header_hlayout.addWidget(self.aquizition_settings_groupbox)
        self.header_hlayout.addWidget(self.save_dir_groupbox)
        self.header_hlayout.addWidget(self.control_all_groupbox)
        self.header_groupbox.setLayout(self.header_hlayout)

    def _page_layout(self):        
        self.page_layout = QVBoxLayout()
        
        self.page_layout.addWidget(self.header_groupbox)
        self.page_layout.addWidget(self.viewfinder_groupbox)
        self.setLayout(self.page_layout)

    def _init_aquire_groupbox(self):

        self.aquizition_settings_groupbox = QGroupBox("Aquisition Settings")
        
        # dropdown for camera selection
        self.camera_selection = QComboBox()
        self.camera_selection.addItems([]) # replace with camera names
        self.camera_selection.currentIndexChanged.connect(self.change_camera_config)
        self._set_aquire_layout()
        
    def _set_aquire_layout(self):
        
        self.aquire_hlayout = QHBoxLayout()
        self.aquire_hlayout.addWidget(self.camera_selection)
        self.aquizition_settings_groupbox.setLayout(self.aquire_hlayout)
        
    def _init_config_groupbox(self):
        
        self.config_groupbox = QGroupBox("Camera Configuration")
        
        # Text box for displaying the number of camera
        self.camera_config_textbox = QSpinBox()
        self.camera_config_textbox.setFont(QFont('Courier', 12))
        self.camera_config_textbox.setReadOnly(False)
        # set text from config file
        self.camera_config_textbox.setValue(self.GUI.recording_config['no_of_cameras'])
        
        self._set_config_layout()
        
    def _set_config_layout(self):
        
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.camera_config_textbox)
        self.config_groupbox.setLayout(self.config_hlayout)
        
        
    def _init_save_dir_groupbox(self):
        
        self.save_dir_groupbox = QGroupBox("Save Directory")
        
        # Buttons for saving and loading camera configurations
        self.save_dir_button = QPushButton('Save Directory')
        self.save_dir_button.clicked.connect(self.select_folder)
        
        # Display the save directory
        self.save_dir_textbox = QPlainTextEdit()
        self.save_dir_textbox.setMaximumBlockCount(1)
        self.save_dir_textbox.setFont(QFont('Courier', 12))
        self.save_dir_textbox.setReadOnly(True)
        
        self.save_dir_textbox.setPlainText('{}'.format(self.GUI.recording_config['save_dir']))
    
        self._set_save_dir_layout()
        
    def _set_save_dir_layout(self):
            
        self.save_dir_hlayout = QHBoxLayout()
        self.save_dir_hlayout.addWidget(self.save_dir_textbox)
        self.save_dir_hlayout.addWidget(self.save_dir_button)
        self.save_dir_groupbox.setLayout(self.save_dir_hlayout)
    
    def _init_control_all_groupbox(self):
            
        self.control_all_groupbox = QGroupBox("Control All")
            
        self.control_all_dropdown = QComboBox()
        self.control_all_dropdown.addItems(['Start', 'Stop', 'Pause', 'Resume'])
        
        self.control_all_button = QPushButton('Control All')
        self.control_all_button.clicked.connect(self.control_all)
        
        self._set_control_all_layout()
        
    def _set_control_all_layout(self):
        
        self.control_all_hlayout = QHBoxLayout()
        self.control_all_hlayout.addWidget(self.control_all_dropdown)
        self.control_all_hlayout.addWidget(self.control_all_button)
        self.control_all_groupbox.setLayout(self.control_all_hlayout)
    
    
    def _init_viewfinder_groupbox(self):
    
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        
        self.camera_groupboxes: List[camera_widget] = []
        
        for camera in range(self.GUI.recording_config['no_of_cameras']):
            self.camera_groupboxes.append(camera_widget(parent=self, camera=self.GUI.cam_list[camera]))
            print('Setting up camera {}'.format(camera))
            # Add to the list of camera groupboxes
            
        # add to layout
        camera_layout = QGridLayout()
        for camera_groupbox in self.camera_groupboxes:
            camera_layout.addWidget(camera_groupbox)
        
        self.viewfinder_groupbox.setLayout(camera_layout)

    def _init_timers(self):
        # Frame capture timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.capture_frames)
        self.timer.start(int(1000 / self.GUI.recording_config['fps']))
        
        # Display Update timer
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(int(1000  / self.GUI.recording_config['display_update_ps']))
        

    def capture_frames(self):
        # Capture frames from all cameras
        for camera in self.camera_groupboxes:
            # Capture frame
            camera.recording_loop()
            pass
        
    def update_display(self):
        # Update the display for all cameras
        for camera in self.camera_groupboxes:
            # Update the display
            camera.refresh_display()
        
    ### Functions
    
    def change_camera_config(self):
        ### Change the camera configuration
        print('Change camera configuration')
        
        pass
        
    def save_camera_config(self):
        ### Save the camera configuration
        print('Save camera configuration')
        
        pass
    
    def load_camera_config(self):
        ### Load the camera configuration
        print('Load camera configuration')
        
        pass
    
    def select_folder(self):
        # Open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")

        # Update the text box
        self.save_dir_textbox.setPlainText(folder_path)
        # Update the config
        self.GUI.viewfinder_config['save_dir'] = folder_path        
        
    
    def control_all(self):
        
        # Get the selected control
        control = self.control_all_dropdown.currentText()
        
        # Perform the control
        if control == 'Start':
            self.start_all()
        elif control == 'Stop':
            self.stop_all()
        elif control == 'Pause':
            self.pause_all()
        elif control == 'Resume':
            self.resume_all()
        else:
            print('Invalid control')
    
    def start_all(self):
        for camera in self.camera_groupboxes:
            camera.start_recording()
    
    def stop_all(self):
        for camera in self.camera_groupboxes:
            camera.stop_recording()
    
