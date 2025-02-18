import os
from math import sqrt, ceil
import json
import logging
from typing import List

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QFileDialog,
    QSpinBox,
    QLabel,
    QCheckBox,
)
from PyQt6.QtGui import QFont, QFontMetrics, QIcon
from PyQt6.QtCore import QTimer

from dataclasses import asdict
from .camera_widget import CameraWidget
from .message_dialogs import show_info_message
from .utility import (
    ExperimentConfig,
    CameraSetupConfig,
    get_valid_ffmpeg_encoders,
)
from config.config import gui_config, paths_config


class VideoCaptureTab(QWidget):
    """Tab used to display the viewfinder and control the cameras"""

    def __init__(self, parent=None):
        super(VideoCaptureTab, self).__init__(parent)
        self.GUI = parent
        self.camera_setup_tab = self.GUI.camera_setup_tab
        self.logging = logging.getLogger(__name__)
        self.camera_widgets = []
        self.paths = paths_config
        self.camera_layout = QGridLayout()
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        self.viewfinder_groupbox.setLayout(self.camera_layout)

        # Initialise Header Group box
        self.header_groupbox = QGroupBox()
        self.header_groupbox.setMaximumHeight(95)

        # Encoder select dropdown
        self.encoder_settings_group_box = QGroupBox("FFMPEG Settings")
        self.encoder_selection = QComboBox()
        self.encoder_selection.addItems(get_valid_ffmpeg_encoders())
        self.encoder_selection.setCurrentIndex(1)
        self.encoder = self.encoder_selection.currentText()
        self.encoder_selection.currentIndexChanged.connect(self.change_encoder)

        self.aquire_hlayout = QHBoxLayout()
        self.aquire_hlayout.addWidget(self.encoder_selection)
        self.encoder_settings_group_box.setLayout(self.aquire_hlayout)

        self.config_groupbox = QGroupBox("Experiment Configuration")

        # Text box for displaying the number of camera
        self.camera_config_textbox_label = QLabel("Cameras:")

        self.camera_quantity_spin_box = QSpinBox()
        self.camera_quantity_spin_box.setFont(QFont("Courier", 12))
        self.camera_quantity_spin_box.setReadOnly(False)
        maxCameras = len(self.camera_setup_tab.setups.keys())
        self.camera_quantity_spin_box.setRange(1, maxCameras)
        self.camera_quantity_spin_box.setSingleStep(1)
        self.camera_quantity_spin_box.valueChanged.connect(self.spinbox_add_remove_cameras)
        self.camera_quantity_spin_box.setValue(1)
        #
        self.save_camera_config_button = QPushButton("Save Layout")
        self.save_camera_config_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "save.svg")))
        self.save_camera_config_button.setFixedHeight(30)
        self.save_camera_config_button.clicked.connect(self.save_experiment_config)

        # Button for loading camera configuration
        self.load_experiment_config_button = QPushButton("Load Layout")
        self.load_experiment_config_button.setFixedHeight(30)
        self.load_experiment_config_button.clicked.connect(self.load_experiment_config)

        # Check box for changing the layout of the camera widgets
        self.layout_checkbox = QCheckBox("Grid Layout")
        self.layout_checkbox.setChecked(True)
        self.layout_checkbox.stateChanged.connect(self.change_layout)
        # self.layout_checkbox.setEnabled(True)  # Feature not yet working.

        self.config_hlayout = QHBoxLayout()
        self.config_hlayout.addWidget(self.save_camera_config_button)
        self.config_hlayout.addWidget(self.load_experiment_config_button)
        self.config_hlayout.addWidget(self.camera_config_textbox_label)
        self.config_hlayout.addWidget(self.camera_quantity_spin_box)
        self.config_hlayout.addWidget(self.layout_checkbox)
        self.config_groupbox.setLayout(self.config_hlayout)

        self.save_dir_groupbox = QGroupBox("Save Directory")

        # Buttons for saving and loading camera configurations
        self.save_dir_button = QPushButton("")
        self.save_dir_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "folder.svg")))
        self.save_dir_button.setFixedWidth(30)
        self.save_dir_button.setFixedHeight(30)
        self.save_dir_button.clicked.connect(self.get_save_dir)

        # Display the save directory
        self.save_dir_textbox = QPlainTextEdit(self.paths["data_dir"])
        self.save_dir_textbox.setMaximumBlockCount(1)
        self.save_dir_textbox.setFont(QFont("Courier", 12))
        self.save_dir_textbox.setReadOnly(True)
        self.temp_data_dir = self.paths["data_dir"]
        self.save_dir_textbox.setPlainText(self.temp_data_dir)
        self.display_save_dir_text()

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

        # Button for stopping recording
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "stop.svg")))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        self.stop_recording_button.setEnabled(False)

        self.control_all_hlayout = QHBoxLayout()
        self.control_all_hlayout.addWidget(self.start_recording_button)
        self.control_all_hlayout.addWidget(self.stop_recording_button)
        self.control_all_groupbox.setLayout(self.control_all_hlayout)

        self.header_hlayout = QHBoxLayout()
        self.header_hlayout.addWidget(self.config_groupbox)
        self.header_hlayout.addWidget(self.encoder_settings_group_box)
        self.header_hlayout.addWidget(self.save_dir_groupbox)
        self.header_hlayout.addWidget(self.control_all_groupbox)
        self.header_groupbox.setLayout(self.header_hlayout)

        # page layout initalisastion
        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.header_groupbox)
        self.page_layout.addWidget(self.viewfinder_groupbox)
        self.setLayout(self.page_layout)

        # Check if the config file is present
        if self.GUI.startup_config is None:
            useable_cameras = sorted(
                list(set(self.connected_cameras()) - set(self.camera_groupbox_labels())),
                key=str.lower,
            )
            for camera_label in useable_cameras[:1]:  # One camera by default
                self.initialize_camera_widget(
                    label=camera_label,
                )
        else:
            # Load the default config file
            with open(self.GUI.startup_config, "r") as config_file:
                config_data = json.load(config_file)
                config_data["cameras"] = [CameraSetupConfig(**camera) for camera in config_data["cameras"]]
            experiment_config = ExperimentConfig(**config_data)

            self.configure_tab_from_config(experiment_config)

        # Initialise timers
        self.fetch_images_timer = QTimer()
        self.fetch_images_timer.timeout.connect(self.fetch_image_data)
        self.fetch_images_timer.start(int(1000 / gui_config["fetch_image_rate"]))

        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self.update_display)
        self.display_update_timer.start(int(1000 / gui_config["display_update_rate"]))

    # Timer callbacks -----------------------------------------------------------------

    def fetch_image_data(self):
        """Fetch new images from all cameras and save if recording."""
        for camera_widget in self.camera_widgets:
            camera_widget.fetch_image_data()

    def update_display(self):
        """Update cameras widget video displays."""
        for camera_widget in self.camera_widgets:
            camera_widget.update_video_display()

    def refresh(self):
        """Refresh the viewfinder tab"""
        for camera_widget in self.camera_widgets:
            camera_widget.refresh()
        # Check the setups_changed flag
        if self.camera_setup_tab.setups_changed:
            self.camera_setup_tab.setups_changed = False
            # Handle the renamed cameras
            self.handle_camera_setups_modified()
            
    def resizeEvent(self, event):
        """Called on resized widget"""
        self.display_save_dir_text()
        super().resizeEvent(event)
        
    # Camera acquisition and recording control ----------------------------------------

    def pause_camera_streaming(self):
        """Pause aqusition of the camera video streams."""
        for camera_widget in self.camera_widgets:
            camera_widget.stop_capturing()
        self.fetch_images_timer.stop()

    def play_camera_streaming(self):
        """Restart the aquisition of the camera video streams"""
        for camera_widget in self.camera_widgets:
            camera_widget.begin_capturing()
        self.fetch_images_timer.start(int(1000 / gui_config["fetch_image_rate"]))

    def start_recording(self):
        for camera_widget in self.camera_widgets:
            camera_widget.start_recording()

    def stop_recording(self):
        for camera_widget in self.camera_widgets:
            camera_widget.stop_recording()

    def change_encoder(self):
        """Function to change the encoder used for recording video."""
        self.encoder = self.encoder_selection.currentText()
        self.logging.info("Encoder changed to {}".format(self.encoder))

    # GUI element visibility control --------------------------------------------------

    def toggle_full_screen_mode(self):
        """Function which calls `toggle_control_header_visibility` and `toggle_all_viewfinder_control_visiblity`"""
        self.toggle_control_header_visibilty()
        self.toggle_all_viewfinder_control_visiblity()

    def toggle_control_header_visibilty(self):
        """Toggle the visibility of the control groupbox"""
        is_visible = self.header_groupbox.isVisible()
        self.header_groupbox.setVisible(not is_visible)

    def toggle_all_viewfinder_control_visiblity(self):
        """Function that toggles the visibility of all the camera control widgets"""
        for camera_widget in self.camera_widgets:
            camera_widget.toggle_control_visibility()

    # GUI element update functions ----------------------------------------------------

    def update_camera_dropdowns(self):
        """Update the camera select dropdown menu for all camera widgets."""
        for camera_widget in self.camera_widgets:
            camera_widget.update_camera_dropdown()

    def display_save_dir_text(self):
        """Display the path in the textbox"""
        save_dir = self.temp_data_dir
        n_char = self.calculate_text_field_width()
        if len(save_dir) > n_char:
            save_dir = ".." + save_dir[-(n_char - 2):]
        self.save_dir_textbox.setPlainText(save_dir)
        
    def calculate_text_field_width(self) -> int:
        """Change the amount of text shown in save_dir textfield"""
        text_edit_width = self.save_dir_textbox.viewport().width()
        font = self.save_dir_textbox.font()
        char_width = QFontMetrics(font).horizontalAdvance('A')
        return text_edit_width // char_width - 2
    
    def spinbox_add_remove_cameras(self):
        """
        Function attached to the spinbox that adds or removes cameras from the viewfinder tab
        """
        # Get the set of useable cameras
        useable_cameras = sorted(
            list(set(self.connected_cameras()) - set(self.camera_groupbox_labels())),
            key=str.lower,
        )

        # value of spinbox
        if self.camera_quantity_spin_box.value() > len(
            self.camera_widgets
        ):  # If the number of cameras is being reduced
            label = useable_cameras[0]
            self.initialize_camera_widget(
                label=label,
            )

        elif self.camera_quantity_spin_box.value() <= len(self.camera_widgets):
            for i in range(len(self.camera_widgets) - self.camera_quantity_spin_box.value()):
                self.remove_camera_widget(self.camera_widgets.pop())

        self.refresh()

    def initialize_camera_widget(self, label: str, subject_id=None):
        """Create a new camera widget and add it to the viewfinder tab"""
        # create_new_viewfinder(self, label, subject_id)
        self.camera_widgets.append(
            CameraWidget(
                parent=self,
                label=label,
                subject_id=subject_id,
            )
        )
        self.add_widget_to_layout()

    def add_widget_to_layout(self):
        """
        """
        if type(self.camera_layout) is QGridLayout:
            # Grid Layout
            position = len(self.camera_widgets) - 1
            self.camera_layout.addWidget(self.camera_widgets[-1], position // 2, position % 2)
        elif type(self.camera_layout) is QVBoxLayout:
            # Vertical Layout
            self.camera_layout.addWidget(self.camera_widgets[-1])
            
        self.refresh()

    def remove_camera_widget(self, camera_widget):
        """Remove camera widget from layout and delete."""
        camera_widget.stop_capturing()
        self.camera_layout.removeWidget(self)
        camera_widget.deleteLater()

    def remove_all_camera_widgets(self):
        """Remove all camera widgets from layout and delete."""
        while self.camera_widgets:
            self.remove_camera_widget(self.camera_widgets.pop())

    def change_layout(self):
        """Function to change the layout of the camera widgets between grid and vertical."""
        # Create new layout and populate with existing camera widgets.
        new_layout = QGridLayout() if self.layout_checkbox.isChecked() else QVBoxLayout()
        for index, camera_widget in enumerate(self.camera_widgets):
            if isinstance(new_layout, QGridLayout):
                new_layout.addWidget(camera_widget, index // 2, index % 2)
            else:
                new_layout.addWidget(camera_widget)
        # Assign old layout to temporary widget to remove it from viewfinder_groupbox.
        QWidget().setLayout(self.camera_layout)
        # Set new layout to viewfinder_groupbox.
        self.camera_layout = new_layout
        self.viewfinder_groupbox.setLayout(self.camera_layout)


    # Saving and loading experiment configs -------------------------------------------

    def save_experiment_config(self):
        """Save the tab configuration to a json file"""
        file_path = QFileDialog.getSaveFileName(self, "Save File", "experiments", "JSON Files (*.json)")
        experiment_config = ExperimentConfig(
            data_dir=self.save_dir_textbox.toPlainText(),
            encoder=self.encoder_selection.currentText(),
            num_cameras=self.camera_quantity_spin_box.value(),
            grid_layout=self.layout_checkbox.isChecked(),
            cameras=[camera_widget.get_camera_config() for camera_widget in self.camera_widgets],
        )
        with open(file_path[0], "w") as config_file:
            config_file.write(json.dumps(asdict(experiment_config), indent=4))

    def load_experiment_config(self):
        """Function to load a camera configuration from a json file"""
        # deinitialise all cameras that are currently running
        file_path = QFileDialog.getOpenFileName(self, "Open File", "experiments", "JSON Files (*.json)")[0]
        with open(file_path, "r") as config_file:
            config_data = json.load(config_file)
        config_data["cameras"] = [CameraSetupConfig(**cam_config) for cam_config in config_data["cameras"]]
        experiment_config = ExperimentConfig(**config_data)
        # Check if the config file is valid.
        for camera in experiment_config.cameras:
            if camera.label not in self.camera_setup_tab.get_setups_labels():
                show_info_message(f"Camera {camera.label} is not connected")
                return
        # Load the camera configuration
        self.configure_tab_from_config(experiment_config)

    def configure_tab_from_config(self, experiment_config: ExperimentConfig):
        """Configure tab to match settings in experiment config."""
        self.remove_all_camera_widgets()
        # Initialise camera widgets.
        for cam_config in experiment_config.cameras:
            self.initialize_camera_widget(label=cam_config.label, subject_id=cam_config.subject_id)
        # Set the values of the spinbox and encoder selection based on config file
        self.camera_quantity_spin_box.setValue(experiment_config.num_cameras)
        self.encoder_selection.setCurrentText(experiment_config.encoder)
        self.save_dir_textbox.setPlainText(experiment_config.data_dir)
        self.layout_checkbox.setChecked(experiment_config.grid_layout)

    def handle_camera_setups_modified(self):
        """
        Handle the renamed cameras by renaming the relevent attributes of the camera groupboxes

        TODO: Add the ability to change the camera settings of a CameraWidget (i.e. fps, pxl_fmt).
        This requires changing the display of these attributes further to changing how the camera is actually recording.
        """
        for label in self.connected_cameras():  # New list of camera labels
            # if the label not in the initialised list of cameras (either new or not initialised)
            if label not in self.camera_groupbox_labels():
                # get the unique id of the camera of the queried label
                unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(label)
                # if the unique id is not in the list of camera groupboxes is it a uninitialized camera
                if unique_id in [camera_widget.unique_id for camera_widget in self.camera_widgets]:
                    camera_widget = [c_w for c_w in self.camera_widgets if c_w.unique_id == unique_id][0]
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
            
    def camera_groupbox_labels(self) -> List[str]:
        """Return the labels of the camera groupboxes"""
        return [camera_widget.label for camera_widget in self.camera_widgets]

    def connected_cameras(self) -> List[str]:
        """Return the labels of cameras connected to the PC"""
        return self.camera_setup_tab.get_setups_labels()

    def update_global_recording_button_states(self):
        """Update the states of global recording buttons based on the readiness and recording status of cameras."""
        all_ready = all(camera_widget.start_recording_button.isEnabled() for camera_widget in self.camera_widgets)
        any_recording = any(camera_widget.recording for camera_widget in self.camera_widgets)

        self.start_recording_button.setEnabled(all_ready)
        self.stop_recording_button.setEnabled(any_recording)

        # If any of the cameras are recording, disable certain buttons
        disable_controls = any_recording
        self.save_dir_button.setEnabled(not disable_controls)
        self.encoder_selection.setEnabled(not disable_controls)
        self.load_experiment_config_button.setEnabled(not disable_controls)
        self.camera_quantity_spin_box.setEnabled(not disable_controls)
