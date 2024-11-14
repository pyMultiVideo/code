import PySpin
from moviepy.editor import VideoFileClip

def configure_camera_from_config(cam, config: dict) -> None:
    # Set width and height if available
    if cam.Width and cam.Width.GetAccessMode() == PySpin.RW and "width" in config:
        cam.Width.SetValue(config["width"])
    if cam.Height and cam.Height.GetAccessMode() == PySpin.RW and "height" in config:
        cam.Height.SetValue(config["height"])

    # Set frame rate if available
    if cam.AcquisitionFrameRateEnable and cam.AcquisitionFrameRateEnable.GetAccessMode() == PySpin.RW:
        cam.AcquisitionFrameRateEnable.SetValue(True)
    if cam.AcquisitionFrameRate and cam.AcquisitionFrameRate.GetAccessMode() == PySpin.RW and "frame_rate" in config:
        cam.AcquisitionFrameRate.SetValue(config["frame_rate"])

    # Set exposure time if available
    if cam.ExposureAuto and cam.ExposureAuto.GetAccessMode() == PySpin.RW:
        cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
    if cam.ExposureTime and cam.ExposureTime.GetAccessMode() == PySpin.RW and "exposure_time" in config:
        cam.ExposureTime.SetValue(config["exposure_time"])

    # Set gain if available
    if cam.GainAuto and cam.GainAuto.GetAccessMode() == PySpin.RW:
        cam.GainAuto.SetValue(PySpin.GainAuto_Off)
    if cam.Gain and cam.Gain.GetAccessMode() == PySpin.RW and "gain" in config:
        cam.Gain.SetValue(config["gain"])
        
        
def get_video_duration(video_path):
    clip = VideoFileClip(video_path)
    duration = clip.duration  # Duration in seconds
    clip.close()
    
    return duration


from PyQt6.QtCore import QEvent, Qt, QObject

class EnterKeyFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Return:
            return True
        return super().eventFilter(obj, event)