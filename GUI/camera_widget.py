import os
import cv2
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import deque

import pyqtgraph as pg
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QMessageBox

from .data_recorder import Data_recorder
from camera_api import init_camera_api_from_module


@dataclass
class CameraWidgetConfig:
    """Represents the configuration of a Camera_widget."""

    label: str
    subject_id: str


class ScrollableGraphicsView(pg.GraphicsView):
    """Custom Graphics View to detect scroll wheel events. Used to allow preview camera to have scrollable view"""

    wheelScrolled = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def wheelEvent(self, event):
        """Emit Signals from wheel events"""
        delta = event.angleDelta()
        if delta.y() > 0:
            self.wheelScrolled.emit("Wheel scrolled up")
        elif delta.y() < 0:
            self.wheelScrolled.emit("Wheel scrolled down")
        super().wheelEvent(event)


class CameraWidget(QGroupBox):
    """Widget for displaying camera video and camera controls."""

    def __init__(self, parent, label, subject_id="", preview_mode=False):
        super(CameraWidget, self).__init__(parent)
        self.video_capture_tab = parent
        self.GUI = self.video_capture_tab.GUI
        self.preview_mode = preview_mode  # True if widget is being used in camera setup tab.
        # Camera attributes
        self.subject_id = subject_id
        self.label = label
        self.settings = self.GUI.camera_setup_tab.get_camera_settings_from_label(label)
        self.camera_api = init_camera_api_from_module(settings=self.settings)
        self.camera_height = self.camera_api.get_height()
        self.camera_width = self.camera_api.get_width()
        self.latest_image = None
        self.frame_timestamps = deque([0], maxlen=10)
        self.framenumbers = deque([0], maxlen=10)
        self.controls_visible = True

        # Video display ---------------------------------------------------------------

        self.graphics_view = ScrollableGraphicsView()
        self.graphics_view.wheelScrolled.connect(self.handle_wheel_event)
        self.video_view_box = pg.ViewBox(defaultPadding=0, invertY=True)
        self.video_view_box.setMouseEnabled(x=False, y=False)
        self.graphics_view.setCentralItem(self.video_view_box)
        pg.setConfigOption("imageAxisOrder", "row-major")
        self.video_image_item = pg.ImageItem()
        self.video_view_box.addItem(self.video_image_item)
        self.video_view_box.setAspectLocked()

        text_spacing = int(self.GUI.gui_config["font_size"] * 1.25)

        # Camera name overlay
        self.camera_name_item = pg.TextItem()
        self.camera_name_item.setPos(10, text_spacing)
        self.graphics_view.addItem(self.camera_name_item)
        self.camera_name_item.setText(
            f"{self.label} : {self.subject_id}" if self.subject_id else f"{self.label}", color="white"
        )

        # Recording Information overlay
        self.recording_status_item = pg.TextItem()
        self.recording_status_item.setPos(10, 2 * text_spacing)
        self.graphics_view.addItem(self.recording_status_item)
        self.recording_status_item.setText("NOT RECORDING", color="r")
        # Framerate overlay
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 3 * text_spacing)
        self.graphics_view.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        # GPIO state overlay
        self.gpio_state_smoothed = np.zeros(self.camera_api.N_GPIO)
        self.gpio_status_item = pg.TextItem()
        self.gpio_status_item.setPos(10, 4 * text_spacing)
        self.graphics_view.addItem(self.gpio_status_item)
        self.gpio_status_item.setText("GPIO state", color="blue")
        self.gpio_status_indicators = [pg.TextItem() for _ in range(self.camera_api.N_GPIO)]
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setPos((5 + i) * text_spacing, 4 * text_spacing)
            self.graphics_view.addItem(gpio_indicator)

        # Dropped frames overlay
        self.dropped_frames_text = pg.TextItem()
        self.dropped_frames_text.setPos(10, 5 * text_spacing)
        self.graphics_view.addItem(self.dropped_frames_text)
        self.dropped_frames_text.setText("", color="r")

        if self.preview_mode:
            # Exposure time overlay
            self.exposure_time_text = pg.TextItem()
            self.exposure_time_text.setPos(10, 6 * text_spacing)
            self.graphics_view.addItem(self.exposure_time_text)
            self.exposure_time_text.setText("Exposure Time:", color="magenta")

            # Gain overlay
            self.gain_text = pg.TextItem()
            self.gain_text.setPos(10, 7 * text_spacing)
            self.graphics_view.addItem(self.gain_text)
            self.gain_text.setText("Gain:", color="magenta")

        # Controls -----------------------------------------------------------------

        # Subject ID text edit
        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.subject_id)
        self.subject_id_text.textChanged.connect(self.subject_ID_edited)

        # Record button.
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "record.svg")))
        self.start_recording_button.setFixedWidth(30)
        self.start_recording_button.setEnabled(bool(self.subject_id))
        self.start_recording_button.clicked.connect(self.start_recording)
        self.start_recording_button.setToolTip("Start Recording")

        # Stop button.
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(QIcon(os.path.join(self.GUI.paths_config["icons_dir"], "stop.svg")))
        self.stop_recording_button.setFixedWidth(30)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.clicked.connect(self.stop_recording)
        self.stop_recording_button.setToolTip("Stop Recording")

        # Camera select dropdown
        self.camera_id_label = QLabel("Camera:")
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.addItems([self.label])
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
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

        if self.preview_mode:
            self.toggle_control_visibility()
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update)
            self.update_timer.start(int(1000 / self.GUI.gui_config["camera_update_rate"]))
        else:
            self.data_recorder = Data_recorder(self)

        self.begin_capturing()  # After init, start capturing from the widget

    # Camera control ----------------------------------------------------

    def begin_capturing(self):
        """Start streaming video from camera."""
        self.recording = False
        self._last_timestamp = None
        # Begin capturing using the camera API
        self.camera_api.begin_capturing(self.settings)

    def stop_capturing(self):
        """Stop streaming video from camera."""
        if self.recording:
            self.stop_recording()
        self.camera_api.stop_capturing()

    def fetch_image_data(self):
        """Get images and associated data from camera and save to disk if recording."""
        new_images = self.camera_api.get_available_images()
        if new_images == None:
            return
        # Store most recent image and GPIO state for the next display update.
        self.latest_image = new_images["images"][-1]
        self.latest_GPIO = new_images["gpio_data"][-1]
        # Check for dropped frames based on expected interval between exposure timestamps
        self._newly_dropped_frames = new_images["dropped_frames"]
        self.frame_timestamps.extend(new_images["timestamps"])  # For displaying the calculated framerate

        # Record data to disk.
        if self.recording:
            self.video_capture_tab.futures.append(
                self.video_capture_tab.threadpool.submit(self.data_recorder.record_new_images, new_images)
            )

    def update(self, update_video_display=True):
        """Called regularly by timer to fetch new images and optionally update video display."""
        self.fetch_image_data()
        if update_video_display:
            self.update_video_display()
        

    # Recording controls --------------------------------------------------------------

    def start_recording(self):
        """Start recording vidoe data to disk"""
        subject_id = self.subject_id_text.toPlainText()
        # Check subject ID is valid.
        if any(char in set('<>:"/\\|?*') for char in subject_id):
            QMessageBox.information(self, "Invalid subject ID", f"Subject ID contains invalid characters: {subject_id}")
            return
        # Start data recording.
        save_dir = self.GUI.video_capture_tab.data_dir
        self.data_recorder.start_recording(subject_id, save_dir, self.settings)
        # Empty camera buffer before recording is started
        self.camera_api.get_available_images()
        self.recording = True
        # Update GUI
        self.stop_recording_button.setEnabled(True)
        self.camera_dropdown.setEnabled(False)
        self.start_recording_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        self.GUI.tab_widget.tabBar().setEnabled(False)
        self.GUI.video_capture_tab.update_button_states()

    def stop_recording(self):
        """Stop recording video data to disk."""
        self.data_recorder.stop_recording()
        self.recording = False
        # Update GUI
        self.recording_status_item.setText("NOT RECORDING", color="r")
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        self.camera_dropdown.setEnabled(True)
        self.GUI.video_capture_tab.update_button_states()
        self.GUI.tab_widget.tabBar().setEnabled(True)

    # Video display -------------------------------------------------------------------

    def update_video_display(self, gpio_smoothing_decay=0.5):
        """Display most recent image and update information overlays."""
        if self.latest_image is None:
            return
        image = np.frombuffer(self.latest_image, dtype=np.uint8).reshape(self.camera_height, self.camera_width)
        if self.settings.pixel_format != "Mono":
            image = cv2.cvtColor(image, self.camera_api.pixel_format_map[self.settings.pixel_format]["cv2"])
        self.video_image_item.setImage(image)
        # Compute average framerate and display over image.
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (self.frame_timestamps.maxlen - 1)
        calculated_framerate = 1e9 / avg_time_diff
        color = "r" if (abs(calculated_framerate - int(self.settings.fps)) > 1) else "g"
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)
        # Update GPIO status indicators.
        self.gpio_state_smoothed = gpio_smoothing_decay * self.gpio_state_smoothed
        self.gpio_state_smoothed[np.array(self.latest_GPIO) > 0] = 1
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setText("\u2b24", color=[0, 0, self.gpio_state_smoothed[i] * 255])
        # Display the current recording duration over image.
        if self.recording:
            elapsed_time = datetime.now() - self.data_recorder.record_start_time
            self.recording_status_item.setText(f"RECORDING  {str(elapsed_time).split('.')[0]}", color="g")
        # Update dropped frames indicator.
        if self._newly_dropped_frames:
            self.dropped_frames_text.setText("DROPPED FRAMES", color="r")
        else:
            self.dropped_frames_text.setText("")
        # Show additional camera settings if in preview mode.
        if self.preview_mode:
            self.exposure_time_text.setText(
                (
                    f"Exposure Time (us) : {self.camera_api.get_exposure_time():.2f}"
                    if self.camera_api.get_exposure_time()
                    else "Exposure Time (us) : N/A"
                ),
                color="magenta",
            )
            self.gain_text.setText(
                f"Gain (dB) :{self.camera_api.get_gain():.2f}" if self.camera_api.get_gain() else "Gain (dB) : N/A"
            )

    # GUI element updates -------------------------------------------------------------

    def refresh(self):
        """refresh the camera widget"""
        self.update_camera_dropdown()
        self.update_viewfinder_text()

    def update_camera_dropdown(self):
        """Update the cameras available in the camera select dropdown menu."""
        # Disconnect function whilst updating text
        try:
            self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        except TypeError:
            pass  # Signal was not connected
        # Available cameras
        available_cameras = sorted(
            set(self.GUI.camera_setup_tab.get_camera_labels())
            - {cam.label for cam in self.GUI.video_capture_tab.camera_widgets},
            key=str.lower,
        )
        selected_camera_label = self.camera_dropdown.currentText()
        if selected_camera_label:  # cbox contains something
            available_cameras = sorted(list(set([selected_camera_label] + available_cameras)), key=str.lower)
        self.camera_dropdown.clear()
        self.camera_dropdown.addItems(available_cameras)
        self.camera_dropdown.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )  # Adjust size to fit contents
        self.camera_dropdown.setCurrentIndex(
            available_cameras.index(selected_camera_label) if selected_camera_label else 0
        )
        # Re-enable function whilst updating text
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)

    def update_viewfinder_text(self):
        """Update the viewfinder display text based on if settings have changed"""
        self.recording_status_item.setText(
            "NOT RECORDING",
            color="r",
        )

    def subject_ID_edited(self):
        """Store new subject ID and update status of recording button."""
        self.subject_id = self.subject_id_text.toPlainText()
        if self.subject_id:
            self.start_recording_button.setEnabled(True)
            self.camera_name_item.setText(f"{self.label} : {self.subject_id}", color="white")
        else:
            self.start_recording_button.setEnabled(False)
            self.camera_name_item.setText(f"{self.label}", color="white")
        # Overwrite start_recording button if FFMPEG not available
        self.start_recording_button.setEnabled(self.GUI.ffmpeg_path_available)
        self.GUI.video_capture_tab.update_button_states()

    def toggle_control_visibility(self) -> None:
        """Toggle the visibility of the camera controls."""
        self.controls_visible = not self.controls_visible
        for i in range(self.header_layout.count()):
            widget = self.header_layout.itemAt(i).widget()
            widget.setVisible(self.controls_visible)

    def handle_wheel_event(self, direction):
        """Zoom in / out of the video data"""
        if self.preview_mode:
            scale_factor = 1.1 if direction == "Wheel scrolled up" else 1 / 1.1
            self.video_view_box.scaleBy((scale_factor, scale_factor))

    ### Config related functions ------------------------------------------------------

    def get_camera_config(self):
        """Get the camera configuration"""
        return CameraWidgetConfig(label=self.label, subject_id=self.subject_id)

    def change_camera(self) -> None:
        # shut down old camera
        if self.camera_api is not None:
            self.camera_api.close_api()
            del self.camera_api
        self.latest_image = None
        # Initialise the new camera
        self.label = str(self.camera_dropdown.currentText())
        self.settings = self.GUI.camera_setup_tab.get_camera_settings_from_label(self.label)
        self.camera_api = init_camera_api_from_module(self.settings)
        self.camera_api.begin_capturing(self.settings)
        self.camera_height = self.camera_api.get_height()
        self.camera_width = self.camera_api.get_width()
        # Rename pyqtgraph element
        self.camera_name_item.setText(
            f"{self.settings.name if self.settings.name is not None else self.settings.unique_id}", color="white"
        )
        # Update GPIO elements
        self.gpio_state_smoothed = np.zeros(self.camera_api.N_GPIO)
        for gpio_indicator in self.gpio_status_indicators:
            self.graphics_view.removeItem(gpio_indicator)
        self.gpio_status_indicators = [pg.TextItem() for _ in range(self.camera_api.N_GPIO)]
        for i, gpio_indicator in enumerate(self.gpio_status_indicators):
            gpio_indicator.setPos(
                (5 + i) * int(self.GUI.gui_config["font_size"] * 1.25), 4 * int(self.GUI.gui_config["font_size"] * 1.25)
            )
            self.graphics_view.addItem(gpio_indicator)
        # Update Frame triggered text
        self.recording_status_item.setText("NOT RECORDING", color="r")

    def closeEvent(self, event):
        """Handle the close event to stop the timer and release resources"""
        self.stop_capturing()
        if self.preview_mode:
            self.update_timer.stop()
        self.close()
        super().closeEvent(event)
        event.accept()

    ### Functions for changing camera settings ----------------------------------------

    def rename(self, new_label):
        """Rename the camera"""
        self.camera_dropdown.removeItem(self.camera_dropdown.findText(self.label))
        self.label = new_label
        self.camera_dropdown.setCurrentText(new_label)
