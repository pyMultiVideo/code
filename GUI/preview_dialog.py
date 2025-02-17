import sys
import os
import numpy as np
from collections import deque
import PyQt6.QtWidgets as QtWidgets
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QFont
import pyqtgraph as pg

# Local Imports
from .utility import init_camera_api
from config.config import paths_config, gui_config


class CameraPreviewDialog(QtWidgets.QWidget):
    """Dialog for previewing the video feed from the setups tab"""

    def __init__(self, gui, unique_id: str, window_title: str = "Camera Preview"):
        super().__init__()
        # self.setups_tab = parent
        self.main_gui = gui
        self.window_title = window_title
        self.unique_id = unique_id
        self.paths = paths_config

        self.setWindowTitle(self.window_title)
        icon = QIcon(os.path.join(self.paths["assets_dir"], "logo.svg"))
        self.setWindowIcon(icon)
        main_gui_geometry = self.main_gui.geometry()
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

        # Exposure time overlay
        self.frame_timestamps = deque(maxlen=10)
        self.exposure_time_text = pg.TextItem()
        self.exposure_time_text.setPos(10, 10)
        self.video_feed.addItem(self.exposure_time_text)
        self.exposure_time_text.setText("Exposure Time:", color="blue")

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
        self.buffered_data: dict = self.camera_api.get_available_images()
        if len(self.buffered_data["images"]) == 0:
            return  # exit the function and wait to be called by the viewfinder tab.
        self._image_data = self.buffered_data["images"][0]

        # Calculate frame_rate
        self.frame_timestamps.extend(self.buffered_data["timestamps"])
        avg_time_diff = (self.frame_timestamps[-1] - self.frame_timestamps[0]) / (
            self.frame_timestamps.maxlen - 1
        )
        calculated_framerate = 1e9 / avg_time_diff
        # Display timestamps data
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color="r")
        self.exposure_time_text.setText(
            f"Exposure Time: {self.buffered_data['exposure_times'][0]:.2f} us",
            color="blue",
        )
        # Display the data
        self.video_feed.setImage(self._image_data.T)

    def display_update_font_size(self, scale_factor=0.015):
        """"""
        font_size = int(min(self.width(), self.height()) * scale_factor)

        self.gpio_status_item.setFont(QFont(self.gpio_status_font.family(), font_size))
        for gpio_indicator in self.gpio_status_indicators:
            gpio_indicator.setFont(QFont(self.gpio_status_font.family(), font_size))
        self.frame_rate_text.setFont(QFont(self.gpio_status_font.family(), font_size))
        self.exposure_time_text.setFont(
            QFont(self.gpio_status_font.family(), font_size)
        )

    def start_timer(self):
        """Start a timer to refresh the video feed every second"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(int(1000 / gui_config["display_update_rate"]))

    def refresh(self):
        """Refresh function for this tab"""
        self.display_data()

    def closeEvent(self, event):
        """Handle the close event to stop the timer and release resources"""
        if hasattr(self, "timer"):
            self.timer.stop()
        self.camera_api.stop_capturing()
        self.main_gui.preview_showing = False
        event.accept()

    def resizeEvent(self, event):
        """Resize event"""
        self.display_update_font_size()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CameraPreviewDialog(unique_id="18360350-spinnaker")
    dialog.exec()
    sys.exit(app.exec())
