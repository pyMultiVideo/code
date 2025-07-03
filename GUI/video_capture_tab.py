import os
import json
from typing import List
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QLineEdit,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QSpinBox,
    QLabel,
    QMessageBox,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, Qt

from .camera_widget import CameraWidget, CameraWidgetConfig


@dataclass
class ExperimentConfig:
    """Represents the configuration of the VideoCaptureTab."""

    data_dir: str
    n_cameras: int
    n_columns: int
    cameras: list[CameraWidgetConfig]


class MonitoringThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(self, *args, debug=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = 0
        self.lock = threading.Lock()
        self.debug = debug

    def submit(self, fn, *args, **kwargs):
        def wrapper(*args, **kwargs):
            with self.lock:
                self.active += 1
                if self.debug:
                    print(f"Active workers: {self.active}")
            try:
                return fn(*args, **kwargs)
            finally:
                with self.lock:
                    self.active -= 1
                    if self.debug:
                        print(f"Active workers: {self.active}")

        return super().submit(wrapper, *args, **kwargs)


class VideoCaptureTab(QWidget):
    """Tab used to display the viewfinder and control the cameras"""

    def __init__(self, parent=None):
        super(VideoCaptureTab, self).__init__(parent)
        self.GUI = parent
        self.camera_setup_tab = self.GUI.camera_setup_tab
        self.camera_widgets = []
        self.saved_config = None
        self.config_save_path = None

        # Initalise Threadpool
        self.threadpool = MonitoringThreadPoolExecutor(max_workers=32)

        # GUI Layout
        self.camera_layout = QGridLayout()
        self.config_groupbox = QGroupBox("Experiment Configuration")

        # Camera quantity select
        self.n_cameras_label = QLabel("Cameras:")
        self.n_cameras_spinbox = QSpinBox()
        self.n_cameras_spinbox.setRange(1, self.camera_setup_tab.n_setups)
        self.n_cameras_spinbox.valueChanged.connect(self.add_or_remove_camera_widgets)
        self.n_cameras_spinbox.setValue(1)

        # Num columns select.
        self.n_columns_label = QLabel("Columns:")
        self.n_columns_spinbox = QSpinBox()
        self.n_columns_spinbox.setRange(1, self.camera_setup_tab.n_setups)
        self.n_columns_spinbox.valueChanged.connect(self.set_number_of_columns)
        self.n_columns_spinbox.setValue(1)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "save.svg")))
        self.save_button.setFixedHeight(30)
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setToolTip("Save the current camera configuration")

        # Save as button
        self.save_as_button = QPushButton("Save as")
        self.save_as_button.setIcon(QIcon("GUI/icons/save_as.svg"))
        self.save_as_button.setFixedHeight(30)
        self.save_as_button.clicked.connect(self.save_config_as)

        # Load button
        self.load_button = QPushButton("Load")
        self.load_button.setFixedHeight(30)
        self.load_button.clicked.connect(self.load_config)
        self.load_button.setToolTip("Load a saved camera configuration")

        # Config layout
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_button)
        self.config_hlayout.addWidget(self.save_as_button)
        self.config_hlayout.addWidget(self.load_button)
        self.config_hlayout.addWidget(self.n_cameras_label)
        self.config_hlayout.addWidget(self.n_cameras_spinbox)
        self.config_hlayout.addWidget(self.n_columns_label)
        self.config_hlayout.addWidget(self.n_columns_spinbox)
        self.config_groupbox.setLayout(self.config_hlayout)

        self.save_dir_groupbox = QGroupBox("Data Directory")

        # Buttons for saving and loading camera configurations
        self.save_dir_button = QPushButton("")
        self.save_dir_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "folder.svg")))
        self.save_dir_button.setFixedWidth(30)
        self.save_dir_button.setFixedHeight(30)
        self.save_dir_button.clicked.connect(self.get_save_dir)
        self.save_dir_button.setToolTip("Change the directory to save data")

        # Display the save directory
        self.save_dir_textbox = QLineEdit(self.GUI.paths_config["data_dir"])
        self.save_dir_textbox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.save_dir_textbox.setReadOnly(True)
        self.data_dir = self.GUI.paths_config["data_dir"]

        self.save_dir_hlayout = QHBoxLayout()
        self.save_dir_hlayout.addWidget(self.save_dir_textbox)
        self.save_dir_hlayout.addWidget(self.save_dir_button)
        self.save_dir_groupbox.setLayout(self.save_dir_hlayout)

        self.control_all_groupbox = QGroupBox("Control All")

        # Button for recording video
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "record.svg")))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.clicked.connect(self.start_recording)
        self.start_recording_button.setEnabled(False)
        self.start_recording_button.setToolTip("Start recording all cameras")

        # Button for stopping recording
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "stop.svg")))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.setToolTip("Stop recording all cameras")

        self.control_all_hlayout = QHBoxLayout()
        self.control_all_hlayout.addWidget(self.start_recording_button)
        self.control_all_hlayout.addWidget(self.stop_recording_button)
        self.control_all_groupbox.setLayout(self.control_all_hlayout)

        self.header_hlayout = QHBoxLayout()
        self.header_hlayout.addWidget(self.config_groupbox)
        self.header_hlayout.addWidget(self.save_dir_groupbox)
        self.header_hlayout.addWidget(self.control_all_groupbox)

        # Initialise Header Group box
        self.header_groupbox = QGroupBox()
        self.header_groupbox.setMaximumHeight(95)
        self.header_groupbox.setLayout(self.header_hlayout)

        # page layout initalisastion
        self.header_groupbox.setMaximumHeight(95)
        self.page_layout = QVBoxLayout()
        # self.page_layout.addLayout(self.header_hlayout)
        self.page_layout.addWidget(self.header_groupbox)
        self.page_layout.addLayout(self.camera_layout)
        self.setLayout(self.page_layout)
        # Handle if the parsed args are send via the command line
        if self.GUI.parsed_args.experiment_config is None:
            available_cameras = sorted(list(self.camera_setup_tab.get_camera_labels()), key=str.lower)
            for camera_label in available_cameras[:1]:  # One camera by default
                self.initialise_camera_widget(
                    label=camera_label,
                )
        else:
            # Load the default config file
            config_data = json.loads(self.GUI.parsed_args.experiment_config)
            config_data["cameras"] = [CameraWidgetConfig(**camera) for camera in config_data["cameras"]]
            experiment_config = ExperimentConfig(**config_data)
            self.configure_tab_from_config(experiment_config)

        # Timers
        self.camera_widget_update_timer = QTimer()
        self.camera_widget_update_timer.timeout.connect(self.update_camera_widgets)
        self.update_counter = 0

    # Timer callbacks -----------------------------------------------------------------

    def update_camera_widgets(self):
        """Fetches new images from all cameras, updates video displays every n calls."""
        self.update_counter = (self.update_counter + 1) % self.GUI.gui_config["camera_updates_per_display_update"]
        update_video_display = self.update_counter == 0
        for camera_widget in self.camera_widgets:
            camera_widget.update(update_video_display)

    def refresh(self):
        """Refresh tab"""
        for camera_widget in self.camera_widgets:
            camera_widget.refresh()
        # Check the setups_changed flag
        if self.camera_setup_tab.setups_changed:
            self.camera_setup_tab.setups_changed = False
            # Handle the renamed cameras
            self.handle_camera_setups_modified()
        # Update button states
        self.update_button_states()

    # Camera acquisition and recording control ----------------------------------------

    def start_recording(self):
        """Start recording video from all camera widgets."""
        # Check whether all the files name will be the same
        subject_IDs = [camera_widget.subject_id for camera_widget in self.camera_widgets if camera_widget.subject_id]
        if len(subject_IDs) != len(set(subject_IDs)):
            self.start_recording_button.setEnabled(False)
            QMessageBox.information(None, "Duplicate Subject IDs", "Duplicate Subject IDs detected.")
            return

        # Begin Recording
        for camera_widget in self.camera_widgets:
            camera_widget.start_recording()

    def stop_recording(self):
        for camera_widget in self.camera_widgets:
            camera_widget.stop_recording()

    # GUI element update functions ----------------------------------------------------

    def tab_selected(self):
        """Called when tab deselected to start aqusition of the camera video streams."""
        for camera_widget in self.camera_widgets:
            camera_widget.begin_capturing()
        self.camera_widget_update_timer.start(int(1000 / self.GUI.gui_config["camera_update_rate"]))
        self.refresh()

    def tab_deselected(self):
        """Called when tab deselected to pause aqusition of the camera video streams."""
        for camera_widget in self.camera_widgets:
            camera_widget.stop_capturing()
        self.camera_widget_update_timer.stop()

    # Adding and removing camera widgets from the GUI --------------------------------

    def add_or_remove_camera_widgets(self):
        """Add or remove the camera widgets from the"""
        # Get the set of useable cameras
        available_cameras = sorted(
            list(set(self.camera_setup_tab.get_camera_labels()) - set(self.get_camera_widget_labels())), key=str.lower
        )
        # Add camera widgets.
        while self.n_cameras_spinbox.value() > len(self.camera_widgets):
            if available_cameras:
                label = available_cameras.pop(0)
                self.initialise_camera_widget(label=label)
            else:
                break
        # Remove camera widgets.
        while self.n_cameras_spinbox.value() < len(self.camera_widgets):
            self.remove_camera_widget(self.camera_widgets.pop())
        self.refresh()

    def initialise_camera_widget(self, label: str, subject_id=None):
        """Create a new camera widget and add it to the tab"""
        self.camera_widgets.append(CameraWidget(parent=self, label=label, subject_id=subject_id))
        position = len(self.camera_widgets) - 1
        n_columns = self.n_columns_spinbox.value()
        self.camera_layout.addWidget(self.camera_widgets[-1], position // n_columns, position % n_columns)

    def remove_camera_widget(self, camera_widget):
        """Remove camera widget from layout and delete."""
        camera_widget.stop_capturing()
        self.camera_layout.removeWidget(self)
        camera_widget.deleteLater()

    def remove_all_camera_widgets(self):
        """Remove all camera widgets from layout and delete."""
        while self.camera_widgets:
            self.remove_camera_widget(self.camera_widgets.pop())

    def toggle_full_screen_mode(self):
        """Toggle full screen video display mode on/off."""
        is_visible = self.header_groupbox.isVisible()
        self.header_groupbox.setVisible(not is_visible)
        for camera_widget in self.camera_widgets:
            camera_widget.toggle_control_visibility()

    def set_number_of_columns(self):
        """Set the number of columns in the camera grid layout."""
        # Remove all widgets from grid.
        for i in reversed(range(self.camera_layout.count())):
            self.camera_layout.itemAt(i).widget().setParent(None)
        # Add widgets to the grid with the new number of columns
        for i, camera_widget in enumerate(self.camera_widgets):
            n_columns = self.n_columns_spinbox.value()
            self.camera_layout.addWidget(camera_widget, i // n_columns, i % n_columns)

    # Saving and loading experiment configs -------------------------------------------

    def get_config(self):
        """Get tab configuration as an ExperimentConfig object."""
        return ExperimentConfig(
            data_dir=self.data_dir,
            n_cameras=self.n_cameras_spinbox.value(),
            n_columns=self.n_columns_spinbox.value(),
            cameras=[camera_widget.get_camera_config() for camera_widget in self.camera_widgets],
        )

    def save_config_as(self):
        """Save the tab configuration to a json file"""
        default_name = os.path.join("experiments", "experiment_config.json")
        file_path = QFileDialog.getSaveFileName(self, "Save File", default_name, "JSON Files (*.json)")[0]
        if not file_path:
            return
        self.config_save_path = file_path
        self.saved_config = self.get_config()
        with open(self.config_save_path, "w") as config_file:
            config_file.write(json.dumps(asdict(self.saved_config), indent=4))
        self.save_button.setEnabled(False)

    def save_config(self):
        self.saved_config = self.get_config()
        with open(self.config_save_path, "w") as config_file:
            config_file.write(json.dumps(asdict(self.saved_config), indent=4))
        self.save_button.setEnabled(False)

    def load_config(self):
        """Load tab configuration from a json file"""
        file_path = QFileDialog.getOpenFileName(self, "Open File", "experiments", "JSON Files (*.json)")[0]
        if not file_path:
            return
        self.config_save_path = file_path
        with open(self.config_save_path, "r") as config_file:
            config_data = json.load(config_file)
        config_data["cameras"] = [CameraWidgetConfig(**cam_config) for cam_config in config_data["cameras"]]
        experiment_config = ExperimentConfig(**config_data)
        # Check if the config file is valid.
        for camera in experiment_config.cameras:
            if camera.label not in self.camera_setup_tab.get_camera_labels():
                QMessageBox.information(None, "Camera not connected", f"Camera {camera.label} is not connected")
                return
        # Configure tab.
        self.configure_tab_from_config(experiment_config)
        self.saved_config = self.get_config()

    def configure_tab_from_config(self, experiment_config: ExperimentConfig):
        """Configure tab to match settings in experiment config."""
        self.remove_all_camera_widgets()
        # Initialise camera widgets.
        for cam_config in experiment_config.cameras:
            self.initialise_camera_widget(label=cam_config.label, subject_id=cam_config.subject_id)
        # Set the values of the spinbox and encoder selection based on config file
        self.n_cameras_spinbox.setValue(experiment_config.n_cameras)
        self.n_columns_spinbox.setValue(experiment_config.n_columns)
        self.data_dir = experiment_config.data_dir
        self.save_dir_textbox.setText(self.data_dir)

    def handle_camera_setups_modified(self):
        """Handle the renamed cameras by renaming the relevent attributes of the camera groupboxes"""
        for label in self.camera_setup_tab.get_camera_labels():  # New list of camera labels
            # if the label not in the initialised list of cameras (either new or not initialised)
            if label not in self.get_camera_widget_labels():
                # get the unique id of the camera of the queried label
                unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(label)
                # if the unique id is not in the list of camera groupboxes is it a uninitialized camera
                if unique_id in [camera_widget.settings.unique_id for camera_widget in self.camera_widgets]:
                    camera_widget = [c_w for c_w in self.camera_widgets if c_w.settings.unique_id == unique_id][0]
                    # Rename the camera with the queried label
                    camera_widget.rename(new_label=label)
                else:
                    # Camera is uninitialized
                    continue
            else:
                # Camera hasn't been renamed
                continue

    def get_save_dir(self):
        """Return the save directory"""
        save_directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.data_dir)
        if save_directory:
            self.save_dir_textbox.setText(save_directory)
            self.data_dir = save_directory

    def get_camera_widget_labels(self) -> List[str]:
        """Return the camera labels for all camera widgets currently initialsed."""
        return [
            camera_widget.label if camera_widget.label else camera_widget.unique_id
            for camera_widget in self.camera_widgets
        ]

    def update_button_states(self):
        """Update the states of global recording buttons based on the readiness and
        recording status of cameras. Update save button state."""
        all_ready = all(c_w.start_recording_button.isEnabled() for c_w in self.camera_widgets)
        any_recording = any(camera_widget.recording for camera_widget in self.camera_widgets)
        self.start_recording_button.setEnabled(all_ready)
        self.stop_recording_button.setEnabled(any_recording)
        # If any of the cameras are recording, disable certain buttons
        self.save_dir_button.setEnabled(not any_recording)
        self.load_button.setEnabled(not any_recording)
        self.save_as_button.setEnabled(not any_recording)
        self.n_cameras_spinbox.setEnabled(not any_recording)
        self.n_columns_spinbox.setEnabled(not any_recording)
        if not any_recording and self.saved_config != self.get_config() and self.config_save_path:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)
