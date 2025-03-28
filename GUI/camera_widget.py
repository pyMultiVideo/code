import os
import csv
import json
import subprocess
import numpy as np
import cv2
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
)

from .utility import (
    cbox_update_options,
    CameraWidgetConfig,
    init_camera_api_from_module,
    validate_ffmpeg_path,
    ffmpeg_encoder_map,
)
from .message_dialogs import show_warning_message
from config.config import ffmpeg_config, paths_config


class CameraWidget(QGroupBox):
    """Widget for displaying camera video and camera controls."""

    def __init__(self, parent, label, subject_id):
        super(CameraWidget, self).__init__(parent)
        self.video_capture_tab = parent
        self.GUI = self.video_capture_tab.GUI
        self.camera_setup_tab = self.video_capture_tab.GUI.camera_setup_tab
        self.paths = paths_config
        self.ffmpeg_path = (
            self.paths["FFMPEG"]
            if validate_ffmpeg_path(self.paths["FFMPEG"])
            else show_warning_message(
                f"FFMPEG path {self.paths['FFMPEG']} not valid",
                okayButtonPresent=False,
                ignoreButtonPresent=True,
            )
        )

        # Camera attributes
        self.subject_id = subject_id
        self.label = label
        self.settings = self.camera_setup_tab.get_camera_settings_from_label(label)
        self.camera_api = init_camera_api_from_module(settings=self.settings)
        self.camera_height = self.camera_api.get_height()
        self.camera_width = self.camera_api.get_width()
        self.latest_image = None
        self.frame_timestamps = deque([0], maxlen=10)
        self.controls_visible = True

        # Video display.
        self.graphics_view = pg.GraphicsView()
        self.video_view_box = pg.ViewBox(defaultPadding=0, invertY=True)
        self.video_view_box.setMouseEnabled(x=False, y=False)
        self.graphics_view.setCentralItem(self.video_view_box)
        pg.setConfigOption('imageAxisOrder', 'row-major')
        self.video_image_item = pg.ImageItem()
        self.video_view_box.addItem(self.video_image_item)
        self.video_view_box.setAspectLocked()

        # Video Feed's Camera Name
        self.camera_name_item = pg.TextItem()
        self.camera_name_item.setPos(10, 10)
        self.video_view_box.addItem(self.camera_name_item)
        self.camera_name_item.setText(f"{self.label}", color="white")

        # Recording Information overlay
        self.recording_status_item = pg.TextItem()
        self.recording_status_item.setPos(10, 40)
        self.video_view_box.addItem(self.recording_status_item)
        self.recording_status_item.setText("NOT RECORDING", color="r")

        # Framerate overlay
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 70)
        self.video_view_box.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        # GPIO state overlay
        self.gpio_state_smoothed = np.zeros(3)
        self.gpio_status_item = pg.TextItem()
        self.gpio_status_item.setPos(10, 100)
        self.video_view_box.addItem(self.gpio_status_item)
        self.gpio_status_item.setText("GPIO state", color="blue")
        self.gpio_status_indicators = [pg.TextItem() for _ in range(3)]
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setPos(150 + i * 30, 100)
            self.video_view_box.addItem(gpio_indicator)

        # Dropped frames overlay
        self.dropped_frames_text = pg.TextItem()
        self.dropped_frames_text.setPos(10, 130)
        self.video_view_box.addItem(self.dropped_frames_text)
        self.dropped_frames_text.setText("", color="r")

        # Subject ID text edit
        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.subject_id)
        self.subject_id_text.textChanged.connect(self.subject_ID_edited)

        # Record button.
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "record.svg")))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setEnabled(bool(self.subject_id))
        self.start_recording_button.clicked.connect(self.start_recording)
        self.start_recording_button.setToolTip("Start Recording")

        # Stop button.
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.paths["assets_dir"], "stop.svg")))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        self.stop_recording_button.setToolTip("Stop Recording")

        # Camera select dropdown
        self.camera_id_label = QLabel("Camera:")
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        self.update_camera_dropdown()
        self.camera_dropdown.setCurrentText(self.label)

        # Layout
        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.camera_id_label)
        self.header_layout.addWidget(self.camera_dropdown)
        self.header_layout.addWidget(self.subject_id_label)
        self.header_layout.addWidget(self.subject_id_text)
        self.header_layout.addWidget(self.start_recording_button)
        self.header_layout.addWidget(self.stop_recording_button)

        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(self.header_layout)
        self.vlayout.addWidget(self.graphics_view, stretch=100)

        self.setLayout(self.vlayout)

        self.begin_capturing()

    # Camera and recording control ----------------------------------------------------

    def begin_capturing(self):
        """Start streaming video from camera."""
        self.recording = False
        self.dropped_frames = 0
        # Begin capturing using the camera API
        self.camera_api.begin_capturing(self.settings)

    def stop_capturing(self):
        """Stop streaming video from camera."""
        if self.recording:
            self.stop_recording()
        self.camera_api.stop_capturing()

    def fetch_image_data(self) -> None:
        """Get images and associated data from camera and save to disk if recording."""
        new_images = self.camera_api.get_available_images()
        if new_images == None:
            return
        # Store most recent image and GPIO state for the next display update.
        self.latest_image = new_images["images"][-1]
        self._GPIO_data = new_images["gpio_data"][-1]
        self._newly_dropped_frames = new_images["dropped_frames"]
        self.frame_timestamps.extend(new_images["timestamps"])
        self.dropped_frames += new_images["dropped_frames"]
        # Record data to disk.
        if self.recording:
            self.recorded_frames += len(new_images["images"])
            # Concatenate the list of numpy buffers into one bytestream
            frame = np.concatenate([img for img in new_images["images"]])
            self.ffmpeg_process.stdin.write(frame)
            for gpio_pinstate in new_images["gpio_data"]:  # Write GPIO pinstate to file.
                self.gpio_writer.writerow(gpio_pinstate)

    def start_recording(self) -> None:
        """Open data files and FFMPEG process, update GUI elements for recording."""
        # Create Filepaths.
        self.subject_id = self.subject_id_text.toPlainText()
        self.record_start_time = datetime.now()
        save_dir = self.video_capture_tab.temp_data_dir
        filename_stem = f"{self.subject_id}_{self.record_start_time.strftime('%Y-%m-%d-%H%M%S')}"
        self.video_filepath = os.path.join(save_dir, filename_stem + ".mp4")
        self.GPIO_filepath = os.path.join(save_dir, filename_stem + "_GPIO_data.csv")
        self.metadata_filepath = os.path.join(save_dir, filename_stem + "_metadata.json")
        self.dropped_frames = 0

        # Open GPIO file and write header data.
        self.gpio_file = open(self.GPIO_filepath, mode="w", newline="")
        self.gpio_writer = csv.writer(self.gpio_file)
        self.gpio_writer.writerow(["GPIO1", "GPIO2", "GPIO3"])

        # Create metadata file.
        self.metadata = {
            "subject_ID": self.subject_id,
            # Camera Config Settings
            "camera_unique_id": self.settings.unique_id,
            "camera_name": self.settings.name,
            "FPS": int(self.settings.fps),
            "exposure_time": self.settings.exposure_time,
            "gain": self.settings.gain,
            "pixel_format": self.settings.pixel_format,
            "downsampling_factor": self.settings.downsampling_factor,
            # Recording information
            "recorded_frames": 0,
            "dropped_frames": None,
            "start_time": self.record_start_time.isoformat(timespec="milliseconds"),
            "end_time": None,
            "duration": None,
        }
        with open(self.metadata_filepath, "w") as meta_data_file:
            json.dump(self.metadata, meta_data_file, indent=4)

        # Initalise ffmpeg process
        self.camera_width = int(self.camera_api.get_width())
        self.camera_height = int(self.camera_api.get_height())
        self.downsampled_width = self.camera_width // self.settings.downsampling_factor
        self.downsampled_height = self.camera_height // self.settings.downsampling_factor
        ffmpeg_command = " ".join(
            [
                self.ffmpeg_path,  # Path to binary
                "-f rawvideo",  # Input codec (raw video)
                f"-s {self.camera_width}x{self.camera_height}",  # Input frame size
                f"-pix_fmt {self.camera_api.supported_pixel_formats[self.settings.pixel_format]}",  # Input Pixel Format: 8-bit grayscale input to ffmpeg process. Input array 1D
                f"-r {self.settings.fps}",  # Frame rate
                "-i -",  # input comes from a pipe (stdin)
                f"-c:v {ffmpeg_encoder_map[ffmpeg_config['compression_standard']]}",  # Output codec
                f"-s {self.downsampled_width}x{self.downsampled_height}",  # Output frame size after any downsampling.
                "-pix_fmt yuv420p",  # Output pixel format
                f"-preset {ffmpeg_config['encoding_speed']}",  # Encoding speed [fast, medium, slow]
                f"-b:v 0 "  # Encoder uses variable bit rate https://superuser.com/questions/1236275/how-can-i-use-crf-encoding-with-nvenc-in-ffmpeg
                f"-cq {ffmpeg_config['crf']}",  # Controls quality vs filesize
                f'"{self.video_filepath}"',  # Output file path
            ]
        )
        print(ffmpeg_command)
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
        self.video_capture_tab.update_global_recording_button_states()

    def stop_recording(self) -> None:
        """Close data files and FFMPEG process, update GUI elements."""
        self.recording = False
        end_time = datetime.now()
        self.recording_status_item.setText("NOT RECORDING", color="r")
        # Close files.
        self.gpio_file.close()
        self.metadata["end_time"] = end_time.isoformat(timespec="milliseconds")
        self.metadata["duration"] = str(end_time - self.record_start_time)[:-3]
        self.metadata["recorded_frames"] = self.recorded_frames
        self.metadata["dropped_frames"] = self.dropped_frames
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
        self.video_capture_tab.update_global_recording_button_states()
        # Tabs can be changed
        self.video_capture_tab.GUI.tab_widget.tabBar().setEnabled(True)

    # Video display -------------------------------------------------------------------

    def update_video_display(self, gpio_smoothing_decay=0.5):
        """Display most recent image and update information overlays."""
        if self.latest_image is None:
            return
        image = np.frombuffer(self.latest_image, dtype=np.uint8).reshape(self.camera_height, self.camera_width)
        if self.settings.pixel_format != "Mono8":
            image = cv2.cvtColor(image, self.camera_api.cv2_conversion[self.settings.pixel_format])
        self.video_image_item.setImage(image)
        # Compute average framerate and display over image.
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (self.frame_timestamps.maxlen - 1)
        calculated_framerate = 1e9 / avg_time_diff
        color = "r" if (abs(calculated_framerate - int(self.settings.fps)) > 1) else "g"
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)
        # Update GPIO status indicators.
        self.gpio_state_smoothed = gpio_smoothing_decay * self.gpio_state_smoothed
        self.gpio_state_smoothed[np.array(self._GPIO_data) > 0] = 1
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setText("\u2b24", color=[0, 0, self.gpio_state_smoothed[i] * 255])
        # Display the current recording duration over image.
        if self.recording:
            elapsed_time = datetime.now() - self.record_start_time
            self.recording_status_item.setText(f"RECORDING  {str(elapsed_time).split('.')[0]}", color="g")
        # Update dropped frames indicator.
        if self._newly_dropped_frames:
            self.dropped_frames_text.setText("DROPPED FRAMES", color="r")
        else:
            self.dropped_frames_text.setText("")

    # GUI element updates -------------------------------------------------------------

    def refresh(self):
        """refresh the camera widget"""
        self.update_camera_dropdown()

    def update_camera_dropdown(self):
        """Update the cameras available in the camera select dropdown menu."""
        self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        cbox_update_options(
            cbox=self.camera_dropdown,
            options=self.camera_setup_tab.get_camera_labels(),
            used_cameras_labels=list([cam.label for cam in self.video_capture_tab.camera_widgets]),
            selected=self.label,
        )
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)

    def subject_ID_edited(self):
        """Store new subject ID and update status of recording button."""
        self.subject_id = self.subject_id_text.toPlainText()
        if self.subject_id:
            self.start_recording_button.setEnabled(True)
            self.camera_name_item.setText(f"{self.label} : {self.subject_id}", color="white")
        else:
            self.start_recording_button.setEnabled(False)
            self.camera_name_item.setText(f"{self.label}", color="white")
        self.video_capture_tab.update_global_recording_button_states()

    def toggle_control_visibility(self) -> None:
        """Toggle the visibility of the camera controls."""
        self.controls_visible = not self.controls_visible
        for i in range(self.header_layout.count()):
            widget = self.header_layout.itemAt(i).widget()
            widget.setVisible(self.controls_visible)
        # Set the camera label onto the pygraph
        if self.controls_visible:
            self.video_view_box.removeItem(self.camera_name_item)
        else:
            self.video_view_box.addItem(self.camera_name_item)

    def resizeEvent(self, event, scale_factor=0.015):
        """Update display element font sizes on resizeEvent."""
        font_size = int(min(self.width(), self.height()) * scale_factor)
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setFont(QFont("Arial", font_size))
        self.gpio_status_item.setFont(QFont("Arial", font_size))
        self.recording_status_item.setFont(QFont("Arial", font_size))
        self.frame_rate_text.setFont(QFont("Arial", font_size))
        self.camera_name_item.setFont(QFont("Arial", font_size))
        super().resizeEvent(event)

    ### Config related functions ------------------------------------------------------

    def get_camera_config(self):
        """Get the camera configuration"""
        return CameraWidgetConfig(label=self.label, subject_id=self.subject_id)

    def change_camera(self) -> None:
        # shut down old camera
        if self.camera_api is not None:
            self.camera_api.close_api()
        # Initialise the new camera
        self.label = str(self.camera_dropdown.currentText())
        self.settings = self.camera_setup_tab.get_camera_settings_from_label(self.label)
        self.camera_api = init_camera_api_from_module(self.settings)
        self.camera_api.begin_capturing()
        self.camera_height = self.camera_api.get_height()
        self.camera_width = self.camera_api.get_width()
        # Rename pyqtgraph element
        self.camera_name_item.setText(
            f"{self.settings.name if self.settings.name is not None else self.settings.unique_id}", color="white"
        )

    ### Functions for changing camera settings ----------------------------------------

    def rename(self, new_label):
        """Rename the camera"""
        self.camera_dropdown.removeItem(self.camera_dropdown.findText(self.label))
        self.label = new_label
        self.camera_dropdown.setCurrentText(new_label)
