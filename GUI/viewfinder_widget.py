# core python
import csv
import sys
import json
import subprocess
import logging
from datetime import datetime
import os
from collections import deque

# video
import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QIcon, QFont

# gui
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
    """
    Widget for each camera to be viewed
    """

    def __init__(
        self,
        parent,
        label,
        subject_id,
    ):
        super(ViewfinderWidget, self).__init__(parent)
        self.view_finder = parent
        self.camera_setup_tab = self.view_finder.GUI.camera_setup_tab
        # Camera object is the camera api that is being used that has generic versions of the core functions
        self.logger = logging.getLogger(__name__)
        self.paths = paths_config_dict
        # Camera attributes
        self.label = label
        self.subject_id = subject_id
        # Check if the camera label is in the database. If is it, we can use the Settings Config information
        # to set the camera settings.

        if self.label in self.camera_setup_tab.get_camera_labels():
            self.camera_settings = self.camera_setup_tab.getCameraSettingsConfig(self.label)
        self.fps = self.camera_settings.fps
        self.pxl_fmt = self.camera_settings.pxl_fmt
        self.unique_id = self.camera_settings.unique_id
        self.downsampling_factor = 1

        self.camera_api = init_camera_api(self.unique_id, self.camera_settings)

        self.cam_width = self.camera_api.get_width()
        self.cam_height = self.camera_api.get_height()

        # Layout

        self.video_feed = pg.ImageView()
        self.video_feed.ui.histogram.hide()
        self.video_feed.ui.roiBtn.hide()
        self.video_feed.ui.menuBtn.hide()
        self.video_feed.view.setMouseEnabled(x=False, y=False)  # Disable zoom and pan

        # Recording Information
        self.recording_status_item = pg.TextItem()
        self.recording_status_item.setPos(10, 10)
        self.video_feed.addItem(self.recording_status_item)
        self.recording_status_item.setText("NOT RECORDING", color="r")

        self.recording_time_text = pg.TextItem()
        self.recording_time_text.setPos(200, 10)
        self.video_feed.addItem(self.recording_time_text)
        self.recording_time_text.setText("", color="r")

        # Initialise the GPIO data
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

        # Framerate information
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 40)
        self.video_feed.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        self.camera_setup_groupbox = QGroupBox(f"{self.label}")

        # Header Layout for groupbox
        self.camera_header_layout = QHBoxLayout()

        # Subject ID
        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.subject_id)
        self.subject_id_text.textChanged.connect(self.update_subject_id)

        # Button for recording video
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "record.svg")))
        self.start_recording_button.setFixedWidth(30)
        # self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.setEnabled(False)
        self.start_recording_button.clicked.connect(self.start_recording)

        # Button for stopping recording
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "stop.svg")))
        self.stop_recording_button.setFixedWidth(30)
        # self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.clicked.connect(self.stop_recording)

        self.camera_id_label = QLabel("Camera ID:")
        # Dropdown for selecting the camera
        self.camera_dropdown = QComboBox()
        # set the current text to the camera label
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        self.update_camera_dropdown()
        self.camera_dropdown.setCurrentText(self.label)
        # Add the widgets to the layout
        self.camera_header_layout.addWidget(self.camera_id_label)
        self.camera_header_layout.addWidget(self.camera_dropdown)
        self.camera_header_layout.addWidget(self.subject_id_label)
        self.camera_header_layout.addWidget(self.subject_id_text)
        self.camera_header_layout.addWidget(self.start_recording_button)
        self.camera_header_layout.addWidget(self.stop_recording_button)
        # Set the layout for the groupbox
        self.camera_setup_groupbox.setLayout(self.camera_header_layout)
        self.camera_setup_groupbox.setFixedHeight(75)

        self.camera_setup_hlayout = QVBoxLayout()

        self.camera_setup_hlayout.addWidget(self.camera_setup_groupbox)
        self.camera_setup_hlayout.addWidget(self.video_feed)

        self.setLayout(self.camera_setup_hlayout)
        self._begin_capturing()

    def _begin_capturing(self):
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
        # Record data to disk if recording.
        if self.recording is True:
            self.recorded_frames += len(new_images["timestamps"])
            self.encode_frame_from_camera_buffer(frame_buffer=new_images["images"])
            self.write_gpio_data_from_buffer(gpio_buffer=new_images["gpio_data"])

    def display_average_frame_rate(self):
        """Compute average framerate and display over image in green if OK else red."""
        # Calculate the frame rate.
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (self.frame_timestamps.maxlen - 1)
        calculated_framerate = 1e9 / avg_time_diff
        # Display the framerate over the image.
        color = "r" if calculated_framerate < (int(self.fps) - 1) else "g"
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)

    def display_recording_time(self):
        """Display the current recording duration over image."""
        if self.recording:
            elapsed_time = datetime.now() - datetime.strptime(self.metadata["begin_time"], "%Y-%m-%d %H:%M:%S")
            elapsed_seconds = elapsed_time.total_seconds()
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.recording_time_text.setText(f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}", color="g")
        else:
            self.recording_time_text.setText("", color="r")

    def update_camera_dropdown(self):
        """Update the cameras available in the camera select dropdown menu."""
        self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        cbox_update_options(
            cbox=self.camera_dropdown,
            options=self.camera_setup_tab.get_camera_labels(),
            used_cameras_labels=list([cam.label for cam in self.view_finder.camera_groupboxes]),
            selected=self.label,
        )
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)

    def get_mp4_filepath(self) -> str:
        """Get the filename for the mp4 file. This is done using GUI information"""
        self.subject_id = self.subject_id_text.toPlainText()
        self.recording_filepath = os.path.join(
            self.view_finder.save_dir_textbox.toPlainText(),
            f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4",
        )

    def create_gpio_file(self):
        """Create the GPIO data file, write header line, store filepath."""
        self.subject_id = self.subject_id_text.toPlainText()
        self.GPIO_filepath = os.path.join(
            self.view_finder.save_dir_textbox.toPlainText(),
            f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_GPIO_data.csv",
        )
        header = ["GPIO1", "GPIO2", "GPIO3"]
        with open(self.GPIO_filepath, mode="w", newline="") as self.f:
            writer = csv.writer(self.f)
            writer.writerow(header)

    def get_metadata_filepath(self) -> str:
        """Get the filename for the metadata file"""
        self.subject_id = self.subject_id_text.toPlainText()
        self.metadata_filepath = os.path.join(
            self.view_finder.save_dir_textbox.toPlainText(),
            f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_metadata.json",
        )

    def display_frame(self):
        """Display most recent image and call functions to add information overlays."""
        self.video_feed.setImage(self._image_data.T)
        self.update_recording_status_overlay()
        self.display_average_frame_rate()
        self.display_recording_time()
        self.update_gpio_overlay()

    def update_recording_status_overlay(self):
        """Set recording status text to match recording status."""
        if self.recording is True:
            status = "RECORDING"
            color = "g"
        elif self.recording is False:
            status = "NOT RECORDING"
            color = "r"
        self.recording_status_item.setText(status, color=color)

    def update_gpio_overlay(self, decay=0.5):
        """Update GPIO status indicators."""
        self.gpio_state_smoothed = decay * self.gpio_state_smoothed
        self.gpio_state_smoothed[np.array(self._GPIO_data) > 0] = 1
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setText("\u2b24", color=[0, 0, self.gpio_state_smoothed[i] * 255])

    def refresh(self):
        """refresh the camera widget"""
        self.update_camera_dropdown()

    def _init_ffmpeg_process(self):
        """Initialise the FFMPEG process that will be used to compress and store video."""
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
            ffmpeg_config_dict["output"]["encoder"][self.view_finder.encoder],
            "-pix_fmt",
            ffmpeg_config_dict["output"]["pxl_fmt"][self.pxl_fmt],
            "-preset",
            "fast",
            "-crf",
            "23",
            self.recording_filepath,  # Output filename
        ]
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

    def encode_frame_from_camera_buffer(self, frame_buffer: list[np.ndarray]) -> None:
        """Encode frames from the frame_buffer and writes them to the file using FFMPEG."""
        while frame_buffer:
            frame = frame_buffer.pop(0)
            self.ffmpeg_process.stdin.write(frame.tobytes())

    def write_gpio_data_from_buffer(self, gpio_buffer):
        """Write the GPIO pinstates in GPIO_buffer to csv file."""
        with open(self.GPIO_filepath, mode="a", newline="") as self.f:
            writer = csv.writer(self.f)
            for gpio_data in gpio_buffer:
                writer.writerow(gpio_data)

    def create_metadata_file(self):
        """Creat the metadata file and write its initial information as a json"""
        self.get_metadata_filepath()
        self.metadata = {
            "subject_ID": self.subject_id,
            "camera_unique_id": self.unique_id,
            "recording_filepath": self.recording_filepath,
            "GPIO_filename": self.GPIO_filepath,
            "recorded_frames": self.recorded_frames,
            "begin_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
        }
        with open(self.metadata_filepath, "w") as self.meta_data_file:
            json.dump(self.metadata, self.meta_data_file, indent=4)

    def close_metadata_file(self):
        self.metadata["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.metadata["recorded_frames"] = self.recorded_frames
        with open(self.metadata_filepath, "w") as self.meta_data_file:
            # add the end time to the metadata file
            json.dump(self.metadata, self.meta_data_file, indent=4)

    def update_subject_id(self):
        self.subject_id = self.subject_id_text.toPlainText()
        self.validate_subject_id_input()

    def validate_subject_id_input(self):
        """Change the colour of the subject ID text field"""
        if self.subject_id_text.toPlainText() == "":
            self.start_recording_button.setEnabled(False)
        else:
            self.start_recording_button.setEnabled(True)

    ### Recording Controls

    def start_recording(self) -> None:
        """
        Function to start the recording of the video.
        - Set the recording flag to True
        - Initalise the ffmpeg process
        - Create the metadata file
        - Update the GUI buttons to the correct state
        """
        # Get the filenames
        self.get_mp4_filepath()
        self.create_gpio_file()
        self.get_metadata_filepath()
        # Initalise ffmpeg process
        self._init_ffmpeg_process()
        # Set the recording flag to True
        self.recording = True
        # Reset the number of recorded frames to zero
        self.recorded_frames = 0
        # Create the metadata file
        self.create_metadata_file()
        # update labels on GUI
        self.stop_recording_button.setEnabled(True)
        self.camera_dropdown.setEnabled(False)
        # self.downsampling_factor_label.setEnabled(False)
        self.start_recording_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        # self.fps_label.setEnabled(False)
        # self.pxl_fmt_label.setEnabled(False)
        # self.downsampling_factor_text.setEnabled(False)
        # Tabs can't be changed whilst recording
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(False)

    def stop_recording(self) -> None:
        """
        Function to stop the recording of the video.
        - Set the recording flag to False
        - Closes the metadata file (by writing the relevent information to it and saving it)
        - Sets the GUI buttons to the correct state
        - De-inits the ffmpeg process
        """
        self.recording = False
        self.close_metadata_file()
        # Set other buttons to now be enabled
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        self.camera_dropdown.setEnabled(True)
        # Tabs can be changed
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(True)
        self.logger.info("Recording Stopped")
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()

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

    def change_downsampling_factor(self) -> None:
        """Change the downsampling factor of the camera"""
        self.logger.info("Changing downsampling factor")
        # Get the new downsampling factor
        downsampling_factor = int(self.downsampling_factor_text.currentText())
        # Set the new downsampling factor
        self.downsampling_factor = downsampling_factor

    ### Config related functions.

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

    ### Functions for changing the camera settings for a camera

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

    ### Visibility Controls

    def toggle_control_visibility(self) -> None:
        """
        Toggle the visibility of the camera controls
        """
        # add a button to connect to this funciton.
        is_visible = self.camera_setup_groupbox.isVisible()
        self.camera_setup_groupbox.setVisible(not is_visible)

    ### Functions for disconnecting the camera from the GUI

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
        self.view_finder.camera_layout.removeWidget(self)
        # This post might suggest that the self.deleteLater() function is causing the application to crash.
        # https://stackoverflow.com/questions/37564728/pyqt-how-to-remove-a-layout-from-a-layout
        # self.deleteLater()
