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
from .camera_setup_tab import CameraSetupTab

from config.config import __version__, gui_config, ffmpeg_config, paths_config


if os.name == "nt":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"pyMultiVideo v{__version__}")

PROFILING = False


class GUIMain(QMainWindow):
    """Class implementing the main GUI window."""

    def __init__(self, parsed_args):
        # Start profiler

        super().__init__()
        # Deal with arguments parsed to application
        self.parsed_args = parsed_args
        # config arguments
        if self.parsed_args.application_config:
            config_data = json.loads(self.parsed_args.application_config)
            self.paths_config = config_data.get("paths_config")
            self.ffmpeg_config = config_data.get("ffmpeg_config")
            self.gui_config = config_data.get("gui_config")
        else:
            self.paths_config = paths_config
            self.ffmpeg_config = ffmpeg_config
            self.gui_config = gui_config
        if PROFILING:
            from pyinstrument import Profiler

            self.profiler = Profiler()
            self.profiler.start()

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

        # Check if FFMPEG is available
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffmpeg_path_available = bool(self.ffmpeg_path)
        if not self.ffmpeg_path_available:
            QMessageBox.warning(
                self,
                "Recording unavaialable",
                "FFMPEG path not found. \nPlease install FFMPEG and add to environment variables",
            )
        # Set window size, title, icon.
        self.setGeometry(100, 100, 900, 800)  # x, y, width, height
        self.setWindowTitle(f"pyMultiVideo v{__version__}")  # default window title
        self.setWindowIcon(QIcon(os.path.join(self.paths_config["icons_dir"], "logo.svg")))
        # Initialise the tabs and tab widget.
        self.camera_setup_tab = CameraSetupTab(parent=self)
        self.camera_setup_tab.tab_deselected()
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

        # Display main window.
        self.show()
        self.video_capture_tab.tab_selected()
        # Recording Options
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
        # Stop profiler and save results to HTML
        if hasattr(self, "profiler"):
            self.profiler.stop()
            html_output = self.profiler.output_html()
            output_path = os.path.join(self.paths_config.get("config_dir", "."), "profiler_report.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            print(f"Profiler HTML report saved to: {output_path}")
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
