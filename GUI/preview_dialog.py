import os
from collections import deque
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QFont
import pyqtgraph as pg

# Local Imports
from .utility import init_camera_api
from config.config import paths_config, gui_config


class CameraPreviewWidget(QWidget):
    """Dialog for previewing the video feed from the setups tab"""

    def __init__(self, gui, camera_table_item, unique_id):  # camera_api):
        super().__init__()
        # self.setups_tab = parent
        self.GUI = gui
        self.camera_table_item = camera_table_item
        self.unique_id = unique_id
        # self.unique_id = self.camera_api.unique_id
        self.window_title = f"Camera {self.unique_id}"
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

        # Intialise Videofeed
        self.video_feed = pg.ImageView()
        self.video_feed.ui.histogram.hide()
        self.video_feed.ui.roiBtn.hide()
        self.video_feed.ui.menuBtn.hide()
        self.video_feed.view.setMouseEnabled(x=False, y=False)  # Disable zoom and pan

        # Framerate overlay
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 10)
        self.video_feed.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        # Exposure time overlay
        self.frame_timestamps = deque(maxlen=10)
        self.exposure_time_text = pg.TextItem()
        self.exposure_time_text.setPos(10, 50)
        self.video_feed.addItem(self.exposure_time_text)
        self.exposure_time_text.setText("Exposure Time:", color="magenta")

        # Gain overlay
        self.gain_text = pg.TextItem()
        self.gain_text.setPos(10, 90)
        self.video_feed.addItem(self.gain_text)
        self.gain_text.setText("Gain:", color="magenta")

        # Close button
        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)

        # Layout
        self.hlayout = QVBoxLayout()
        self.hlayout.addWidget(self.video_feed)
        self.hlayout.addWidget(self.closeButton)
        self.setLayout(self.hlayout)

        # Init camera
        self.camera_api = init_camera_api(_id=self.unique_id)
        self.camera_api.begin_capturing()

        self.start_timer()

    def display_data(self):
        # Get the buffered data
        self.buffered_data = self.camera_api.get_available_images()
        if type(self.buffered_data) is type(None):
            return  # exit the function and wait to be called by the viewfinder tab.
        self._image_data = self.buffered_data["images"][0]
        # Calculate frame_rate
        self.frame_timestamps.extend(self.buffered_data["timestamps"])
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (self.frame_timestamps.maxlen - 1)
        calculated_framerate = 1e9 / avg_time_diff
        color = "r" if (abs(calculated_framerate - int(self.camera_table_item.fps)) > 1) else "g"
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)
        self.exposure_time_text.setText(
            f"Exposure Time (us) : {self.camera_api.get_exposure_time():.2f}",
            color="magenta",
        )
        self.gain_text.setText(f"Gain (dB) :{self.camera_api.get_gain():.2f}")
        # Display the data
        self.video_feed.setImage(self._image_data.T)

    def start_timer(self):
        """Start a timer to refresh the video feed every second"""
        self.display_update_timer = QTimer()
        self.display_update_timer.timeout.connect(self.display_data)
        self.display_update_timer.start(int(1000 / gui_config["display_update_rate"]))

    def closeEvent(self, event):
        """Handle the close event to stop the timer and release resources"""
        self.camera_api.stop_capturing()
        self.display_update_timer.stop()
        self.GUI.preview_showing = False
        self.camera_table_item.exposure_time_edit.setEnabled(False)
        self.camera_table_item.fps_edit.setEnabled(False)
        self.close()
        super().closeEvent(event)
        event.accept()

    def resizeEvent(self, event, scale_factor=0.02):
        """Scale the font size to the window"""
        super().resizeEvent(event)
        font_size = int(min(self.width(), self.height()) * scale_factor)
        self.frame_rate_text.setFont(QFont("Arial", font_size))
        self.exposure_time_text.setFont(QFont("Arial", font_size))
        self.gain_text.setFont(QFont("Arial", font_size))
