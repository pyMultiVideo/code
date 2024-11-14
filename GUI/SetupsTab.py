import pandas as pd
from api.data_classes import CameraConfig
from tools.load_camera import get_unique_ids, load_saved_setups
import PyQt6.QtGui as QtGui, PyQt6.QtWidgets as QtWidgets
import PyQt6.QtCore as QtCore
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit
    )

import db as database


class SetupsTabs(QtWidgets.QWidget):
    '''
    Class that creates a setup tab that contains the camera table. This where we can see the camera settings and update them.
    In particular a name for the camera, for each serial number. 
    
    This is the highest level of the setups tab, and contains the camera table.
    
    
    '''
    def __init__(self, parent=None):
        super(SetupsTabs, self).__init__(parent)

        self.GUI = parent
        
        self._initialize_camera_groupbox()

        # 
        self.setups = {} # Dict of setups: {Unique_id: Setup}
        # Get a list of the saved setups from the database
        self.saved_setups = self.load_saved_setups()
        self.refresh()

        # print('List of cameras:', [setup.name if setup.name else setup.unique_id for setup in self.setups.values()])
    # Layout functions

    def _initialize_camera_groupbox(self):
        self.camera_table_groupbox = QGroupBox("Camera Table")
        self.camera_table = CameraOverviewTable(parent=self)
        
        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.camera_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)
        
        self.page_layout = QHBoxLayout()
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.camera_table_layout)
        
    def load_saved_setups(self) -> list[CameraConfig]:
        '''Function to load the saved setups from the database as a list of Setup objects'''
        return load_saved_setups(database)

    def get_saved_setups(self, unique_id: str = None, name: str = None) -> CameraConfig:
        '''
        Get a saved Setup_info object from a name or unique_id from self.saved_setups
        This function gets the next setup that matches the unique_id or name (using the 'next' function)
        '''
        if unique_id:
            try:
                return next(setup for setup in self.saved_setups if setup.unique_id == unique_id)
            except StopIteration:
                pass
        if name:
            try:
                return next(setup for setup in self.saved_setups if setup.name == name)
            except StopIteration:
                pass
        return None
    
    def refresh(self): 
        ''' Function to refresh the entries in the camera table to correspond to the connected cameras'''
        # Get a list of connected cameras (based on their unique id)
        connected_cameras = get_unique_ids()
        # Check if the connected cameras are the same as the setups
        if not connected_cameras == self.setups.keys(): 
            # Add any new cameras setups to the setups
            for unique_id in set(connected_cameras) - set(self.setups.keys()):
                # Check if this unique_id has been seen before by looking in the saved setups database
                setup_info = self.get_saved_setups(unique_id=unique_id)
                if setup_info:
                    # Instantiate the setup and add it to the setups dict
                    self.setups[unique_id] = Setup(
                        setups_table = self.camera_table, 
                        name = setup_info.name, 
                        unique_id = setup_info.unique_id,
                        width = setup_info.width,
                        height = setup_info.height,
                        bitrate = setup_info.bitrate,
                        fps = setup_info.fps,
                        pixel_format = setup_info.pixel_format,
                        gain = setup_info.gain,
                        exposure_time = setup_info.exposure_time
                        )
                # If the unique_id has not been seen before, create a new setup
                else:
                    # Note: Name == None since this is a new camera
                    self.setups[unique_id] = Setup(
                        setups_table = self.camera_table, 
                        name=None, 
                        unique_id=unique_id
                        )
                    
            # Remove any setups that are no longer connected
            for unique_id in set(self.setups.keys()) - set(connected_cameras):
                # Sequence for removed a setup from the table (and deleting it)
                self.setups.pop(unique_id)
                
        
    def get_setups_labels(self) -> list[str]:
        '''Function to get the labels of the setups'''
        return [setup.label for setup in self.setups.values()]
    
    def get_camera_names(self) -> list[str]:
        '''Function to get the names of the cameras if they exist. if they have not been named, use the unique_id'''
        return [setup.name if setup.name else setup.unique_id for setup in self.setups.values()]
    
    def get_camera_unique_id_from_dropdown(self, dropdown: str) -> str:
        '''Function to get the unique_id of the camera from the label'''
        for setup in self.setups.values():
            # Check if the setup name is the same as the dropdown
            if setup.name == dropdown:
                return setup.unique_id
            elif setup.unique_id == dropdown:
                return setup.unique_id
        return None
            
            
