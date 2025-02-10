import time
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
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QTimer

from dataclasses import asdict
from .viewfinder_widget import ViewfinderWidget
from .dialogs import show_info_message
from tools import (
    ExperimentConfig,
    CameraSetupConfig,
    valid_ffmpeg_encoders,
    gpu_available,
)
from config import gui_config_dict
from config import paths_config_dict


class VideoCaptureTab(QWidget):
    """Tab used to display the viewfinder and control the cameras"""

    def __init__(self, parent=None):
        super(VideoCaptureTab, self).__init__(parent)
        self.GUI = parent
        self.camera_setup_tab = self.GUI.camera_setup_tab
        self.logging = logging.getLogger(__name__)
        self.camera_groupboxes = []
        self.paths = paths_config_dict
        self.camera_layout = QGridLayout()
        self.viewfinder_groupbox = QGroupBox("Viewfinder")
        self.viewfinder_groupbox.setLayout(self.camera_layout)

        self._init_timers()
        print("Viewfinder tab initialised")

        # Initialise Header Group box
        self.header_groupbox = QGroupBox()
        self.header_groupbox.setMaximumHeight(95)

        """List of encoders that are available"""
        self.encoder_settings_group_box = QGroupBox("FFMPEG Settings")
        # dropdown for camera selection
        self.encoder_selection = QComboBox()

        self.encoder_selection.addItems(
            valid_ffmpeg_encoders(
                GPU_AVAIALABLE=gpu_available(),
                encoder_dict_keys=self.camera_setup_tab.ffmpeg_config["output"][
                    "encoder"
                ].keys(),
            )
        )

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
        self.camera_quantity_spin_box.valueChanged.connect(
            self.spinbox_add_remove_cameras
        )
        self.camera_quantity_spin_box.setValue(1)
        #
        self.save_camera_config_button = QPushButton("Save Layout")
        self.save_camera_config_button.setIcon(
            QIcon(os.path.join(self.paths["assets_dir"], "save.svg"))
        )
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
        # This feature does not work. disable the checkbox
        self.layout_checkbox.setEnabled(False)

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
        self.save_dir_button.setIcon(
            QIcon(os.path.join(self.paths["assets_dir"], "folder.svg"))
        )
        self.save_dir_button.setFixedWidth(30)
        self.save_dir_button.setFixedHeight(30)
        self.save_dir_button.clicked.connect(self.get_save_dir)

        # Display the save directory
        self.save_dir_textbox = QPlainTextEdit()
        self.save_dir_textbox.setMaximumBlockCount(1)
        self.save_dir_textbox.setFont(QFont("Courier", 12))
        self.save_dir_textbox.setReadOnly(True)
        self.save_dir_textbox.setPlainText(self.paths["data_dir"])

        self.save_dir_hlayout = QHBoxLayout()
        self.save_dir_hlayout.addWidget(self.save_dir_textbox)
        self.save_dir_hlayout.addWidget(self.save_dir_button)
        self.save_dir_groupbox.setLayout(self.save_dir_hlayout)

        self.control_all_groupbox = QGroupBox("Control All")

        # Button for recording video
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(
            QIcon(os.path.join(self.paths["assets_dir"], "record.svg"))
        )
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.clicked.connect(self.start_recording)

        # Button for stopping recording
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(
            QIcon(os.path.join(self.paths["assets_dir"], "stop.svg"))
        )
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.clicked.connect(self.stop_recording)

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
                list(
                    set(self.connected_cameras()) - set(self.camera_groupbox_labels())
                ),
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
                config_data["cameras"] = [
                    CameraSetupConfig(**camera) for camera in config_data["cameras"]
                ]
            experiment_config = ExperimentConfig(**config_data)

            self.load_from_config_dir(experiment_config)

    ### Visibility Controls

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
        for camera in self.camera_groupboxes:
            camera.toggle_control_visibility()

    ### Timer Functions

    def _init_timers(self):
        """Initialise the timers for the viewfinder tab"""
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self.update_display)
        self.display_update_timer.start(
            int(1000 / gui_config_dict["update_display_rate"])
        )  # 30 fps by default. Can be edited in the .json file

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(1000)

    def update_display(self):
        """
        Function that calls the required functions to collect, encode and display the images from the camera.
        """
        TESTING = False
        # TESTING = True
        if TESTING is True:
            for camera_widget in self.camera_groupboxes:
                # check if the camera is in the performance_table as a column
                if camera_widget.unique_id not in self.GUI.performance_table.columns:
                    self.GUI.performance_table[camera_widget.unique_id] = []

        for camera_widget in self.camera_groupboxes:
            if TESTING is True:
                start_time = time.time()
            camera_widget.fetch_image_data()
            camera_widget.display_frame(camera_widget._image_data)
            camera_widget.update_gpio_overlay()
            if TESTING is True:
                end_time = time.time()
                # Append the time taken to the performance table
                self.GUI.performance_table.loc[time.time(), camera_widget.unique_id] = (
                    end_time - start_time
                )

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
            self.camera_groupboxes
        ):  # If the number of cameras is being reduced
            label = useable_cameras[0]
            self.initialize_camera_widget(
                label=label,
            )

        elif self.camera_quantity_spin_box.value() <= len(self.camera_groupboxes):
            for i in range(
                len(self.camera_groupboxes) - self.camera_quantity_spin_box.value()
            ):
                # Removes camera from
                camera = self.camera_groupboxes.pop()
                camera.disconnect()
                camera.deleteLater()

        self.refresh()

    def initialize_camera_widget(self, label: str, subject_id=None):
        """Create a new camera widget and add it to the viewfinder tab"""
        # create_new_viewfinder(self, label, subject_id)
        self.camera_groupboxes.append(
            ViewfinderWidget(
                parent=self,
                label=label,
                subject_id=subject_id,
            )
        )
        self.add_widget_to_layout()

    def add_widget_to_layout(self):
        """Add the camera widget to the layout
        Will try to make the camera layout as square as possible. THis will be based on the nunber of connected cameras to the setup
        """
        SQUARE = True
        if SQUARE:
            # Position of the new camera to be added.
            position = len(self.camera_groupboxes) - 1
            # Square side length calculated
            side_len = ceil(sqrt(len(self.connected_cameras())))
            # Could instead, add a manual setting for the number of colmns in the layout.
            # Add the new camera to the correct position
            self.camera_layout.addWidget(
                self.camera_groupboxes[-1], position // side_len, position % side_len
            )
        else:
            if type(self.camera_layout) is QGridLayout:
                # Grid Layout
                position = len(self.camera_groupboxes) - 1
                self.camera_layout.addWidget(
                    self.camera_groupboxes[-1], position // 2, position % 2
                )
            elif type(self.camera_layout) is QVBoxLayout:
                # Vertical Layout
                self.camera_layout.addWidget(self.camera_groupboxes[-1])
        self.refresh()

    def change_layout(self):
        """Function to change the layout of the camera widgets

        Change the layout from the square one to a vertical one
        This function should be able to be called whilst recording is taking place
        """
        no_cameras = len(self.camera_groupboxes)
        for camera in self.camera_groupboxes:
            # Remove all the camera from the layout
            camera = self.camera_groupboxes.pop()
            camera.disconnect()
        # Remove the widget
        # self.viewfinder_groupbox.removeLayout(self.camera_layout)
        # Change the layout after the cameras have been removed
        if self.layout_checkbox.isChecked():
            self.camera_layout = QGridLayout()
        else:
            self.camera_layout = QVBoxLayout()

        self.viewfinder_groupbox.setLayout(self.camera_layout)

        useable_cameras = sorted(
            list(set(self.connected_cameras())),
            key=str.lower,
        )

        for camera_index in range(no_cameras):
            print("Label:", useable_cameras[camera_index])
            self.initialize_camera_widget(label=useable_cameras[camera_index])

    def change_encoder(self):
        "Function to change the encoder"
        self.encoder = self.encoder_selection.currentText()
        self.logging.info("Encoder changed to {}".format(self.encoder))

    ### Functions

    def get_page_config(self) -> ExperimentConfig:
        """From the GUI, get the data that defines the layout of the page.
        Returns ExperimentConfig (datastruct)
        """
        return ExperimentConfig(
            data_dir=self.save_dir_textbox.toPlainText(),
            encoder=self.encoder_selection.currentText(),
            num_cameras=self.camera_quantity_spin_box.value(),
            grid_layout=self.layout_checkbox.isChecked(),
            cameras=[camera.get_camera_config() for camera in self.camera_groupboxes],
        )

    def save_experiment_config(self):
        """Save the camera configuration to a json file"""
        # Open folder selection dialog for which file to save to
        file_path = QFileDialog.getSaveFileName(
            self, "Save File", "experiments", "JSON Files (*.json)"
        )
        # save the experiment to a json file

        with open(file_path[0], "w") as config_file:
            config_file.write(json.dumps(asdict(self.get_page_config()), indent=4))

    def load_experiment_config(self):
        """Function to load a camera configuration from a json file"""
        # deinitialise all cameras that are currently running
        file_tuple = QFileDialog.getOpenFileName(
            self, "Open File", "experiments", "JSON Files (*.json)"
        )
        with open(file_tuple[0], "r") as config_file:
            config_data = json.load(config_file)
            config_data["cameras"] = [
                CameraSetupConfig(**camera) for camera in config_data["cameras"]
            ]
        experiment_config = ExperimentConfig(**config_data)
        # Check if the config file is valid
        VALID = self.check_valid_config(experiment_config)
        if VALID:
            # Load the camera configuration
            self.load_from_config_dir(experiment_config)
        else:
            return

    def check_valid_config(self, experiment_config: ExperimentConfig):
        """
        Function to hold the logic for checking if the config file is valid
        """
        # Check if config file contains cameras that are in the database
        for camera in experiment_config.cameras:
            if camera.label not in self.camera_setup_tab.get_setups_labels():
                show_info_message(f"Camera {camera.label} is not connected")
                return False
        else:
            return True

    def load_from_config_dir(self, experiment_config: ExperimentConfig):
        """
        Load the camera configuration from the experiment config dataclass
        """

        # Remove all the cameras that are currently being displayed
        for i in range(len(self.camera_groupboxes)):
            camera = self.camera_groupboxes.pop()
            camera.disconnect()

        # Initialise the cameras from the config file
        for camera in experiment_config.cameras:
            self.initialize_camera_widget(
                label=camera.label, subject_id=camera.subject_id
            )
        # Set the values of the spinbox and encoder selection based on config file
        self.camera_quantity_spin_box.setValue(experiment_config.num_cameras)
        self.encoder_selection.setCurrentText(experiment_config.encoder)
        self.save_dir_textbox.setPlainText(experiment_config.data_dir)
        self.layout_checkbox.setChecked(experiment_config.grid_layout)

    def update_camera_dropdowns(self):
        """Update the camera dropdowns"""
        for camera in self.camera_groupboxes:
            camera.update_camera_dropdown()

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
                if unique_id in [camera.unique_id for camera in self.camera_groupboxes]:
                    camera_widget = [
                        camera
                        for camera in self.camera_groupboxes
                        if camera.unique_id == unique_id
                    ][0]
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
        save_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if save_directory:
            self.save_dir_textbox.setPlainText(save_directory)

    def camera_groupbox_labels(self) -> List[str]:
        """Return the labels of the camera groupboxes"""
        return [camera.label for camera in self.camera_groupboxes]

    def connected_cameras(self) -> List[str]:
        """Return the labels of cameras connected to the PC"""
        return self.camera_setup_tab.get_setups_labels()

    def check_to_enable_global_start_recording(self):
        """Check if all the cameras are ready to start recording. If any camera is not ready to start,
        disable the global start recording button"""
        all_ready = True
        for camera in self.camera_groupboxes:
            if not camera.start_recording_button.isEnabled():
                all_ready = False
                break
        self.start_recording_button.setEnabled(all_ready)

        # If any of the cameras are recording, the 'Change directory' button, 'Change encoder' button, Load Layout button, and change number of cameras should all be grayed out
        any_recording = any(camera.recording for camera in self.camera_groupboxes)
        self.save_dir_button.setEnabled(not any_recording)
        self.encoder_selection.setEnabled(not any_recording)
        self.load_experiment_config_button.setEnabled(not any_recording)
        self.camera_quantity_spin_box.setEnabled(not any_recording)

    def check_to_enable_global_stop_recording(self):
        """Check if any camera is recording. If so enable the stop recording button"""
        any_recording = any(camera.recording for camera in self.camera_groupboxes)
        self.stop_recording_button.setEnabled(any_recording)

        # If any of the cameras are recording, the 'Change directory' button, 'Change encoder' button, Load Layout button, and change number of cameras should all be grayed out
        self.save_dir_button.setEnabled(not any_recording)
        self.encoder_selection.setEnabled(not any_recording)
        self.load_experiment_config_button.setEnabled(not any_recording)
        self.camera_quantity_spin_box.setEnabled(not any_recording)

    def disconnect(self):
        """Disconnect all cameras"""
        while self.camera_groupboxes:
            camera = self.camera_groupboxes.pop()
            camera.disconnect()

    def start_recording(self):
        for camera in self.camera_groupboxes:
            camera.start_recording()

    def stop_recording(self):
        for camera in self.camera_groupboxes:
            camera.stop_recording()

    def refresh(self):
        """Refresh the viewfinder tab"""
        self.check_to_enable_global_start_recording()
        self.check_to_enable_global_stop_recording()
        for camera_label in self.camera_groupboxes:
            camera_label.refresh()

        # Check the setups_changed flag
        if self.camera_setup_tab.setups_changed:
            self.camera_setup_tab.setups_changed = False
            # Handle the renamed cameras
            self.handle_camera_setups_modified()
