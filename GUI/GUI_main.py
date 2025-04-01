from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtCore import QTimer
import ctypes
import sys
import os
import shutil
import json

# import tab classes
from .video_capture_tab import VideoCaptureTab
from .camera_setup_tab import CamerasTab

from config.config import __version__, gui_config, ffmpeg_config, paths_config
import logging


if os.name == "nt":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"pyMultiVideo v{__version__}")


class GUIMain(QMainWindow):
    """Class implementing the main GUI window."""

    def __init__(self, parsed_args):
        super().__init__()
        ### Deal with arguments parsed to application ###
        self.paths_config = paths_config
        self.ffmpeg_config = ffmpeg_config
        self.gui_config = gui_config
        self.parsed_args = parsed_args
        print(self.parsed_args)
        self.experiment_config = self.parsed_args.experiment_config
        # Update config values with parsed arguments if specified
        config_mappings = {
            self.parsed_args.camera_update_rate: ("gui_config", "camera_update_rate"),
            self.parsed_args.camera_updates_per_display_update: ("gui_config", "camera_updates_per_display_update"),
            self.parsed_args.font_size: ("gui_config", "font_size"),
            self.parsed_args.crf: ("ffmpeg_config", "crf"),
            self.parsed_args.encoding_speed: ("ffmpeg_config", "encoding_speed"),
            self.parsed_args.compression_standard: ("ffmpeg_config", "compression_standard"),
        }
        for arg, (config, key) in config_mappings.items():
            if arg:
                getattr(self, config)[key] = arg
        # close-after argument
        if self.parsed_args.close_after:
            # Parse time in HH:SS format
            time_parts = self.parsed_args.close_after.split(":")
            hours = int(time_parts[0])
            seconds = int(time_parts[1])
            total_seconds = hours * 3600 + seconds
            close_timer = QTimer(self)
            close_timer.setInterval(total_seconds * 1000)
            close_timer.setSingleShot(True)
            close_timer.timeout.connect(self.close)
            close_timer.start()

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
        # Recording Options
        if self.parsed_args.record_on_startup:
            for c_w in self.video_capture_tab.camera_widgets:
                if self.parsed_args.downsampling_factor:  # Set the downsampling factor if specified
                    c_w.settings.downsampling_factor = self.parsed_args.downsampling_factor
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

    def exception_hook(self, exctype, value, traceback):
        """Hook for uncaught exceptions"""
        print("Using the except hook to close the application")

        if exctype is KeyboardInterrupt:
            print("KeyboardInterrupt detected. Closing GUI.")
            self.close()
        else:
            print("Uncaught exception", exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
