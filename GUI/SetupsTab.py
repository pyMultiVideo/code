import pandas as pd
from api.data_classes import CameraSettingsConfig
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
import json
import db as database
from dataclasses import asdict

class Setup():
    '''Class that contains the setup for the camera'''
    def __init__(self, 
                setups_table, 
                name, 
                unique_id, 
    ):
        self.setups_table = setups_table
        self.setups_tab = setups_table.parent
        self.label = name
        self.unique_id = unique_id

        
        self.label = self.label if self.label != None else self.unique_id
        
        # Edit name 
        self.name_edit = QLineEdit()
        if self.label:
            self.name_edit.setText(self.label)
        self.name_edit.editingFinished.connect(self.camera_name_changed)

        # Edit unique_id
        self.unique_id_edit = QLineEdit()
        self.unique_id_edit.setReadOnly(True)
        if self.unique_id:
            self.unique_id_edit.setText(self.unique_id)
    
        self.setups_table.insertRow(0)
        self.setups_table.setCellWidget(0, 0, self.name_edit)
        self.setups_table.setCellWidget(0, 1, self.unique_id_edit)
        
    def camera_name_changed(self):
        """Called when name text of setup is edited."""
        self.label = str(self.name_edit.text())
        self.label = self.label if self.label else self.unique_id
        if self.label == "_hidden_":
            self.name_edit.setStyleSheet("color: grey;")
        else:
            self.name_edit.setStyleSheet("color: black;")
        self.setups_tab.update_saved_setups(setup=self)
        self.setups_tab.setups_changed = True
        
    
    def get_info(self):
        return CameraSettingsConfig(
            name = self.label,
            unique_id = self.unique_id,
            )

class SetupsTab(QtWidgets.QWidget):
    '''
    Class that creates a setup tab that contains the camera table. This where we can see the camera settings and update them.
    In particular a name for the camera, for each serial number. 
    
    This is the highest level of the setups tab, and contains the camera table.
    
    
    '''
    def __init__(self, parent=None):
        super(SetupsTab, self).__init__(parent)

        self.GUI = parent
        
        self._initialize_camera_groupbox()
        self.saved_setups_file = database.this.paths['camera_dir'] + '/cameras_configs.json'
        # 
        self.setups: dict[str, Setup] = {} # Dict of setups: {Unique_id: Setup}
        # Get a list of the saved setups from the database
        self.saved_setups = self.load_saved_setups()
        self.refresh()
        # flag to check if the setups have changed (which can be used to update things about the viewfinder tab)
        self.setups_changed = False
        
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
        
    def load_saved_setups(self) -> list[CameraSettingsConfig]:
        '''Function to load the saved setups from the database as a list of Setup objects'''
        return load_saved_setups(database)

    def get_saved_setups(self, unique_id: str = None, name: str = None) -> CameraSettingsConfig:
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
    
    
    def update_saved_setups(self, setup: Setup):
        '''Called when a setup is updated to update the saved setups'''
        saved_setup: CameraSettingsConfig = self.get_saved_setups(unique_id=setup.unique_id)
        camera_settings_config = setup.get_info()
        # if therer are no changes to the setup, return
        if saved_setup == camera_settings_config:
            return
        # if the setup has a name 
        if saved_setup:
            self.saved_setups.remove(saved_setup)
        if setup.label:
            # add the setup config to the saved setups list
            self.saved_setups.append(setup.get_info())
        if self.saved_setups:
            with open(self.saved_setups_file, 'w') as f:
                json.dump([asdict(setup) for setup in self.saved_setups], f, indent=4)
        # else:
        #     self.save_path.unlink(missing_ok=True)
        
        self.refresh()
    
    def refresh(self): 
        ''' Function to refresh the entries in the camera table to correspond to the connected cameras'''
        # Get a list of connected cameras (based on their unique id)
        connected_cameras = get_unique_ids()
        # Check if the connected cameras are the same as the setups
        if not connected_cameras == self.setups.keys(): 
            # Add any new cameras setups to the setups (comparing unique_ids)
            for unique_id in set(connected_cameras) - set(self.setups.keys()):
                # Check if this unique_id has been seen before by looking in the saved setups database
                camera_settings_config: CameraSettingsConfig = self.get_saved_setups(unique_id=unique_id)
                if camera_settings_config:
                    # Instantiate the setup and add it to the setups dict
                    self.setups[unique_id] = Setup(
                        setups_table    = self.camera_table, 
                        name            = camera_settings_config.name, 
                        unique_id       = camera_settings_config.unique_id
                        )
                # If the unique_id has not been seen before, create a new setup
                else:
                    # Note: Name == None since this is a new camera
                    self.setups[unique_id] = Setup(
                        setups_table = self.camera_table, 
                        name=None, 
                        unique_id=unique_id
                        )
                    
                self.update_saved_setups(self.setups[unique_id])
                
            # Remove any setups that are no longer connected
            for unique_id in set(self.setups.keys()) - set(connected_cameras):
                # Sequence for removed a setup from the table (and deleting it)
                self.setups.pop(unique_id)
                
        
    def get_setups_labels(self) -> list[str]:
        '''Function to get the labels of the setups'''
        return [setup.label for setup in self.setups.values()]
    
    def get_camera_labels(self) -> list[str]:
        '''Function to get the names of the cameras if they exist. if they have not been named, use the unique_id'''
        return sorted([setup.label if setup.label else setup.unique_id for setup in self.setups.values()])
    
    def get_camera_unique_ids(self) -> list[str]:
        
        '''Function to get the unique_ids of the cameras'''
        return sorted([setup.unique_id for setup in self.setups.values()])

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        '''Function to get the unique_id of the camera from the label'''

        for setup in self.setups.values():
            print(setup.label, setup.label, camera_label)
            # Check if the setup name is the same as the dropdown
            if setup.label == camera_label:
                return setup.unique_id
            elif setup.unique_id == camera_label:
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
    