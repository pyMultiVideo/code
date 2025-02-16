import json
import os
import PyQt6.QtWidgets as QtWidgets
from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QTableWidget,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
)
from dataclasses import asdict

from config.config import ffmpeg_config, paths_config
from .utility import CameraSettingsConfig, find_all_cameras, load_saved_setups, load_camera_dict
from .preview_dialog import CameraPreviewDialog


class CamerasTab(QtWidgets.QWidget):
    """Tab for naming cameras and editing camera-level settings."""

    def __init__(self, parent=None):
        super(CamerasTab, self).__init__(parent)
        self.GUI = parent
        self.paths = paths_config
        self.saved_setups_file = os.path.join(self.paths["camera_dir"], "camera_configs.json")
        self.setups = {}  # Dict of setups: {Unique_id: Camera_table_item}

        # Initialize_camera_groupbox
        self.camera_table_groupbox = QGroupBox("Camera Table")
        self.camera_table = CameraOverviewTable(parent=self)

        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.camera_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)

        self.page_layout = QVBoxLayout()
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.page_layout)

        # Get a list of the saved setups from the database
        self.saved_setups = load_saved_setups(load_camera_dict(camera_config_path=self.saved_setups_file))
        self.ffmpeg_config: dict = ffmpeg_config
        self.refresh()
        self.setups_changed = False

    def get_saved_setups(self, unique_id: str = None, name: str = None) -> CameraSettingsConfig:
        """Get a saved Setup_info object from a name or unique_id from self.saved_setups."""
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
        """Called when a setup is updated to update the saved setups"""
        saved_setup = self.get_saved_setups(unique_id=setup.unique_id)
        camera_settings_config = setup.getCameraSettingsConfig()
        if saved_setup == camera_settings_config:
            return
        # if the setup has a name
        if saved_setup:
            self.saved_setups.remove(saved_setup)
        if setup.label:
            # add the setup config to the saved setups list
            self.saved_setups.append(setup.getCameraSettingsConfig())
        if self.saved_setups:
            with open(self.saved_setups_file, "w") as f:
                json.dump([asdict(setup) for setup in self.saved_setups], f, indent=4)

    def refresh(self):
        """Check for new and removed cameras and updates the setups table."""
        connected_cameras = find_all_cameras()
        if not connected_cameras == self.setups.keys():
            # Add any new cameras setups to the setups (comparing unique_ids)
            for unique_id in set(connected_cameras) - set(self.setups.keys()):
                # Check if this unique_id has been seen before by looking in the saved setups database
                camera_settings_config: CameraSettingsConfig = self.get_saved_setups(unique_id=unique_id)
                if camera_settings_config:
                    # Instantiate the setup and add it to the setups dict
                    self.setups[unique_id] = Camera_table_item(
                        setups_table=self.camera_table,
                        name=camera_settings_config.name,
                        unique_id=camera_settings_config.unique_id,
                        fps=camera_settings_config.fps,
                        pxl_fmt=camera_settings_config.pxl_fmt,
                        downsampling_factor=camera_settings_config.downsample_factor,
                    )
                else:  # unique_id has not been seen before, create a new setup
                    self.setups[unique_id] = Camera_table_item(
                        setups_table=self.camera_table,
                        name=None,
                        unique_id=unique_id,
                        fps="30",
                        pxl_fmt="yuv420p",
                        downsampling_factor=1,
                    )

                self.update_saved_setups(self.setups[unique_id])

            # Remove any setups that are no longer connected
            for unique_id in set(self.setups.keys()) - set(connected_cameras):
                # Sequence for removed a setup from the table (and deleting it)
                self.setups.pop(unique_id)
                self.camera_table.remove(unique_id)

    def get_setups_labels(self) -> list[str]:
        """Function to get the labels of the setups"""
        return [setup.label for setup in self.setups.values()]

    def get_camera_labels(self) -> list[str]:
        """Function to get the names of the cameras if they exist. if they have not been named, use the unique_id"""
        return sorted([setup.label if setup.label else setup.unique_id for setup in self.setups.values()])

    def get_camera_unique_ids(self) -> list[str]:
        """Function to get the unique_ids of the cameras"""
        return sorted([setup.unique_id for setup in self.setups.values()])

    def setups_recording_status_dict(self) -> dict[str, bool]:
        """
        Function to get the recording status of the camera from the label.
        Returns:
            dict[str, bool]: Dictionary of the camera labels and their recording status
        """
        recording_status = {}
        for setup in self.setups.values():
            camera_object = [
                camera.camera_object
                for camera in self.GUI.viewfinder_tab.camera_groupboxes
                if camera.unique_id == setup.unique_id
            ]
            for camera_object in camera_object:
                recording_status[setup.label] = camera_object.is_Recording()
        return recording_status

    def get_camera_unique_id_from_label(self, camera_label: str) -> str:
        """Function to get the unique_id of the camera from the label"""
        for setup in self.setups.values():
            if setup.label == camera_label:
                return setup.unique_id
            elif setup.unique_id == camera_label:
                return setup.unique_id
        return None

    def getCameraSettingsConfig(self, label: str) -> CameraSettingsConfig:
        """Get the camera settings config datastruct from the setups table."""
        for setup in self.setups.values():
            if setup.label == label:
                return setup.getCameraSettingsConfig()
        return None


