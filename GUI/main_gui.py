from PyQt6.QtGui import (
    QIcon
)
import PyQt6.QtWidgets as QtWidgets # This import is used in the script above.
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
from GUI.ViewFinderTab  import ViewFinderTab
from GUI.SetupsTab      import SetupsTab
from GUI.ipython_tab    import iPythonTab

if os.name == 'nt':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('pyCamera')


class GUIApp(QMainWindow):
    '''
    Class to create the main GUI window
    '''
    def __init__(self):
        super().__init__()
        print('Starting GUI')  
        self.logger = logging.getLogger(__name__)
        self._load_camera_names() 
        
        # Initialise the tab classess
        self._set_icons()
        self._init_tabs()
        self._init_timers() 
        # Could add log in here

        self.setGeometry(100, 100, 700, 800) # x, y, width, height
        self.setWindowTitle('pyCamera') # default window title
        self.setCentralWidget(self.tab_widget)
        self.show() # show the GUI
        
    def _set_icons(self):
        '''Set the icons for the GUI'''
        icon = QIcon('assets/logo/pyCamera.svg')
        self.setWindowIcon(icon)
        self.statusBar().showMessage('Ready')
                        
    def _init_tabs(self):
        '''Initialize tab classes'''
        self.setups_tab     = SetupsTab(parent = self)
        self.viewfinder_tab = ViewFinderTab(parent = self)
        self.ipython_tab    = iPythonTab(parent = self)
        
        self._add_tabs()

    def _add_tabs(self):
        '''Add tabs to the GUI'''
        self.tab_widget = QTabWidget()

        self.tab_widget.addTab(self.viewfinder_tab, 'View Finder')
        self.tab_widget.addTab(self.setups_tab,     'Setups')
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
        self.viewfinder_tab.refresh()
            
    def resizeEvent(self, event):
        '''Resize the GUI'''
        self.viewfinder_tab.resize(event.size().width(), event.size().height())
        event.accept()

    def closeEvent(self, event):
        '''Close the GUI'''
        logging.info('Closing the GUI')
        event.accept()
        sys.exit(0)
        
    # Exception handling    
        
    def exception_hook(exctype, value, traceback):
        '''Hook for uncaught exceptions'''
        logging.error('Uncaught exception', exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
        
        