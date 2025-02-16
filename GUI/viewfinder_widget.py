import os
import csv
import json
import subprocess
import logging
import numpy as np
from datetime import datetime
from collections import deque

import pyqtgraph as pg
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tools import cbox_update_options
from tools import CameraSetupConfig
from tools import init_camera_api
from config import ffmpeg_config_dict
from config import gui_config_dict
from config import paths_config_dict


class ViewfinderWidget(QWidget):
    """Widget for displaying camera video and camera controls."""

    def __init__(self, parent, label, subject_id):
        super(ViewfinderWidget, self).__init__(parent)
        self.video_capture_tab = parent
        self.GUI = self.video_capture_tab.GUI
        self.camera_setup_tab = self.video_capture_tab.GUI.camera_setup_tab
        self.logger = logging.getLogger(__name__)
        self.paths = paths_config_dict
        # Camera attributes
        self.label = label
        self.subject_id = subject_id
        if self.label in self.camera_setup_tab.get_camera_labels():
            self.camera_settings = self.camera_setup_tab.getCameraSettingsConfig(self.label)
        self.fps = self.camera_settings.fps
        self.pxl_fmt = self.camera_settings.pxl_fmt
        self.unique_id = self.camera_settings.unique_id
        self.downsampling_factor = 1

        self.camera_api = init_camera_api(self.unique_id, self.camera_settings)
        self.cam_width = self.camera_api.get_width()
        self.cam_height = self.camera_api.get_height()

        # Video display

        self.video_feed = pg.ImageView()
        self.video_feed.ui.histogram.hide()
        self.video_feed.ui.roiBtn.hide()
        self.video_feed.ui.menuBtn.hide()
        self.video_feed.view.setMouseEnabled(x=False, y=False)  # Disable zoom and pan

        # Recording Information overlay
        self.recording_status_item = pg.TextItem()
        self.recording_status_item.setPos(10, 10)
        self.video_feed.addItem(self.recording_status_item)
        self.recording_status_item.setText("NOT RECORDING", color="r")

        self.recording_time_text = pg.TextItem()
        self.recording_time_text.setPos(200, 10)
        self.video_feed.addItem(self.recording_time_text)
        self.recording_time_text.setText("", color="r")

        # GPIO state overlay
        self.gpio_state_smoothed = np.zeros(3)
        self.gpio_status_item = pg.TextItem()
        self.gpio_status_font = QFont()
        self.gpio_status_item.setPos(10, 70)
        self.video_feed.addItem(self.gpio_status_item)
        self.gpio_status_item.setText("GPIO state", color="blue")
        self.gpio_status_indicators = [pg.TextItem() for _ in range(3)]
        self.gpio_status_font = QFont()
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setPos(150 + i * 30, 70)
            self.video_feed.addItem(gpio_indicator)

        # Framerate overlay
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 40)
        self.video_feed.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        self.camera_setup_groupbox = QGroupBox(f"{self.label}")

        # Subject ID text edit
        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.subject_id)
        self.subject_id_text.textChanged.connect(self.update_subject_id)

        # Record button.
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "record.svg")))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setEnabled(False)
        self.start_recording_button.clicked.connect(self.start_recording)

        # Stop button.
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "stop.svg")))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.clicked.connect(self.stop_recording)

        # Camera select dropdown
        self.camera_id_label = QLabel("Camera ID:")
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        self.update_camera_dropdown()
        self.camera_dropdown.setCurrentText(self.label)

        # Layout
        self.camera_header_layout = QHBoxLayout()
        self.camera_header_layout.addWidget(self.camera_id_label)
        self.camera_header_layout.addWidget(self.camera_dropdown)
        self.camera_header_layout.addWidget(self.subject_id_label)
        self.camera_header_layout.addWidget(self.subject_id_text)
        self.camera_header_layout.addWidget(self.start_recording_button)
        self.camera_header_layout.addWidget(self.stop_recording_button)

        self.camera_setup_groupbox.setLayout(self.camera_header_layout)
        self.camera_setup_groupbox.setFixedHeight(75)

        self.camera_setup_hlayout = QVBoxLayout()
        self.camera_setup_hlayout.addWidget(self.camera_setup_groupbox)
        self.camera_setup_hlayout.addWidget(self.video_feed)

        self.setLayout(self.camera_setup_hlayout)

        self._begin_capturing()

    # Camera interaction --------------------------------------------------------------

    def _begin_capturing(self):
        """Start streaming video from camera."""
        self.recording = False
        self.width = self.cam_width
        self.height = self.cam_height
        self.validate_subject_id_input()
        self.frame_timestamps = deque(maxlen=10)
        self.camera_api.begin_capturing()

    def fetch_image_data(self) -> None:
        """Get images and associated data from camera and save to disk if recording."""
        new_images = self.camera_api.get_available_images()
        if new_images == None:
            return
        # Store first image and GPIO state for display update.
        self._image_data = new_images["images"][0]
        self._GPIO_data = new_images["gpio_data"][0]
        self.frame_timestamps.extend(new_images["timestamps"])
        # Record data to disk.
        if self.recording is True:
            self.save_image_data(new_images)

    # Video display -------------------------------------------------------------------

    def display_frame(self):
        """Display most recent image and call functions to add information overlays."""
        self.video_feed.setImage(self._image_data.T)
        self.display_recording_status()
        self.display_average_frame_rate()
        self.display_recording_time()
        self.display_gpio_state()

    def display_average_frame_rate(self):
        """Compute average framerate and display over image in green if OK else red."""
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (self.frame_timestamps.maxlen - 1)
        calculated_framerate = 1e9 / avg_time_diff
        color = "r" if (abs(calculated_framerate - int(self.fps)) > 1) else "g"
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)

    def display_recording_time(self):
        """Display the current recording duration over image."""
        if self.recording:
            elapsed_time = datetime.now() - self.record_start_time
            self.recording_time_text.setText(str(elapsed_time).split(".")[0], color="g")
        else:
            self.recording_time_text.setText("", color="r")

    def display_recording_status(self):
        """Set recording status text to match recording status."""
        if self.recording is True:
            status = "RECORDING"
            color = "g"
        elif self.recording is False:
            status = "NOT RECORDING"
            color = "r"
        self.recording_status_item.setText(status, color=color)

    def display_gpio_state(self, decay=0.5):
        """Update GPIO status indicators."""
        self.gpio_state_smoothed = decay * self.gpio_state_smoothed
        self.gpio_state_smoothed[np.array(self._GPIO_data) > 0] = 1
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setText("\u2b24", color=[0, 0, self.gpio_state_smoothed[i] * 255])

    def display_font_size_update(self, scale_factor = 0.01):
        """Update the size of the GUI text elements"""        
        font_size = int(min(self.GUI.width(), self.GUI.height()) * scale_factor)

        # Update GUI elements to font size
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setFont(QFont("Arial", font_size))
        self.gpio_status_item.setFont(QFont("Arial", font_size))
        self.recording_status_item.setFont(QFont("Arial", font_size))
        self.recording_time_text.setFont(QFont("Arial", font_size))
        self.frame_rate_text.setFont(QFont("Arial", font_size))
    
    # GUI element updates -------------------------------------------------------------

    def refresh(self):
        """refresh the camera widget"""
        self.update_camera_dropdown()
        
    def resizeEvent(self, event):
        """Called on Widget resize"""
        self.display_font_size_update()
        super().resizeEvent(event)

    def update_camera_dropdown(self):
        """Update the cameras available in the camera select dropdown menu."""
        self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        cbox_update_options(
            cbox=self.camera_dropdown,
            options=self.camera_setup_tab.get_camera_labels(),
            used_cameras_labels=list([cam.label for cam in self.video_capture_tab.camera_groupboxes]),
            selected=self.label,
        )
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)

    def update_subject_id(self):
        self.subject_id = self.subject_id_text.toPlainText()
        self.validate_subject_id_input()

    def validate_subject_id_input(self):
        """Change the colour of the subject ID text field"""
        if self.subject_id_text.toPlainText() == "":
            self.start_recording_button.setEnabled(False)
        else:
            self.start_recording_button.setEnabled(True)

    def toggle_control_visibility(self) -> None:
        """Toggle the visibility of the camera controls."""
        is_visible = self.camera_setup_groupbox.isVisible()
        self.camera_setup_groupbox.setVisible(not is_visible)

    # Data file interaction -----------------------------------------------------------

    def start_recording(self) -> None:
        """Start recording video to disk."""
        # Create Filepaths.
        self.subject_id = self.subject_id_text.toPlainText()
        self.record_start_time = datetime.now()
        save_dir = self.video_capture_tab.temp_data_dir
        filename_stem = f"{self.subject_id}_{self.record_start_time.strftime('%Y-%m-%d-%H%M%S')}"
        self.video_filepath = os.path.join(save_dir, filename_stem + ".mp4")
        self.GPIO_filepath = os.path.join(save_dir, filename_stem + "_GPIO_data.csv")
        self.metadata_filepath = os.path.join(save_dir, filename_stem + "_metadata.json")

        # Open GPIO file and write header data.
        self.gpio_file = open(self.GPIO_filepath, mode="w", newline="")
        self.gpio_writer = csv.writer(self.gpio_file)
        self.gpio_writer.writerow(["GPIO1", "GPIO2", "GPIO3"])

        # Create metadata file.
        self.metadata = {
            "subject_ID": self.subject_id,
            "camera_unique_id": self.unique_id,
            "recorded_frames": 0,
            "begin_time": self.record_start_time.isoformat(timespec="milliseconds"),
            "end_time": None,
        }
        with open(self.metadata_filepath, "w") as meta_data_file:
            json.dump(self.metadata, meta_data_file, indent=4)

        # Initalise ffmpeg process
        downsampled_width = int(self.cam_width / self.downsampling_factor)
        downsampled_height = int(self.cam_height / self.downsampling_factor)
        ffmpeg_path = gui_config_dict["PATH_TO_FFMPEG"]
        ffmpeg_command = [
            ffmpeg_path,
            "-y",  # overwrite output file if it exists
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-s",
            f"{downsampled_width}x{downsampled_height}",
            "-r",
            self.fps,  # Set framerate to camera resolution
            "-i",
            "pipe:",  # input comes from a pipe
            "-vcodec",
            ffmpeg_config_dict["output"]["encoder"][self.video_capture_tab.encoder],
            "-pix_fmt",
            ffmpeg_config_dict["output"]["pxl_fmt"][self.pxl_fmt],
            "-preset",
            "fast",
            "-crf",
            "23",
            self.video_filepath,  # Output filename
        ]
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

        # Set variables
        self.recording = True
        self.recorded_frames = 0

        # Update GUI
        self.stop_recording_button.setEnabled(True)
        self.camera_dropdown.setEnabled(False)
        self.start_recording_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        self.video_capture_tab.GUI.tab_widget.tabBar().setEnabled(False)

    def stop_recording(self) -> None:
        """Stop video recording to disk."""
        self.recording = False
        # Close files.
        self.gpio_file.close()
        self.metadata["end_time"] = datetime.now().isoformat(timespec="milliseconds")
        self.metadata["recorded_frames"] = self.recorded_frames
        with open(self.metadata_filepath, "w") as self.meta_data_file:
            json.dump(self.metadata, self.meta_data_file, indent=4)
        # Close FFMPEG process
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()
        # Update GUI
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        self.camera_dropdown.setEnabled(True)
        # Tabs can be changed
        self.video_capture_tab.GUI.tab_widget.tabBar().setEnabled(True)
        self.logger.info("Recording Stopped")

    def save_image_data(self, new_images):
        """Save new images and GPIO data to disk."""
        self.recorded_frames += len(new_images["images"])
        for frame in new_images["images"]:  # Send new images to FFMPEG for encoding.
            self.ffmpeg_process.stdin.write(frame.tobytes())
        for gpio_pinstate in new_images["gpio_data"]:  # Write GPIO pinstate to file.
            self.gpio_writer.writerow(gpio_pinstate)

    ### Config related functions ------------------------------------------------------

    def get_camera_config(self):
        """Get the camera configuration"""
        return CameraSetupConfig(
            label=self.label,
            # downsample_factor=self.downsampling_factor,
            subject_id=self.subject_id,
        )

    def set_camera_widget_config(self, camera_config: CameraSetupConfig):
        """Set the settings assocaitd with the camera widget into the GUI"""
        # Check if the camera label is in the database
        if camera_config.label not in self.camera_setup_tab.get_camera_labels():
            self.logger.error(f"Camera label {camera_config.label} not found in database")
            return

        self.label = camera_config.label
        # self.downsampling_factor = camera_config.downsample_factor
        self.unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(self.label)
        self.subject_id = camera_config.subject_id
        self._change_camera(new_unique_id=self.unique_id, new_camera_label=self.label)
        self.logger.info(f"Camera configuration set to: {camera_config}")

    def change_camera(self) -> None:
        self.logger.info("Changing camera")
        # shut down old camera
        if self.camera_api is not None:
            self.camera_api.stop_capturing()
        # Get the new camera ID
        new_camera_label = str(self.camera_dropdown.currentText())
        # from the setups tab, get the unique id of the camera
        camera_unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(new_camera_label)
        self._change_camera(camera_unique_id, new_camera_label)

    def _change_camera(self, new_unique_id, new_camera_label) -> None:
        # Set the new camera name
        self.unique_id = new_unique_id
        self.label = new_camera_label
        # Get the new camera settings
        self.camera_settings = self.camera_setup_tab.getCameraSettingsConfig(self.label)
        # Set the new camera object
        self.camera_api = init_camera_api(new_unique_id, self.camera_settings)
        self.camera_api.begin_capturing()
        # Call the display function once
        # self.display_frame(self.camera_object.get_next_image())
        #  Update the list cameras that are currently being used.
        self.camera_setup_groupbox.setTitle(self.label)

    def disconnect(self):
        """
        Function for disconnecting the camera from the GUI.
        This function does the following:
        - Ends the recording from the camera object
        - Removes the camera from the grid layout
        - Deletes the camera widget when PyQt6 is ready to delete it
        It should be possible to also remove the camera from the groupboxes list from this function, however
        I have done this after this function is called, in the other places this function is called.
        """
        self.camera_api.stop_capturing()
        self.video_capture_tab.camera_layout.removeWidget(self)

    ### Functions for changing camera settings ----------------------------------------

    def rename(self, new_label):
        """Function to rename the camera"""
        # remove the current label from the camera_dropdown widget
        # self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        self.camera_dropdown.removeItem(self.camera_dropdown.findText(self.label))
        self.label = new_label
        self.camera_dropdown.setCurrentText(new_label)
        self.camera_setup_groupbox.setTitle(new_label)

    def change_fps(self):
        """Change the FPS of the camera"""
        self.logger.info("Changing FPS")
        # Set the new FPS
        self.camera_settings.fps = str(self.fps_cbox.currentText())
        # This function requires reinitalisation of the camera with the new FPS
        self.camera_api.set_frame_rate(int(self.camera_settings.fps))

    def change_pxl_fmt(self):
        """Change the pixel format of the camera"""
        self.logger.info("Changing pixel format")
        # Set the new pixel format to the camera settings datastructure
        self.camera_settings.pxl_fmt = str(self.pxl_fmt_cbox.currentText())
        # This function requires reinitalisation of the camera with the new pixel format
        self.camera_api.set_pixel_format(self.camera_settings.pxl_fmt)

    def change_downsampling_factor(self) -> None:
        """Change the downsampling factor of the camera"""
        self.logger.info("Changing downsampling factor")
        # Get the new downsampling factor
        downsampling_factor = int(self.downsampling_factor_text.currentText())
        # Set the new downsampling factor
        self.downsampling_factor = downsampling_factor
