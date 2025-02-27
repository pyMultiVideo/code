import os
import json
from typing import List

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QSpinBox,
    QLabel,
)
from PyQt6.QtGui import QFontMetrics, QIcon
from PyQt6.QtCore import QTimer, Qt

from dataclasses import asdict
from .camera_widget import CameraWidget
from .message_dialogs import show_info_message
from .utility import ExperimentConfig, CameraWidgetConfig, gpu_available
from config.config import gui_config, paths_config


class VideoCaptureTab(QWidget):
    """Tab used to display the viewfinder and control the cameras"""

    def __init__(self, parent=None):
        super(VideoCaptureTab, self).__init__(parent)
        self.GUI = parent
        self.camera_setup_tab = self.GUI.camera_setup_tab
        self.camera_widgets = []
        self.paths = paths_config
        self.camera_layout = QGridLayout()

        # Specify the FFMPEG encoders available
        if gpu_available():
            self.ffmpeg_encoder_map = {
                "h264": "h264_nvenc",
                "h265": "hevc_nvenc",
            }
        else:
            self.ffmpeg_encoder_map = {
                "h264": "libx264",
                "h265": "libx265",
            }

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

        # Save layout button
        self.save_camera_config_button = QPushButton("Save")
        self.save_camera_config_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "save.svg")))
        self.save_camera_config_button.setFixedHeight(30)
        self.save_camera_config_button.clicked.connect(self.save_experiment_config)
        self.save_camera_config_button.setToolTip("Save the current camera configuration")

        # Load layout button
        self.load_experiment_config_button = QPushButton("Load")
        self.load_experiment_config_button.setFixedHeight(30)
        self.load_experiment_config_button.clicked.connect(self.load_experiment_config)
        self.load_experiment_config_button.setToolTip("Load a saved camera configuration")

        # Config layout
        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_camera_config_button)
        self.config_hlayout.addWidget(self.load_experiment_config_button)
        self.config_hlayout.addWidget(self.n_cameras_label)
        self.config_hlayout.addWidget(self.n_cameras_spinbox)
        self.config_hlayout.addWidget(self.n_columns_label)
        self.config_hlayout.addWidget(self.n_columns_spinbox)
        self.config_groupbox.setLayout(self.config_hlayout)

        self.save_dir_groupbox = QGroupBox("Data Directory")

        # Buttons for saving and loading camera configurations
        self.save_dir_button = QPushButton("")
        self.save_dir_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "folder.svg")))
        self.save_dir_button.setFixedWidth(30)
        self.save_dir_button.setFixedHeight(30)
        self.save_dir_button.clicked.connect(self.get_save_dir)
        self.save_dir_button.setToolTip("Change the directory to save data")

        # Display the save directory
        self.save_dir_textbox = QPlainTextEdit(self.paths["data_dir"])
        self.save_dir_textbox.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.save_dir_textbox.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.save_dir_textbox.setMaximumBlockCount(1)
        self.save_dir_textbox.setReadOnly(True)
        self.temp_data_dir = self.paths["data_dir"]
        self.save_dir_textbox.setPlainText(self.temp_data_dir)
        self.update_save_directory_display()

        self.save_dir_hlayout = QHBoxLayout()
        self.save_dir_hlayout.addWidget(self.save_dir_textbox)
        self.save_dir_hlayout.addWidget(self.save_dir_button)
        self.save_dir_groupbox.setLayout(self.save_dir_hlayout)

        self.control_all_groupbox = QGroupBox("Control All")

        # Button for recording video
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "record.svg")))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.clicked.connect(self.start_recording)
        self.start_recording_button.setEnabled(False)
        self.start_recording_button.setToolTip("Start recording all cameras")

        # Button for stopping recording
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "stop.svg")))
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

        # Check if the config file is present
        if self.GUI.startup_config is None:
            available_cameras = sorted(
                list(set(self.camera_setup_tab.get_camera_labels()) - set(self.get_camera_widget_labels())),
                key=str.lower,
            )
            for camera_label in available_cameras[:1]:  # One camera by default
                self.initialize_camera_widget(
                    label=camera_label,
                )
        else:
            # Load the default config file
            with open(self.GUI.startup_config, "r") as config_file:
                config_data = json.load(config_file)
                config_data["cameras"] = [CameraWidgetConfig(**camera) for camera in config_data["cameras"]]
            experiment_config = ExperimentConfig(**config_data)

            self.configure_tab_from_config(experiment_config)

        # Timers
        self.camera_widget_update_timer = QTimer()
        self.camera_widget_update_timer.timeout.connect(self.update_camera_gui)
        self.camera_image_update_timer = QTimer()
        self.camera_image_update_timer.timeout.connect(self.fetch_image_buffers)

    # Timer callbacks -----------------------------------------------------------------

    def update_camera_gui(self):
        """Display new image from to all camera widgets"""
        for camera_widget in self.camera_widgets:
            camera_widget.update_video_display()
            
    def fetch_image_buffers(self):
        """Fetch new images from all cameras, save if recording"""
        for camera_widget in self.camera_widgets:
            camera_widget.fetch_image_data()

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
        self.update_global_recording_button_states()

    def resizeEvent(self, event):
        """Called on resized widget"""
        self.update_save_directory_display()
        super().resizeEvent(event)

    # Camera acquisition and recording control ----------------------------------------

    def start_recording(self):
        # Check whether all the files name will be the same
        camera_labels = [camera_widget.subject_id_text.toPlainText() for camera_widget in self.camera_widgets if camera_widget.subject_id_text.toPlainText()]
        if len(camera_labels) != len(set(camera_labels)):
            self.start_recording_button.setEnabled(False)
            show_info_message("Duplicate Subject IDs detected. Please ensure all are unique.")
            return
        
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
        self.camera_widget_update_timer.start(int(1000 / gui_config["gui_update_rate"]))
        self.camera_image_update_timer.start(int(1000 / gui_config["camera_update_rate"]))
        self.refresh()

    def tab_deselected(self):
        """Called when tab deselected to pause aqusition of the camera video streams."""
        for camera_widget in self.camera_widgets:
            camera_widget.stop_capturing()
        self.camera_widget_update_timer.stop()
        self.camera_image_update_timer.stop()

    def update_save_directory_display(self):
        """Display the path in the textbox"""
        save_dir = self.temp_data_dir
        # Calculate the width of the textbox
        text_edit_width = self.save_dir_textbox.viewport().width()
        font = self.save_dir_textbox.font()
        char_width = QFontMetrics(font).horizontalAdvance("W")
        n_char = text_edit_width // char_width

        if len(save_dir) > n_char:
            save_dir = ".." + save_dir[-(n_char):]
        self.save_dir_textbox.setPlainText(save_dir)

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
                self.initialize_camera_widget(label=label)
            else:
                break
        # Remove camera widgets.
        while self.n_cameras_spinbox.value() < len(self.camera_widgets):
            self.remove_camera_widget(self.camera_widgets.pop())
        self.refresh()

    def initialize_camera_widget(self, label: str, subject_id=None):
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

    def save_experiment_config(self):
        """Save the tab configuration to a json file"""
        default_name = os.path.join("experiments", "experiment_config.json")
        file_path = QFileDialog.getSaveFileName(self, "Save File", default_name, "JSON Files (*.json)")
        experiment_config = ExperimentConfig(
            data_dir=self.temp_data_dir,
            n_cameras=self.n_cameras_spinbox.value(),
            n_columns=self.n_columns_spinbox.value(),
            cameras=[camera_widget.get_camera_config() for camera_widget in self.camera_widgets],
        )
        with open(file_path[0], "w") as config_file:
            config_file.write(json.dumps(asdict(experiment_config), indent=4))

    def load_experiment_config(self):
        """Load tab configuration from a json file"""
        file_path = QFileDialog.getOpenFileName(self, "Open File", "experiments", "JSON Files (*.json)")[0]
        with open(file_path, "r") as config_file:
            config_data = json.load(config_file)
        config_data["cameras"] = [CameraWidgetConfig(**cam_config) for cam_config in config_data["cameras"]]
        experiment_config = ExperimentConfig(**config_data)
        # Check if the config file is valid.
        for camera in experiment_config.cameras:
            if camera.label not in self.camera_setup_tab.get_camera_labels():
                show_info_message(f"Camera {camera.label} is not connected")
                return
        # Configure tab.
        self.configure_tab_from_config(experiment_config)

    def configure_tab_from_config(self, experiment_config: ExperimentConfig):
        """Configure tab to match settings in experiment config."""
        self.remove_all_camera_widgets()
        # Initialise camera widgets.
        for cam_config in experiment_config.cameras:
            self.initialize_camera_widget(label=cam_config.label, subject_id=cam_config.subject_id)
        # Set the values of the spinbox and encoder selection based on config file
        self.n_cameras_spinbox.setValue(experiment_config.n_cameras)
        self.n_columns_spinbox.setValue(experiment_config.n_columns)
        self.temp_data_dir = experiment_config.data_dir
        self.update_save_directory_display()

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
        save_directory = QFileDialog.getExistingDirectory(self, "Select Directory", paths_config["data_dir"])
        if save_directory:
            self.save_dir_textbox.setPlainText(save_directory)
            self.temp_data_dir = save_directory

    def get_camera_widget_labels(self) -> List[str]:
        """Return the camera labels for all camera widgets."""
        return [
            camera_widget.label if camera_widget.label else camera_widget.unique_id
            for camera_widget in self.camera_widgets
        ]

    def update_global_recording_button_states(self):
        """Update the states of global recording buttons based on the readiness and recording status of cameras."""
        all_ready = all(camera_widget.start_recording_button.isEnabled() for camera_widget in self.camera_widgets)
        any_recording = any(camera_widget.recording for camera_widget in self.camera_widgets)
        self.start_recording_button.setEnabled(all_ready)
        self.stop_recording_button.setEnabled(any_recording)
        # If any of the cameras are recording, disable certain buttons
        disable_controls = any_recording
        self.save_dir_button.setEnabled(not disable_controls)
        self.load_experiment_config_button.setEnabled(not disable_controls)
        self.n_cameras_spinbox.setEnabled(not disable_controls)
