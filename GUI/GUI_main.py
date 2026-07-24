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
from .settings_tab import SettingsTab
from .camera_manager import CameraManager

from config.config import __version__, gui_config, ffmpeg_config, paths_config

if os.name == "nt":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"pyMultiVideo v{__version__}")


class GUIMain(QMainWindow):
    """Class implementing the main GUI window."""

    def __init__(self, parsed_args):
        super().__init__()

        # Handle arguments parsed to application by CLI.
        self.CLI_args = parsed_args

        if self.CLI_args.application_config:  # Config info passed from CLI.
            config_data = json.loads(self.CLI_args.application_config)
            self.paths_config = config_data.get("paths_config")
            self.ffmpeg_config = config_data.get("ffmpeg_config")
            self.gui_config = config_data.get("gui_config")
        else:  # Use config info from config.py and application_config.json file.
            self.paths_config = paths_config
            settings_filepath = os.path.join(self.paths_config["config_dir"], "application_config.json")
            if os.path.exists(settings_filepath):
                with open(settings_filepath, "r", encoding="utf-8") as f:
                    self.ffmpeg_config = json.load(f)["ffmpeg_config"]
            else:
                self.ffmpeg_config = ffmpeg_config
            self.gui_config = gui_config

        # close-after argument
        if self.CLI_args.close_after:
            # Parse time in HH:SS format
            time_parts = self.CLI_args.close_after.split(":")
            mins = int(time_parts[0])
            seconds = int(time_parts[1])
            total_seconds = mins * 60 + seconds
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
        self.camera_manager = CameraManager()
        self.camera_setup_tab = SettingsTab(parent=self)
        self.camera_setup_tab.tab_deselected()
        self.video_capture_tab = VideoCaptureTab(parent=self)
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.video_capture_tab, "Video Capture")
        self.tab_widget.addTab(self.camera_setup_tab, "Settings")
        self.tab_widget.currentChanged.connect(self.on_tab_change)
        self.setCentralWidget(self.tab_widget)

        # Keyboard shortcuts.
        self.maximise_video_action = QAction("Maximise Video", self)
        self.maximise_video_action.setShortcut("Ctrl+M")
        self.maximise_video_action.triggered.connect(self.handle_maximise_video_action)
        self.addAction(self.maximise_video_action)

        self.full_screen_video_action = QAction("Fullscreen Video", self)
        self.full_screen_video_action.setShortcut("Ctrl+F")
        self.full_screen_video_action.triggered.connect(self.toggle_full_screen_video)
        self.addAction(self.full_screen_video_action)

        self.exit_maximised_video_action = QAction("Exit Maximised Video", self)
        self.exit_maximised_video_action.setShortcut("Esc")
        self.exit_maximised_video_action.triggered.connect(self.exit_to_standard_video_mode)
        self.addAction(self.exit_maximised_video_action)
        self.set_video_mode_actions_enabled(self.tab_widget.currentIndex() == 0)

        # Display main window.
        self.show()
        self.video_capture_tab.tab_selected()
        # Recording Options
        if self.CLI_args.record_on_startup:
            for c_w in self.video_capture_tab.camera_widgets:
                c_w.start_recording()

    def on_tab_change(self):
        """Function that is run on tab change: Deselect the tab you are in before selecting a new tab"""
        if self.tab_widget.currentIndex() == 0:  # Select video_capture_tab
            self.set_video_mode_actions_enabled(True)
            self.camera_setup_tab.tab_deselected()
            self.video_capture_tab.tab_selected()
        else:  # Select camera_setup_tab
            self.exit_to_standard_video_mode()
            self.set_video_mode_actions_enabled(False)
            self.video_capture_tab.tab_deselected()
            self.camera_setup_tab.tab_selected()

    def set_video_mode_actions_enabled(self, enabled: bool):
        """Enable or disable keyboard actions used by video display modes."""
        self.maximise_video_action.setEnabled(enabled)
        self.full_screen_video_action.setEnabled(enabled)
        self.exit_maximised_video_action.setEnabled(enabled)

    def handle_maximise_video_action(self):
        """Handle Ctrl+M with special behavior while in fullscreen mode."""
        if self.isFullScreen():  # Leave fullscreen but keep video maximised layout.
            self.showNormal()
        else:
            self.video_capture_tab.toggle_maximise_video()

    def toggle_full_screen_video(self):
        """Toggle true fullscreen video mode while preserving maximised-video layout behavior."""
        if self.isFullScreen():
            self.exit_to_standard_video_mode()
        else:
            self.video_capture_tab.enter_video_maximised_mode()
            self.showFullScreen()

    def exit_to_standard_video_mode(self):
        """Return to standard mode: not fullscreen and not maximised video layout."""
        if self.isFullScreen():
            self.showNormal()
        self.video_capture_tab.exit_video_maximised_mode()

    def closeEvent(self, event):
        """Close the GUI"""
        # Ensure all threadpool futures are complete
        while self.video_capture_tab.futures:
            future = self.video_capture_tab.futures.pop()
            future.result()
        # Close open camera widgets
        for c_w in self.video_capture_tab.camera_widgets:
            if c_w.recording:
                c_w.stop_recording()
            c_w.closeEvent(event)
            c_w.deleteLater()
        # Close Camera preview
        if self.camera_setup_tab.preview_showing:
            self.camera_setup_tab.camera_preview.closeEvent(event)
            self.camera_setup_tab.camera_preview.deleteLater()

        self.camera_manager.close_all()

        event.accept()
        sys.exit(0)

    def exception_hook(self, exctype, value, traceback):
        """Hook for uncaught exceptions"""
        print("Using the except hook to close the application")

        if exctype is KeyboardInterrupt:
            print("KeyboardInterrupt detected. Closing GUI.")
            self.close()
        else:
            print("Uncaught exception:", exctype, value, traceback)
        sys.__excepthook__(exctype, value, traceback)
        sys.__excepthook__(exctype, value, traceback)
