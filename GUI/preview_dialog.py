import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

from tools import init_camera_api


class CameraPreviewDialog(QDialog):
    """Dialog for previewing the video feed from the setups tab"""

    def __init__(self, unique_id:str, window_title: str = "Camera Preview"):
        super().__init__()
        # self.setups_tab = parent
        self.window_title = window_title
        self.unique_id = unique_id

        self.initUI()
        self.initCamera()
        self.start_timer()

    def initUI(self):
        self.setWindowTitle(self.window_title)
        self.setGeometry(700, 100, 500,500)

        self.hlayout = QVBoxLayout()

        """Intialise Videofeed"""
        self.video_feed = pg.ImageView()
        self.video_feed.ui.histogram.hide()
        self.video_feed.ui.roiBtn.hide()
        self.video_feed.ui.menuBtn.hide()
        self.video_feed.view.setMouseEnabled(x=False, y=False)
        self.hlayout.addWidget(self.video_feed)

        """Close Button"""
        self.closeButton = QPushButton("Close", self)
        self.closeButton.clicked.connect(self.close)
        self.hlayout.addWidget(self.closeButton)

        self.setLayout(self.hlayout)

    def initCamera(self):
        self.camera_api = init_camera_api(_id=self.unique_id)
        self.camera_api.begin_capturing()

    def _display_preview(self):
        """Display the data at the GUI"""

        # Get the buffered data
        self.buffered_data: dict = self.camera_api.retrieve_buffered_data()
        if len(self.buffered_data["images"]) == 0:
            return  # exit the function and wait to be called by the viewfinder tab.
        self._image_data = self.buffered_data["images"][0]
        self._GPIO_data = [int(x) for x in self.buffered_data["gpio_data"][0]]

        # Display the data
        self.video_feed.setImage(self._image_data.T)

        pass


    def start_timer(self):
        """Start a timer to refresh the video feed every second"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10)

    def refresh(self):
        """Refresh function for this tab"""
        self._display_preview()

    def closeEvent(self, event):
        """Handle the close event to stop the timer and release resources"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.camera_api.stop_capturing()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CameraPreviewDialog(unique_id="18360350-spinnaker" )
    dialog.exec()
    sys.exit(app.exec())