class CameraOverviewTable(QTableWidget):
    'List of the cameras and their current settings'
    def __init__(self, parent=None):
        super(CameraOverviewTable, self).__init__(parent)
        self.parent = parent
        # Set the camera table to the camera_table in the database
        self.camera_dict: pd.DataFrame = database.camera_dict
        # Configure the camera table
        self.configure_camera_table()
        # table is populated row by row. Specifically when each new camera is connected view instantiation of a new Setup object


           
    def configure_camera_table(self):
        self.header_names = self.camera_dict[0].keys() if len(self.camera_dict) > 0 else ['Name', 'Unique ID']
        self.setColumnCount(len(self.header_names))
        self.setRowCount(len(self.camera_dict))
        self.verticalHeader().setVisible(False)
        
        self.setHorizontalHeaderLabels(self.header_names)
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)       
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)       
        self.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)       
        self.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)       
        self.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)       
        self.horizontalHeader().setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

class Setup():
    '''Class that contains the setup for the camera'''
    def __init__(self, setups_table, name, unique_id, width=0, height=0, bitrate=0, fps=0, pixel_format='None', gain=0, exposure_time=0):
        self.setups_table = setups_table
        self.name = name
        self.unique_id = unique_id
        self.width = width
        self.height = height
        self.bitrate = bitrate
        self.fps = fps
        self.pixel_format = pixel_format
        self.gain = gain
        self.exposure_time = exposure_time
        
        self.label = self.name if self.name else self.unique_id # If the name is not given, use the unique_id as the label
        
        # Edit name 
        self.name_edit = QLineEdit()
        if self.name:
            self.name_edit.setText(self.name)
        self.name_edit.editingFinished.connect(self.camera_name_changed)

        # Edit unique_id
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        if self.unique_id:
            self.id_edit.setText(self.unique_id)
    
        # Edit width
        self.width_edit = QLineEdit()
        self.width_edit.setReadOnly(True)
        if self.width:
            self.width_edit.setText(str(self.width))
            
        # Edit height
        self.height_edit = QLineEdit()
        self.height_edit.setReadOnly(True)
        if self.height:
            self.height_edit.setText(str(self.height))
            
        # Edit bitrate
        self.bitrate_edit = QLineEdit()
        self.bitrate_edit.setReadOnly(True)
        if self.bitrate:
            self.bitrate_edit.setText(str(self.bitrate))
            
        # Edit fps
        self.fps_edit = QLineEdit()
        self.fps_edit.setReadOnly(True)
        if self.fps:
            self.fps_edit.setText(str(self.fps))
            
        # Edit pixel_format
        self.pixel_format_edit = QLineEdit()
        self.pixel_format_edit.setReadOnly(True)
        if self.pixel_format:
            self.pixel_format_edit.setText(self.pixel_format)
            
        # Edit gain
        self.gain_edit = QLineEdit()
        self.gain_edit.setReadOnly(True)
        if self.gain:
            self.gain_edit.setText(str(self.gain))
    
        # Exit Exposure Time
        self.exposure_time_edit = QLineEdit()
        self.exposure_time_edit.setReadOnly(True)
        if self.exposure_time:
            self.exposure_time_edit.setText(str(self.exposure_time))
            
            

        self.setups_table.insertRow(0)
        self.setups_table.setCellWidget(0, 0, self.name_edit)
        self.setups_table.setCellWidget(0, 1, self.id_edit)
        self.setups_table.setCellWidget(0, 2, self.width_edit)
        self.setups_table.setCellWidget(0, 3, self.height_edit)
        self.setups_table.setCellWidget(0, 4, self.bitrate_edit)
        self.setups_table.setCellWidget(0, 5, self.fps_edit)
        self.setups_table.setCellWidget(0, 6, self.pixel_format_edit)
        self.setups_table.setCellWidget(0, 7, self.gain_edit)
        
        
    def camera_name_changed(self):
        '''Change the name of the camera, getting the new information from the table'''
        self.name = str(self.name_edit.text())
        self.label = self.name if self.name else self.unique_id
        
        self.setups_table
    
    
    def get_info(self):
        return CameraConfig(self.name, self.unique_id, self.subject_id, self.width, self.height, self.bitrate, self.fps, self.pixel_format, self.gain)
    
    