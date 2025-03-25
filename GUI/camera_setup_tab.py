import os
import json
from dataclasses import dataclass, asdict

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QSizePolicy,
    QHeaderView,
    QMessageBox,
)

from config.config import paths_config, default_camera_config
from .camera_widget import CameraWidget
from camera_api import get_camera_ids, init_camera_api_from_module


@dataclass
class CameraSettingsConfig:
    """Represents the CamerasTab settings for one camera"""

    name: str
    unique_id: str
    fps: int
    exposure_time: float
    gain: float
    pixel_format: str
    downsampling_factor: int


class CamerasTab(QWidget):
    """Tab for naming cameras and editing camera-level settings."""

    def __init__(self, parent=None):
        super(CamerasTab, self).__init__(parent)
        self.GUI = parent
        self.saved_setups_filepath = os.path.join(paths_config["camera_dir"], "camera_configs.json")
        self.setups = {}  # Dict of setups: {Unique_id: Camera_table_item}
        self.preview_showing = False
        # Check if any cameras are connected
        _, NO_CAMERAS_CONNECTED = get_camera_ids()
        if NO_CAMERAS_CONNECTED:
            warning_box = QMessageBox()
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText("No cameras connected.")
            warning_box.setWindowTitle("Warning")
            warning_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            warning_box.exec()
        # Initialize_camera_groupbox
        self.camera_table_groupbox = QGroupBox("Camera Table")
        self.camera_table = CameraOverviewTable(parent=self)
        self.camera_table.setMinimumSize(1, 1)
        self.camera_table.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Initialise Refresh button
        self.refresh_layout = QHBoxLayout()
        self.refresh_cameras_button = QPushButton("Refresh camera list")
        self.refresh_cameras_button.setIcon(QIcon(os.path.join(paths_config["icons_dir"], "refresh.svg")))
        self.refresh_cameras_button.clicked.connect(self.refresh)
        self.refresh_cameras_button.setToolTip("Refresh the list of connected cameras")
        self.refresh_layout.addStretch()
        self.refresh_layout.addWidget(self.refresh_cameras_button)

        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.camera_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addLayout(self.refresh_layout)
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.page_layout)

        # Load saved setup info.
        if not os.path.exists(self.saved_setups_filepath):
            self.saved_setups = []
        else:
            with open(self.saved_setups_filepath, "r") as file:
                cams_list = json.load(file)
            self.saved_setups = [CameraSettingsConfig(**cam_dict) for cam_dict in cams_list]

        self.refresh()
        self.setups_changed = False

    # Refresh timer / tab changing logic -------------------------------------------------------------------------------

    def tab_selected(self):
        """Called when tab selected."""
        self.refresh()

    def tab_deselected(self):
        """Called when tab deselected."""
        # Deinitialise all camera APIs on tab being deselected
        for unique_id in self.setups:
            if self.preview_showing:
                self.setups[unique_id].close_preview_camera()
            self.setups[unique_id].camera_api.stop_capturing()

    # Reading / Writing the Camera setups saved function --------------------------------------------------------

    def get_saved_setup(self, unique_id: str = None, name: str = None) -> CameraSettingsConfig:
        """Get a saved CameraSettingsConfig object from a name or unique_id from self.saved_setups."""
        if unique_id:
            try:
                return next(setup for setup in self.saved_setups if setup.unique_id == unique_id)
            except StopIteration:
                pass
        if name:
            try:
                return next(setup for setup in self.saved_setups if setup.name == name)
            except StopIteration:
                pass
        return None

    def update_saved_setups(self, setup):
        """Updates the saved setups"""
        saved_setup = self.get_saved_setup(unique_id=setup.settings.unique_id)
        # if saved_setup == setup.settings:
        #     return
        if saved_setup:
            self.saved_setups.remove(saved_setup)
        # if the setup has a name
        # if setup.settings.label:
        # add the setup config to the saved setups list
        self.saved_setups.append(setup.settings)
        # Save any setups in the list of setups
        if self.saved_setups:
            with open(self.saved_setups_filepath, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_setups], f, indent=4)

    def refresh(self):
        """Check for new and removed cameras and updates the setups table."""
        connected_cameras, _ = get_camera_ids()
        if not connected_cameras == self.setups.keys():
            # Add any new cameras setups to the setups (comparing unique_ids)
            for unique_id in set(connected_cameras) - set(self.setups.keys()):
                # Check if this unique_id has been seen before by looking in the saved setups database
                camera_settings_config: CameraSettingsConfig = self.get_saved_setup(unique_id=unique_id)
                if camera_settings_config:
                    # Instantiate the setup and add it to the setups dict
                    self.setups[unique_id] = Camera_table_item(self.camera_table, **asdict(camera_settings_config))
                else:  # unique_id has not been seen before, create a new setup
                    self.setups[unique_id] = Camera_table_item(
                        self.camera_table, **default_camera_config, unique_id=unique_id
                    )
                self.update_saved_setups(self.setups[unique_id])
            # Remove any setups that are no longer connected
            for unique_id in set(self.setups.keys()) - set(connected_cameras):
                # Sequence for removed a setup from the table (and deleting it)
                self.setups.pop(unique_id)
                self.camera_table.remove(unique_id)
        self.n_setups = len(self.setups.keys())

    def get_camera_labels(self) -> list[str]:
        """Get the labels of the available cameras. The label is the camera's user set name if available, else unique ID."""
        return [setup.get_label() for setup in self.setups.values()]

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        """Get the unique_id of the camera from the label"""
        for setup in self.setups.values():
            if setup.settings.name == camera_label:
                return setup.settings.unique_id
            elif setup.settings.unique_id == camera_label:
                return setup.settings.unique_id
        return None

    def get_camera_settings_from_label(self, label: str) -> CameraSettingsConfig:
        """Get the camera settings config datastruct from the setups table."""
        for setup in self.setups.values():
            if setup.settings.name is None:
                query_label = setup.settings.unique_id
            else:
                query_label = setup.settings.name
            if query_label == label:
                return setup.settings
        return None


