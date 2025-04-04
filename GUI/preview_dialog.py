import os
import numpy as np
import cv2
from collections import deque
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QFont
import pyqtgraph as pg

# Local Imports
from .utility import init_camera_api_from_module
from config.config import paths_config, gui_config


class CameraPreviewWidget(QWidget):
    """Dialog for previewing the video feed from the setups tab"""

    def __init__(self, gui, camera_table_item):
        super().__init__()
        # self.setups_tab = parent
        self.GUI = gui
        self.camera_table_item = camera_table_item
        self.settings = self.camera_table_item.settings
        self.window_title = f"Camera {self.settings.unique_id}"
        self.paths = paths_config

        self.setWindowTitle(self.window_title)
        icon = QIcon(os.path.join(self.paths["assets_dir"], "logo.svg"))
        self.setWindowIcon(icon)
        main_gui_geometry = self.GUI.geometry()
        self.setGeometry(
            main_gui_geometry.x() + main_gui_geometry.width() + 10,
            main_gui_geometry.y(),
            500,
            500,
        )

        # Video display.
        self.graphics_view = pg.GraphicsView()
        pg.setConfigOption("imageAxisOrder", "row-major")
        self.video_view_box = pg.ViewBox(defaultPadding=0, invertY=True)
        self.video_view_box.setMouseEnabled(x=False, y=False)
        self.graphics_view.setCentralItem(self.video_view_box)
        self.video_image_item = pg.ImageItem()
        self.video_view_box.addItem(self.video_image_item)
        self.video_view_box.setAspectLocked()

        # Framerate overlay
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 10)
        self.video_view_box.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        # Exposure time overlay
        self.frame_timestamps = deque([0], maxlen=10)
        self.exposure_time_text = pg.TextItem()
        self.exposure_time_text.setPos(10, 50)
        self.video_view_box.addItem(self.exposure_time_text)
        self.exposure_time_text.setText("Exposure Time:", color="magenta")

        # Gain overlay
        self.gain_text = pg.TextItem()
        self.gain_text.setPos(10, 90)
        self.video_view_box.addItem(self.gain_text)
        self.gain_text.setText("Gain:", color="magenta")

        # Close button
        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)

        # Layout
        self.hlayout = QVBoxLayout()
        self.hlayout.addWidget(self.graphics_view)
        self.hlayout.addWidget(self.closeButton)
        self.setLayout(self.hlayout)

        # Timer
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self.display_data)

        # Init camera
        self.camera_api = init_camera_api_from_module(settings=self.settings)
        self.camera_width = self.camera_api.get_width()
        self.camera_height = self.camera_api.get_height()
        self.camera_api.begin_capturing()

        self.start_timer()

    # Timers ---------------------------------------------------------------------------------

    def start_timer(self):
        """Start a timer to refresh the video feed at the config `display_update_rate`"""
        self.display_update_timer.start(int(1000 / gui_config["camera_update_rate"]))

    # Video Display  --------------------------------------------------------------------------

    def display_data(self):
        # Get the buffered data
        self.buffered_data = self.camera_api.get_available_images()
        if self.buffered_data is None:
            return  # Exit function if no data
        # Convert image data to np array
        image_data = self.buffered_data["images"][-1]
        image = np.frombuffer(image_data, dtype=np.uint8).reshape(self.camera_height, self.camera_width)
        image = cv2.cvtColor(image, self.camera_api.cv2_conversion[self.settings.pixel_format])
        # Display the data
        self.video_image_item.setImage(image)
        # Calculate frame_rate
        self.frame_timestamps.extend(self.buffered_data["timestamps"])
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (self.frame_timestamps.maxlen - 1)
        calculated_framerate = 1e9 / avg_time_diff
        color = "r" if (abs(calculated_framerate - int(self.settings.fps)) > 1) else "g"
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)
        self.exposure_time_text.setText(
            f"Exposure Time (us) : {self.camera_api.get_exposure_time():.2f}",
            color="magenta",
        )
        self.gain_text.setText(f"Gain (dB) :{self.camera_api.get_gain():.2f}")

    # GUI element udpates ------------------------------------------------------------------------

    def closeEvent(self, event):
        """Handle the close event to stop the timer and release resources"""
        self.camera_api.close_api()
        self.display_update_timer.stop()
        self.GUI.preview_showing = False
        self.close()
        super().closeEvent(event)
        event.accept()

    def resizeEvent(self, event, scale_factor=0.02):
        """Scale the font size to the widget"""
        super().resizeEvent(event)
        font_size = int(min(self.width(), self.height()) * scale_factor)
        self.frame_rate_text.setFont(QFont("Arial", font_size))
        self.exposure_time_text.setFont(QFont("Arial", font_size))
        self.gain_text.setFont(QFont("Arial", font_size))
