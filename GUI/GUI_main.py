from PyQt6.QtGui import (
    QIcon,
    QAction
)
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget
)
from PyQt6.QtCore import (
    QTimer
)

import ctypes
import json
import logging
import sys
import os
import pandas as pd
# import tab classes
from GUI.VideoCaptureTab  import VideoCaptureTab
from GUI.CameraSetupTab      import CamerasTab

if os.name == 'nt':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('pyMultiVideo')


class GUIApp(QMainWindow):
    '''
    Class to create the main GUI window
    '''
    def __init__(self, parsed_args):
        super().__init__()
        self.startup_config = parsed_args.config
        self.logger = logging.getLogger(__name__)
        self._load_camera_names() 
        # Initialise the tab classess
        self._set_icons()
        self._init_tabs()
        self._init_menu_bar()
        self._init_timers() 
        # self.init_performance_table()
        # Could add logger  here
        self.setGeometry(100, 100, 700, 800) # x, y, width, height
        self.setWindowTitle('pyMultiVideo') # default window title
        self.setCentralWidget(self.tab_widget)
        self.show() # show the GUI
        
        
    def _set_icons(self):
        '''Set the icons for the GUI'''
        icon = QIcon('assets/logo/pyMultiVideo.svg')
        self.setWindowIcon(icon)
        self.statusBar().showMessage('Ready')
                        
    def _init_tabs(self):
        '''Initialize tab classes'''
        self.camera_setup_tab     = CamerasTab(parent = self)
        self.video_capture_tab = VideoCaptureTab(parent = self)
        
        self._add_tabs()

    def _add_tabs(self):
        '''Add tabs to the GUI'''
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.video_capture_tab, 'Video Capture')
        self.tab_widget.addTab(self.camera_setup_tab,     'Cameras')
        
    def _load_camera_names(self):
        
        # Get list of json files in the configs folder
        json_files = [f for f in os.listdir('config') if f.endswith('.json')]
        
        for setup in json_files:
            name = setup.split('.')[0]
            setattr(self, name, json.load(open(f'config/{setup}')))
                
        logging.info('Loaded configurations: ' + ', '.join(json_files))


    def _init_menu_bar(self):
        '''
        Initialises a menu bar for the application 
        '''
        main_menu = self.menuBar()
        # View menu
        view_menu = main_menu.addMenu('View')
        full_screen_controls_action = QAction("Toggle Fullscreen", self)
        full_screen_controls_action.setShortcut('Ctrl+F')       
        # hide_camera_controls_action = QAction("Toggle &Camera Controls", self)
        # hide_camera_controls_action.setShortcut('Ctrl+C')
        # hide_camera_controls_action.triggered.connect(
        #     self.video_capture_tab.toggle_control_header_visibilty
        #     )
        
        # hide_tab_controls_action = QAction('Toggle &Viewfinder Tab Controls', self)
        # hide_tab_controls_action.setShortcut('Ctrl+V')
        # hide_tab_controls_action.triggered.connect(
        #     self.video_capture_tab.toggle_all_viewfinder_control_visiblity
        #     )
        
        # view_menu.addAction(full_screen_controls_actino)
        # view_menu.addAction(hide_camera_controls_action)
        # view_menu.addAction(hide_tab_controls_action)


    def _init_experiments(self):
        # Get list of json files in the configs folder
        json_files = [f for f in os.listdir('experiments') if f.endswith('.json')]
        
        for experiment in json_files:
            name = experiment.split('.')[0]
            setattr(self, name, json.load(open(f'configs/{experiment}')))
                
        logging.info('Loaded configurations: ' + ', '.join(json_files))

    
    def _init_timers(self):
        '''Initialise the timers'''
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(1000)
    
    def refresh(self):
        '''
        Refresh the pages that require it
        '''
        # self.setups_tab.refresh()
        self.video_capture_tab.refresh()
            
    def resizeEvent(self, event):
        '''Resize the GUI'''
        self.video_capture_tab.resize(event.size().width(), event.size().height())
        event.accept()

    def closeEvent(self, event):
        '''Close the GUI'''
        logging.info('Closing the GUI')
        # self.close_performance_table()
        event.accept()
        sys.exit(0)
        
    def init_performance_table(self):
        '''Initialises a pandas dataframe that can keep track of how long a function takes to run'''
        self.performance_table = pd.DataFrame()
        
    def close_performance_table(self):
        '''Function to close the pandas dataframe to disk'''
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.performance_table.to_csv(os.path.join(data_dir, 'performance_table.csv'), index=False)
    # Exception handling    
        
    def exception_hook(exctype, value, traceback):
        '''Hook for uncaught exceptions'''
        logging.error('Uncaught exception', exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
        
        