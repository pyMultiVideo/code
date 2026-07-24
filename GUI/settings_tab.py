import os
import json
from dataclasses import dataclass, asdict

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QSizePolicy,
    QHeaderView,
    QMessageBox,
    QCheckBox,
)

from config.config import default_camera_config
from .camera_widget import CameraWidget
from .camera_manager import get_camera_ids
from .data_recorder import GPU_AVAILABLE


@dataclass
class CameraSettingsConfig:
    """Represents the CamerasTab settings for one camera"""

    name: str
    unique_id: str
    fps: int
    exposure_time: float
    gain: float
    pixel_format: str
    external_trigger: bool
    downsampling_factor: int


class TableCheckbox(QWidget):
    """Checkbox that is centered in cell when placed in table."""

    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.checkbox = QCheckBox(parent=parent)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.checkbox)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, state):
        self.checkbox.setChecked(state)


class SettingsTab(QWidget):
    """Tab for naming cameras and editing camera-level settings."""

    FFMPEG_ENCODING_SPEED_OPTIONS = ["fast", "medium", "slow"]
    FFMPEG_COMPRESSION_STANDARD_OPTIONS = ["h264", "h265"]

    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent)
        self.GUI = parent
        self.camera_settings_filepath = os.path.join(self.GUI.paths_config["camera_dir"], "camera_configs.json")
        self.ffmpeg_settings_filepath = os.path.join(self.GUI.paths_config["config_dir"], "application_config.json")
        self.setups = {}  # Dict of setups: {Unique_id: Camera_table_item}
        self.preview_showing = False
        self.camera_preview = None  # Place holder for camera preview widget
        self.setups_changed = False  # Flag that is checked for handling camera setups being changed

        # Check if any cameras are connected
        _, CAMERAS_CONNECTED = get_camera_ids()
        if not CAMERAS_CONNECTED:
            warning_box = QMessageBox()
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText("No cameras connected.")
            warning_box.setWindowTitle("Warning")
            warning_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            warning_box.exec()

        # Initialize_camera_groupbox
        self.camera_table_groupbox = QGroupBox("Camera Settings")
        self.camera_table = CameraOverviewTable(parent=self)
        self.camera_table.setMinimumSize(1, 1)
        self.camera_table.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Initialise Refresh button
        self.refresh_layout = QHBoxLayout()
        self.refresh_cameras_button = QPushButton("Refresh camera list")
        self.refresh_cameras_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "refresh.svg")))
        self.refresh_cameras_button.clicked.connect(self.refresh)
        self.refresh_cameras_button.setToolTip("Refresh the list of connected cameras")
        self.refresh_layout.addStretch()
        self.refresh_layout.addWidget(self.refresh_cameras_button)

        self.ffmpeg_groupbox = QGroupBox("FFMPEG Settings")
        self.ffmpeg_layout = QHBoxLayout()

        encoding_backend = "GPU" if GPU_AVAILABLE else "CPU"
        self.ffmpeg_backend_label = QLabel(
            f"Encoder hardware: <span style='color:#1E6FD9; font-weight: bold;'>{encoding_backend}</span>"
        )
        self.ffmpeg_backend_label.setToolTip("Detected from availability of nvidia-smi on this system.")

        self.ffmpeg_crf_label = QLabel("CRF")
        self.ffmpeg_crf_edit = QSpinBox()
        self.ffmpeg_crf_edit.setRange(1, 51)
        self.ffmpeg_crf_edit.setToolTip(
            "Controls video quality vs file size, range [1 - 51], lower values give higher quality and larger files."
        )
        self.ffmpeg_crf_edit.setValue(int(self.GUI.ffmpeg_config["crf"]))

        self.ffmpeg_encoding_speed_label = QLabel("Encoding Speed")
        self.ffmpeg_encoding_speed_edit = QComboBox()
        self.ffmpeg_encoding_speed_edit.addItems(self.FFMPEG_ENCODING_SPEED_OPTIONS)

        self.ffmpeg_encoding_speed_edit.setToolTip("Controls encoding speed vs file size.")
        self.ffmpeg_encoding_speed_edit.setCurrentText(self.GUI.ffmpeg_config["encoding_speed"])

        self.ffmpeg_compression_standard_label = QLabel("Compression")
        self.ffmpeg_compression_standard_edit = QComboBox()
        self.ffmpeg_compression_standard_edit.addItems(self.FFMPEG_COMPRESSION_STANDARD_OPTIONS)
        self.ffmpeg_compression_standard_edit.setCurrentText(self.GUI.ffmpeg_config["compression_standard"])

        self.ffmpeg_layout.addWidget(self.ffmpeg_backend_label)
        self.ffmpeg_layout.addWidget(self.ffmpeg_crf_label)
        self.ffmpeg_layout.addWidget(self.ffmpeg_crf_edit)
        self.ffmpeg_layout.addWidget(self.ffmpeg_encoding_speed_label)
        self.ffmpeg_layout.addWidget(self.ffmpeg_encoding_speed_edit)
        self.ffmpeg_layout.addWidget(self.ffmpeg_compression_standard_label)
        self.ffmpeg_layout.addWidget(self.ffmpeg_compression_standard_edit)

        self.ffmpeg_layout.addStretch()

        self.ffmpeg_groupbox.setLayout(self.ffmpeg_layout)

        self.ffmpeg_crf_edit.valueChanged.connect(self.ffmpeg_crf_changed)
        self.ffmpeg_encoding_speed_edit.currentTextChanged.connect(self.ffmpeg_encoding_speed_changed)
        self.ffmpeg_compression_standard_edit.currentTextChanged.connect(self.ffmpeg_compression_standard_changed)

        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addLayout(self.refresh_layout)
        self.camera_table_layout.addWidget(self.camera_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.ffmpeg_groupbox)
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.page_layout.addStretch()
        self.setLayout(self.page_layout)

        if self.GUI.CLI_args.camera_config is None:
            # Load saved setup info.
            if not os.path.exists(self.camera_settings_filepath):
                self.saved_setups = []
            else:
                with open(self.camera_settings_filepath, "r") as file:
                    cams_list = json.load(file)
                self.saved_setups = [
                    CameraSettingsConfig(**{**default_camera_config, **cam_dict}) for cam_dict in cams_list
                ]
        else:
            # Load saved setups from JSON formatted string
            cams_list = json.loads(self.GUI.CLI_args.camera_config)
            self.saved_setups = [
                CameraSettingsConfig(**{**default_camera_config, **cam_dict}) for cam_dict in cams_list
            ]
        self.refresh()

    # Tab changing logic -------------------------------------------------------------------------------

    def tab_selected(self):
        """Called when tab selected."""
        self.refresh()

    def tab_deselected(self):
        """Called when tab deselected.
        Deinitialise all camera APIs on tab being deselected"""
        for unique_id in self.setups:
            if self.preview_showing:
                self.setups[unique_id].close_preview_camera()

    # FFMPEG Settings methods ---------------------------------------------------------------------------

    def ffmpeg_crf_changed(self, value: int):
        self.GUI.ffmpeg_config["crf"] = int(value)
        self.save_ffmpeg_config()

    def ffmpeg_encoding_speed_changed(self, value: str):
        self.GUI.ffmpeg_config["encoding_speed"] = value
        self.save_ffmpeg_config()

    def ffmpeg_compression_standard_changed(self, value: str):
        self.GUI.ffmpeg_config["compression_standard"] = value
        self.save_ffmpeg_config()

    def save_ffmpeg_config(self):
        """Save current ffmpeg settings to disk."""
        with open(self.ffmpeg_settings_filepath, "w", encoding="utf-8") as f:
            json.dump({"ffmpeg_config": self.GUI.ffmpeg_config}, f, indent=4)

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
        # Remove the saved setup if it is present
        if saved_setup:
            self.saved_setups.remove(saved_setup)
        # Add the setup config to the saved setups list
        self.saved_setups.append(setup.settings)
        # Save any setups in the list of setups
        if self.saved_setups:
            with open(self.camera_settings_filepath, "w") as f:
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
                self.GUI.camera_manager.close(unique_id)
        self.n_setups = len(self.setups.keys())

    def get_camera_labels(self) -> list[str]:
        """Get the labels of the available cameras. Label is the camera's user set name if available, else unique ID."""
        return [setup.get_label() for setup in self.setups.values()]

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        """Get the unique_id of the camera from the label"""
        for setup in self.setups.values():
            if setup.settings.name == camera_label:
                return setup.settings.unique_id
            elif setup.settings.unique_id == camera_label:
                return setup.settings.unique_id
        raise ValueError(f"No camera unique_id found for label: {camera_label}")

    def get_camera_settings_from_label(self, label: str) -> CameraSettingsConfig:
        """Get the camera settings config datastruct from the setups table."""
        for setup in self.setups.values():
            if label in [setup.settings.name, setup.settings.unique_id]:
                return setup.settings
        raise ValueError(f"No camera settings found for label: {label}")


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
            "Downsample Factor",
            "External Trigger",
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

    def __init__(self, setups_table, **kwargs):
        self.settings = CameraSettingsConfig(**kwargs)

        self.setups_table = setups_table
        self.setups_tab = setups_table.setups_tab
        self.setups_tab.preview_showing = False
        self.camera_api = self.setups_tab.GUI.camera_manager.get_or_create(self.settings.unique_id)

        # Name edit
        self.name_edit = QLineEdit()
        if self.settings.name:
            self.name_edit.setText(self.settings.name)
        else:
            self.name_edit.setPlaceholderText("Set a name")
        self.name_edit.textChanged.connect(self.camera_name_changed)

        # ID edit
        self.unique_id_edit = QLineEdit()
        self.unique_id_edit.setReadOnly(True)
        if self.settings.unique_id:
            self.unique_id_edit.setText(self.settings.unique_id)

        # FPS edit
        self.fps_edit = QSpinBox()
        # Set the min and max values of the spinbox
        self.fps_edit.setRange(*self.camera_api.get_frame_rate_range(self.settings.exposure_time))
        self.fps_edit.setEnabled(not self.settings.external_trigger)
        if self.settings.fps:
            self.settings.fps = str(self.settings.fps)
            self.fps_edit.setValue(int(self.settings.fps))
        self.fps_edit.valueChanged.connect(self.camera_fps_changed)

        # Exposure time edit
        self.exposure_time_edit = QSpinBox()
        self.exposure_time_edit.setSingleStep(100)
        self.exposure_time_edit.setRange(*self.camera_api.get_exposure_time_range(self.settings.fps))
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
        self.settings.pixel_format = self.camera_api.pixel_format.name

        # Configure what settings are available manual camera control is not enabled
        if self.camera_api.manual_control_enabled:
            # Connect functions is camera control enabled
            self.exposure_time_edit.valueChanged.connect(self.camera_exposure_time_changed)
            self.gain_edit.valueChanged.connect(self.camera_gain_changed)
            # Connect the Set range functions
            self.exposure_time_edit.setRange(*self.camera_api.get_exposure_time_range(self.settings.fps))
            self.gain_edit.setRange(*self.camera_api.get_gain_range())
        else:  # The edit boxes are not enabled if no function is connected
            self.exposure_time_edit.setEnabled(False)
            self.gain_edit.setEnabled(False)

        # Downsampling factor edit
        self.downsampling_factor_edit = QComboBox()
        self.downsampling_factor_edit.addItems(["1", "2", "4"])
        if self.settings.downsampling_factor:
            self.downsampling_factor_edit.setCurrentText(str(self.settings.downsampling_factor))
        self.downsampling_factor_edit.activated.connect(self.camera_downsampling_factor_changed)

        self.external_trigger_checkbox = TableCheckbox()
        if self.settings.external_trigger:
            self.external_trigger_checkbox.setChecked(bool(self.settings.external_trigger))
        self.external_trigger_checkbox.checkbox.stateChanged.connect(self.camera_external_trigger_changed)

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
        self.setups_table.setCellWidget(0, 5, self.downsampling_factor_edit)
        self.setups_table.setCellWidget(0, 6, self.external_trigger_checkbox)
        self.setups_table.setCellWidget(0, 7, self.preview_camera_button)

    # Helper function

    def current_camera_preview_showing(self):
        """Check if the preview is currently showing for this camera."""
        if self.setups_tab.preview_showing:
            return self.setups_tab.camera_preview.label == self.get_label()
        return False

    # Attribute Changed Functions -----------------------------------------------------------------

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
        if self.current_camera_preview_showing():
            self.setups_tab.camera_preview.update_viewfinder_text()

    def get_label(self):
        """Return name if defined else unique ID."""
        return self.settings.name if self.settings.name else self.settings.unique_id

    # Camera Parameters Changed--------------------------------------------------------------------

    def camera_fps_changed(self):
        """Called when fps text of setup is edited."""
        self.settings.fps = int(self.fps_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.current_camera_preview_showing():
            self.setups_tab.camera_preview.camera_api.set_frame_rate(self.settings.fps)
        self.exposure_time_edit.setRange(*self.camera_api.get_exposure_time_range(self.settings.fps))

    def camera_exposure_time_changed(self):
        """"""
        self.settings.exposure_time = int(self.exposure_time_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.current_camera_preview_showing():
            self.setups_tab.camera_preview.camera_api.set_exposure_time(self.settings.exposure_time)
        self.fps_edit.setRange(*self.camera_api.get_frame_rate_range(self.settings.exposure_time))

    def camera_gain_changed(self):
        """"""
        self.settings.gain = float(self.gain_edit.text())
        self.setups_tab.update_saved_setups(setup=self)
        if self.current_camera_preview_showing():
            self.setups_tab.camera_preview.camera_api.set_gain(self.settings.gain)

    def camera_external_trigger_changed(self):
        """Change if the camera is"""
        self.settings.external_trigger = self.external_trigger_checkbox.isChecked()
        self.setups_tab.update_saved_setups(setup=self)
        # Restart the preview if open
        if self.current_camera_preview_showing():
            self.setups_tab.camera_preview.camera_api.set_acqusition_mode(self.settings.external_trigger)
            self.setups_tab.camera_preview.update_viewfinder_text()
        # FPS spin box only enabled if external trigger not enabled.
        self.fps_edit.setEnabled(not self.settings.external_trigger)

    # FFMPEG Parameters ---------------------------------------------------------------------------

    def camera_downsampling_factor_changed(self):
        """Called when the downsampling factor of the seutp is edited"""
        self.settings.downsampling_factor = int(self.downsampling_factor_edit.currentText())
        self.setups_tab.update_saved_setups(setup=self)

    # Camera preview functions --------------------------------------------------------------------

    def open_preview_camera(self):
        """Button to preview the camera in the row"""
        self.setups_tab.refresh()
        if self.setups_tab.preview_showing:
            self.close_preview_camera()
        self.setups_tab.camera_preview = CameraWidget(self.setups_tab, label=self.get_label(), preview_mode=True)
        self.setups_tab.page_layout.addWidget(self.setups_tab.camera_preview)
        self.setups_tab.preview_showing = True

    def close_preview_camera(self):
        self.setups_tab.camera_preview.close()
        self.setups_tab.preview_showing = False