class CameraOverviewTable(QTableWidget):
    """Table for displaying information and setting for connected cameras."""

    def __init__(self, parent=None):
        super(CameraOverviewTable, self).__init__(parent)
        self.setups_tab = parent
        self.paths = paths_config
        # Set the camera table to the camera_table in the database
        self.camera_dict = load_camera_dict(os.path.join(self.paths["config_dir"], "camera_configs.json"))
        # Configure the camera table
        self.header_names = ["Name", "Unique ID", "FPS", "Pxl Fmt", "Downsample Factor", "Camera Preview"]
        self.setColumnCount(len(self.header_names))
        self.setRowCount(len(self.camera_dict))
        self.verticalHeader().setVisible(False)

        self.setHorizontalHeaderLabels(self.header_names)
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def remove(self, unique_id):
        for row in range(self.rowCount()):
            if self.cellWidget(row, 1).text() == unique_id:
                self.removeRow(row)
                break


class Camera_table_item:
    """Class representing single camera in the Camera Tab table."""

    def __init__(self, setups_table, name, unique_id, fps, pxl_fmt, downsampling_factor):
        self.setups_table = setups_table
        self.setups_tab = setups_table.setups_tab
        self.gui = self.setups_tab.GUI
        self.label = name
        self.unique_id = unique_id
        self.fps = (fps,)
        self.pxl_fmt = pxl_fmt
        self.downsampling_factor = downsampling_factor

        self.label = self.label if self.label is not None else self.unique_id

        # Name edit
        self.name_edit = QLineEdit()
        if self.label:
            self.name_edit.setText(self.label)
        self.name_edit.editingFinished.connect(self.camera_name_changed)

        # ID edit
        self.unique_id_edit = QLineEdit()
        self.unique_id_edit.setReadOnly(True)
        if self.unique_id:
            self.unique_id_edit.setText(self.unique_id)

        # FPS edit
        self.fps_edit = QSpinBox()
        # Set the min and max values of the spinbox
        self.fps_edit.setRange(1, 120)
        self.fps_edit.setMaximum(120)
        if self.fps:
            self.fps = str(self.fps[0])
            self.fps_edit.setValue(int(self.fps))
        self.fps_edit.editingFinished.connect(self.camera_fps_changed)

        # Pxl format edit
        self.pxl_fmt_edit = QLineEdit()
        if self.pxl_fmt:
            self.pxl_fmt_edit.setText(self.pxl_fmt)
        self.pxl_fmt_edit.editingFinished.connect(self.camera_pxl_fmt_changed)

        # Downsampling factor edit
        self.downsampling_factor_edit = QComboBox()
        self.downsampling_factor_edit.addItems(["1", "2", "4", "8"])
        if self.downsampling_factor:
            self.downsampling_factor_edit.setCurrentText(str(self.downsampling_factor))
        self.downsampling_factor_edit.activated.connect(self.camera_downsampling_factor)

        # Preview button.
        self.preview_camera_button = QPushButton("Preview")
        self.preview_camera_button.clicked.connect(self.preview_camera)

        self.setups_table.insertRow(0)
        self.setups_table.setCellWidget(0, 0, self.name_edit)
        self.setups_table.setCellWidget(0, 1, self.unique_id_edit)
        self.setups_table.setCellWidget(0, 2, self.fps_edit)
        self.setups_table.setCellWidget(0, 3, self.pxl_fmt_edit)
        self.setups_table.setCellWidget(0, 4, self.downsampling_factor_edit)
        self.setups_table.setCellWidget(0, 5, self.preview_camera_button)

    def camera_name_changed(self):
        """Called when name text of setup is edited."""
        self.label = str(self.name_edit.text())
        self.label = self.label if self.label else self.unique_id
        if self.label == "_hidden_":
            self.name_edit.setStyleSheet("color: grey;")
        else:
            self.name_edit.setStyleSheet("color: black;")
        self.setups_tab.update_saved_setups(setup=self)
        self.setups_tab.setups_changed = True

    def camera_fps_changed(self):
        """Called when fps text of setup is edited."""
        self.fps = str(self.fps_edit.text())
        self.setups_tab.update_saved_setups(setup=self)

    def camera_pxl_fmt_changed(self):
        """Called when pixel format text of setup is edited."""
        self.pxl_fmt = str(self.pxl_fmt_edit.text())
        self.setups_tab.update_saved_setups(setup=self)

    def camera_downsampling_factor(self):
        """Called when the downsampling factor of the seutp is edited"""
        self.downsampling_factor = int(self.downsampling_factor_edit.currentText())
        self.setups_tab.update_saved_setups(setup=self)

    def preview_camera(self):
        """Button to preview the camera in the row"""
        camera_preview = CameraPreviewDialog(
            gui=self.gui, unique_id=self.unique_id, window_title=f"Camera {self.unique_id}"
        )
        camera_preview.exec()

    def getCameraSettingsConfig(self):
        """Get the camera settings config datastruct from the setups table."""
        return CameraSettingsConfig(
            name=self.label,
            unique_id=self.unique_id,
            fps=self.fps,
            pxl_fmt=self.pxl_fmt,
            downsample_factor=self.downsampling_factor,
        )