class CameraOverviewTable(QTableWidget):
    """Table for displaying information and setting for connected cameras."""

    def __init__(self, parent=None):
        super(CameraOverviewTable, self).__init__(parent)
        self.setups_tab = parent
        self.header_names = [
            "Name",
            "Unique ID",
            "FPS",
            "Exposure (μs)",
            "Gain (dB)",
            "Pixel Format",
            "Downsample Factor",
            "Camera Preview",
        ]
        self.setColumnCount(len(self.header_names))
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)

        self.setHorizontalHeaderLabels(self.header_names)
        for i in range(len(self.header_names)):
            resize_mode = QHeaderView.ResizeMode.Stretch if i < 2 else QHeaderView.ResizeMode.ResizeToContents
            self.horizontalHeader().setSectionResizeMode(i, resize_mode)

    def remove(self, unique_id):
        for row in range(self.rowCount()):
            if self.cellWidget(row, 1).text() == unique_id:
                self.removeRow(row)
                break


class Camera_table_item:
    """Class representing single camera in the Camera Tab table."""

    def __init__(self, setups_table, name, unique_id, fps, exposure_time, gain, pixel_format, downsampling_factor):
        self.settings = CameraSettingsConfig(
            name=name,
            unique_id=unique_id,
            fps=fps,
            downsampling_factor=downsampling_factor,
            exposure_time=exposure_time,
            gain=gain,
            pixel_format=pixel_format,
        )

        self.setups_table = setups_table
        self.setups_tab = setups_table.setups_tab
        self.setups_tab.preview_showing = False
        self.camera_api = init_camera_api_from_module(settings=self.settings)

        # Name edit
        self.name_edit = QLineEdit()
        if self.settings.name:
            self.name_edit.setText(self.settings.name)
        else:
            self.name_edit.setPlaceholderText("Set a name")
        self.name_edit.editingFinished.connect(self.camera_name_changed)

        # ID edit
        self.unique_id_edit = QLineEdit()
        self.unique_id_edit.setReadOnly(True)
        if self.settings.unique_id:
            self.unique_id_edit.setText(self.settings.unique_id)

        # FPS edit
        self.fps_edit = QSpinBox()
        # Set the min and max values of the spinbox
        self.fps_edit.setRange(*self.camera_api.get_frame_rate_range(self.settings.exposure_time))
        self.fps_edit.setMaximum(120)
        if self.settings.fps:
            self.settings.fps = str(self.settings.fps)
            self.fps_edit.setValue(int(self.settings.fps))
        self.fps_edit.valueChanged.connect(self.camera_fps_changed)

        # Exposure time edit
        self.exposure_time_edit = QSpinBox()
        self.exposure_time_edit.setSingleStep(100)
        self.exposure_time_edit.setValue(self.settings.exposure_time)
        self.exposure_time_edit.setEnabled(self.camera_api.manual_control_enabled)
        if self.settings.exposure_time:
            self.exposure_time_edit.setValue(int(self.settings.exposure_time))

        # Gain edit
        self.gain_edit = QSpinBox()
        self.gain_edit.setValue(int(self.settings.gain))
        if self.settings.gain:
            self.gain_edit.setValue(int(self.settings.gain))

        self.gain_edit.setEnabled(self.camera_api.manual_control_enabled)
        # Pixel format edit
        self.pixel_format_edit = QComboBox()
        self.pixel_format_edit.addItem(self.camera_api.pixel_format)
        if self.settings.pixel_format:
            self.pixel_format_edit.setCurrentText(self.settings.pixel_format)

        # Configure what settings are available manual camera control is not enabled
        if self.camera_api.manual_control_enabled:
            # Connect functions is camera control enabled
            self.pixel_format_edit.activated.connect(self.camera_pixel_format_changed)
            self.exposure_time_edit.valueChanged.connect(self.camera_exposure_time_changed)
            self.gain_edit.valueChanged.connect(self.camera_gain_changed)
            # Connect the Set range functions
            self.exposure_time_edit.setRange(*self.camera_api.get_exposure_time_range(self.settings.fps))
            self.gain_edit.setRange(*self.camera_api.get_gain_range())
        else:  # The edit boxes are not enabled if no function is connected
            self.pixel_format_edit.setEnabled(False)
            self.exposure_time_edit.setEnabled(False)
            self.gain_edit.setEnabled(False)

        # Downsampling factor edit
        self.downsampling_factor_edit = QComboBox()
        self.downsampling_factor_edit.addItems(["1", "2", "4"])
        if self.settings.downsampling_factor:
            self.downsampling_factor_edit.setCurrentText(str(self.settings.downsampling_factor))
        self.downsampling_factor_edit.activated.connect(self.camera_downsampling_factor_changed)

        # Preview button.
        self.preview_camera_button = QPushButton("Preview")
        self.preview_camera_button.clicked.connect(self.open_preview_camera)
        self.preview_camera_button.setToolTip(
            f"Preview camera: {self.settings.name if self.settings.name is not None else self.settings.unique_id}"
        )

        # Populate the table
        self.setups_table.insertRow(0)
        self.setups_table.setCellWidget(0, 0, self.name_edit)
        self.setups_table.setCellWidget(0, 1, self.unique_id_edit)
        self.setups_table.setCellWidget(0, 2, self.fps_edit)
        self.setups_table.setCellWidget(0, 3, self.exposure_time_edit)
        self.setups_table.setCellWidget(0, 4, self.gain_edit)
        self.setups_table.setCellWidget(0, 5, self.pixel_format_edit)
        self.setups_table.setCellWidget(0, 6, self.downsampling_factor_edit)
        self.setups_table.setCellWidget(0, 7, self.preview_camera_button)

    def camera_name_changed(self):
        """Called when name text of setup is edited."""
        name = str(self.name_edit.text())
        if name and name not in [
            setup.settings.name
            for setup in self.setups_tab.setups.values()
            if setup.settings.unique_id != self.settings.unique_id
        ]:
            self.settings.name = name
        else:
            self.settings.name = None
            self.name_edit.setText("")
            self.name_edit.setPlaceholderText("Set a name")
        self.setups_tab.update_saved_setups(setup=self)
        self.setups_tab.setups_changed = True

    def get_label(self):
        """Return name if defined else unique ID."""
        return self.settings.name if self.settings.name else self.settings.unique_id

    # Camera Parameters --------------------------------------------------------------------------

    def camera_fps_changed(self):
        """Called when fps text of setup is edited."""
        self.settings.fps = int(self.fps_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_frame_rate(self.settings.fps)
        self.exposure_time_edit.setRange(*self.camera_api.get_exposure_time_range(self.settings.fps))

    def camera_exposure_time_changed(self):
        """"""
        self.settings.exposure_time = int(self.exposure_time_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_exposure_time(self.settings.exposure_time)
        self.fps_edit.setRange(*self.camera_api.get_frame_rate_range(self.settings.exposure_time))

    def camera_gain_changed(self):
        """"""
        self.settings.gain = float(self.gain_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_gain(self.settings.gain)

    def camera_pixel_format_changed(self):
        """Change the pixel format"""
        self.settings.pixel_format = self.pixel_format_edit.currentText()
        self.setups_tab.update_saved_setups(setup=self)
        if self.setups_tab.preview_showing:
            self.setups_tab.camera_preview.camera_api.set_pixel_format(self.settings.pixel_format)

    # FFMPEG Parameters -----------------------------------------------------------------------

    def camera_downsampling_factor_changed(self):
        """Called when the downsampling factor of the seutp is edited"""
        self.settings.downsampling_factor = int(self.downsampling_factor_edit.currentText())
        self.setups_tab.update_saved_setups(setup=self)

    # Camera preview functions -----------------------------------------------------------------------

    def open_preview_camera(self):
        """Button to preview the camera in the row"""
        self.setups_tab.refresh()
        if self.setups_tab.preview_showing:
            self.close_preview_camera()
        self.setups_tab.camera_preview = CameraWidget(self.setups_tab, self.get_label(), preview_mode=True)
        self.setups_tab.camera_preview.begin_capturing()
        self.setups_tab.page_layout.addWidget(self.setups_tab.camera_preview)
        self.setups_tab.preview_showing = True

    def close_preview_camera(self):
        self.setups_tab.camera_preview.close()
        self.setups_tab.preview_showing = False
