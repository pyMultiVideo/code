from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox

import ctypes
import sys
import os
import shutil
import json

# import tab classes
from .video_capture_tab import VideoCaptureTab
from .camera_setup_tab import CamerasTab

from config.config import __version__, gui_config, ffmpeg_config, paths_config

if os.name == "nt":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"pyMultiVideo v{__version__}")


class GUIMain(QMainWindow):
    """Class implementing the main GUI window."""

    def __init__(self, parsed_args):
        super().__init__()
        self.parsed_args = parsed_args
        # Load configs into main class
        if self.parsed_args.config:
            with open(self.parsed_args.config, "r") as config_file:
                config_data = json.load(config_file)
                print(config_data)
            self.ffmpeg_config = config_data["ffmpeg_config"]
            self.paths_config = config_data["paths_config"]
            self.gui_config = config_data["gui_config"]
        else:
            self.ffmpeg_config = ffmpeg_config
            self.paths_config = paths_config
            self.gui_config = gui_config
        self.experiment_config = self.parsed_args.experiment
        # Set window size, title, icon.
        self.setGeometry(100, 100, 700, 800)  # x, y, width, height
        self.setWindowTitle(f"pyMultiVideo v{__version__}")  # default window title
        self.setWindowIcon(QIcon(os.path.join(self.paths_config["icons_dir"], "logo.svg")))
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
        # Check if FFMPEG is available
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffmpeg_path_available = bool(self.ffmpeg_path)
        if not self.ffmpeg_path_available:
            QMessageBox.warning(
                self,
                "Recording unavaialable",
                "FFMPEG path not found. \nPlease install FFMPEG and add to environment variables",
            )
        # Display main window.
        self.show()
        self.video_capture_tab.tab_selected()
        #
        if self.parsed_args.record_on_startup:
            for c_w in self.video_capture_tab.camera_widgets:
                c_w.start_recording()

    def on_tab_change(self):
        """Function that is run on tab change: Deselect the tab you are in before selecting a new tab"""
        if self.tab_widget.currentIndex() == 0:  # Select video_capture_tab
            self.camera_setup_tab.tab_deselected()
            self.video_capture_tab.tab_selected()
        else:  # Select camera_setup_tab
            self.video_capture_tab.tab_deselected()
            self.camera_setup_tab.tab_selected()

    def closeEvent(self, event):
        """Close the GUI"""
        # Close open camera widgets
        for c_w in self.video_capture_tab.camera_widgets:
            if c_w.recording:
                c_w.stop_recording()
            c_w.closeEvent(event)
            c_w.deleteLater()
        # Close Camera preview
        if self.camera_setup_tab.camera_preview:
            self.camera_setup_tab.camera_preview.closeEvent(event)
            self.camera_setup_tab.camera_preview.deleteLater()
        event.accept()
        sys.exit(0)
