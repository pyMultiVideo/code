from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QTabWidget

import ctypes
import logging
import sys
import os

# import tab classes
from .video_capture_tab import VideoCaptureTab
from .camera_setup_tab import CamerasTab

from config.config import __version__, paths_config, profiling_config

if os.name == "nt":  # Needed on windows to get taskbar icon to display correctly.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"pyMultiVideo v{__version__}")


class GUIMain(QMainWindow):
    """
    Class to create the main GUI window
    """

    def __init__(self, parsed_args):
        super().__init__()
        self.startup_config = parsed_args.config
        self.paths = paths_config
        # Profiling the application
        if profiling_config["profile_code"]:
            from pyinstrument import Profiler
            from datetime import datetime

            self.profiler = Profiler()
            self.profiler.start()
            profiling_config["save_dir_name"] = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        # Display main window.
        self.show()
        self.video_capture_tab.tab_selected()

    def on_tab_change(self):
        """Function that is run on tab change: Deselect the tab you are in before selecting a new tab"""
        if self.tab_widget.currentIndex() == 0:
            self.camera_setup_tab.tab_deselected()
            self.video_capture_tab.tab_selected()
        else:
            self.video_capture_tab.tab_deselected()
            self.camera_setup_tab.tab_selected()

    def resizeEvent(self, event):
        """Resize the GUI"""
        self.video_capture_tab.resize(event.size().width(), event.size().height())
        event.accept()

    def closeEvent(self, event):
        """Close the GUI"""
        for c_w in self.video_capture_tab.camera_widgets:
            if c_w.recording:
                c_w.stop_recording()
            c_w.deleteLater()
        event.accept()
        # End profiling application & Saving metadata to output folder
        if profiling_config["profile_code"]:

            import shutil
            import json
            from dataclasses import asdict
            from .utility import ExperimentConfig

            self.profiler.stop()
            profile_dir = os.path.join(self.paths["data_dir"], "profiling", profiling_config["save_dir_name"])
            os.makedirs(profile_dir, exist_ok=True)
            with open(os.path.join(profile_dir, f"{profiling_config['profile_name']}.html"), "w") as f:
                f.write(self.profiler.output_html())
            # Copy the config file
            shutil.copy(os.path.join(self.paths["config_dir"], "config.py"), profile_dir)
            # Copy the states of the GUI to a config file
            experiment_config = ExperimentConfig(
                data_dir=self.video_capture_tab.temp_data_dir,
                n_cameras=self.video_capture_tab.n_cameras_spinbox.value(),
                n_columns=self.video_capture_tab.n_columns_spinbox.value(),
                cameras=[camera_widget.get_camera_config() for camera_widget in self.video_capture_tab.camera_widgets],
            )
            config_file_path = os.path.join(profile_dir, "gui-config.json")
            with open(config_file_path, "w") as config_file:
                config_file.write(json.dumps(asdict(experiment_config), indent=4))
            # Copy the states of the cameras to the folder
            shutil.copy(os.path.join(self.paths["config_dir"], "camera_configs.json"), profile_dir)

        sys.exit(0)

    # Exception handling

    def exception_hook(exctype, value, traceback):
        """Hook for uncaught exceptions"""
        logging.error("Uncaught exception", exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
