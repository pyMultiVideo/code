from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import QTimer

import ctypes
import logging
import sys
import os

# import tab classes
from .video_capture_tab import VideoCaptureTab
from .camera_setup_tab import CamerasTab

from config.config import __version__, paths_config

if os.name == "nt":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"pyMultiVideo v{__version__}")


class GUIMain(QMainWindow):
    """
    Class to create the main GUI window
    """

    def __init__(self, parsed_args):
        super().__init__()
        self.startup_config = parsed_args.config
        self.logger = logging.getLogger(__name__)
        self.paths = paths_config
        # Set window size, title, icon.
        self.setGeometry(100, 100, 700, 800)  # x, y, width, height
        self.setWindowTitle(f"pyMultiVideo v{__version__}")  # default window title
        self.setWindowIcon(QIcon(os.path.join(self.paths["assets_dir"], "logo.svg")))
        # Initialise the tabs and tab widget.
        self.camera_setup_tab = CamerasTab(parent=self)
        self.video_capture_tab = VideoCaptureTab(parent=self)
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.video_capture_tab, "Video Capture")
        self.tab_widget.addTab(self.camera_setup_tab, "Cameras")
        self.tab_widget.currentChanged.connect(self.on_tab_change)
        self.setCentralWidget(self.tab_widget)
        # Initialise menu bar.
        main_menu = self.menuBar()
        view_menu = main_menu.addMenu("View")
        full_screen_controls_action = QAction("Toggle Fullscreen", self)
        full_screen_controls_action.setShortcut("Ctrl+F")
        full_screen_controls_action.triggered.connect(self.video_capture_tab.toggle_full_screen_mode)
        view_menu.addAction(full_screen_controls_action)
        # Initialise refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(1000)
        # Display main window.
        self.show()

    def on_tab_change(self):
        """Function that is run on tab change"""
        if self.tab_widget.currentIndex() == 0:
            self.video_capture_tab.play_camera_streaming()
        else:
            self.video_capture_tab.pause_camera_streaming()

    def refresh(self):
        """Call tab refresh methods."""
        # self.camera_setup_tab.refresh()
        self.video_capture_tab.refresh()

    def resizeEvent(self, event):
        """Resize the GUI"""
        self.video_capture_tab.resize(event.size().width(), event.size().height())
        event.accept()

    def closeEvent(self, event):
        """Close the GUI"""
        logging.info("Closing the GUI")
        event.accept()
        sys.exit(0)

    # Exception handling

    def exception_hook(exctype, value, traceback):
        """Hook for uncaught exceptions"""
        logging.error("Uncaught exception", exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
