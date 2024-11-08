from PyQt6.QtGui import (
    QIcon
)
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget
)
from PyQt6.QtCore import (
    QTimer
)

import ctypes
import json
import logging
import sys, os

# import tab classes
from GUI.ViewFinder_Tab import ViewFinder_Tab
from GUI.camera_widget import CameraWidget
from GUI.system_tab import system_tab
from GUI.setups_tab import setups_tab
from GUI.ipython_tab import ipython_tab

# import camera wrapper classes
from api.camera import (
    CameraTemplate as Camera
)
import PySpin

if os.name == 'nt':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Camera Viewer 2')


class GUIApp(QMainWindow):
    '''
    Class to create the main GUI window
    '''
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self._load_camera_names() 
        self._init_cam_list()
        
        # Initialise the tab classess
        self._set_icons()
        self._init_tabs()
        # Could add log in here

        self.setGeometry(100, 100, 700, 800) # x, y, width, height
        self.setWindowTitle('Camera Viewer 2') # default window title
        self.setCentralWidget(self.tab_widget)
        self.show() # show the GUI
        
    def _set_icons(self):
        '''Set the icons for the GUI'''
        icon = QIcon('assets/camera_icon.webp')
        self.setWindowIcon(icon)
        self.statusBar().showMessage('Ready')
                        
    def _init_tabs(self):
        '''Initialize tab classes'''
        # self.summary_tab    = system_tab(parent = self)
        self.viewfinder_tab = ViewFinder_Tab(parent = self)
        self.encoder_tab    = setups_tab(parent = self)
        self.ipython_tab    = ipython_tab(parent = self)
        
        self._add_tabs()

    def _add_tabs(self):
        '''Add tabs to the GUI'''
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.viewfinder_tab, 'View Finder')
        # self.tab_widget.addTab(self.summary_tab,    'Summary')
        self.tab_widget.addTab(self.encoder_tab,    'Encoder')
        self.tab_widget.addTab(self.ipython_tab,    'IPython')
        
    def _load_camera_names(self):
        
        # Get list of json files in the configs folder
        json_files = [f for f in os.listdir('configs') if f.endswith('.json')]
        
        for setup in json_files:
            name = setup.split('.')[0]
            setattr(self, name, json.load(open(f'configs/{setup}')))
                
        logging.info('Loaded configurations: ' + ', '.join(json_files))

    def _init_experiments(self):
        
        # Get list of json files in the configs folder
        json_files = [f for f in os.listdir('experiments') if f.endswith('.json')]
        
        for experiment in json_files:
            name = experiment.split('.')[0]
            setattr(self, name, json.load(open(f'configs/{experiment}')))
                
        logging.info('Loaded configurations: ' + ', '.join(json_files))

    def _init_cam_list(self):
        '''Initialise the camera list'''
        # self.system = CameraSystem()
        # self.cam_list = self.system.get_camera_list()
        
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.numCams = len(self.system.GetCameras())
        # print(self.cam_list)    
        for cam in self.cam_list:
            
            logging.info(f'Found camera: {cam.GetUniqueID()}')
            


    def closeEvent(self, event):
        '''Close the GUI'''
        logging.info('Closing the GUI')
        # Close the camera
        self.cam_list.Clear()
        self.system.ReleaseInstance()
        event.accept()
        # Close the GUI   
        # run ctrl+c
        sys.exit(0)
        
    # Exception handling    
        
    def exception_hook(exctype, value, traceback):
        '''Hook for uncaught exceptions'''
        logging.error('Uncaught exception', exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
        
        