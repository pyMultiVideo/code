import os
import csv
import json
import shutil
import subprocess
import numpy as np
from datetime import datetime

# Check GPU availibility for video encode and set which encoders to use.

try:
    subprocess.check_output("nvidia-smi")
    ffmpeg_encoder_map = {
        "h264": "h264_nvenc",
        "h265": "hevc_nvenc",
    }
    GPU_AVAILABLE = True
except Exception:
    ffmpeg_encoder_map = {
        "h264": "libx264",
        "h265": "libx265",
    }
    GPU_AVAILABLE = False

# -------------------------------------------------------------------------------------
# Data recorder
# -------------------------------------------------------------------------------------


class Data_recorder:
    """Class for recording video data, GPIO pinstates and metadata."""

    def __init__(self, camera_widget):
        self.camera_widget = camera_widget

    def start_recording(self, subject_id, save_dir, settings):
        """Open data files and FFMPEG process"""
        self.settings = settings
        self.recorded_frames = 0
        self.dropped_frames = 0
        # Create Filepaths_config.
        self.subject_id = subject_id
        self.record_start_time = datetime.now()
        filename_stem = f"{self.subject_id}_{self.record_start_time.strftime('%Y-%m-%d-%H%M%S')}"
        self.video_filepath = os.path.join(save_dir, filename_stem + ".mp4")
        self.GPIO_filepath = os.path.join(save_dir, filename_stem + "_GPIO_data.csv")
        self.metadata_filepath = os.path.join(save_dir, filename_stem + "_metadata.json")

        # Open GPIO file and write header data.
        self.gpio_file = open(self.GPIO_filepath, mode="w", newline="")
        self.gpio_writer = csv.writer(self.gpio_file)
        self.gpio_writer.writerow([f"GPIO{pin}" for pin in range(1, self.camera_widget.camera_api.N_GPIO + 1)])

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
            "device_model": self.camera_widget.camera_api.device_model,
            "device_serial_number": self.camera_widget.camera_api.serial_number,
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
        self.downsampled_width = self.camera_widget.camera_width // self.settings.downsampling_factor
        self.downsampled_height = self.camera_widget.camera_height // self.settings.downsampling_factor
        ffmpeg_command = " ".join(
            [
                self.camera_widget.GUI.ffmpeg_path,  # Path to binary
                "-f rawvideo",  # Input codec (raw video)
                f"-s {self.camera_widget.camera_width}x{self.camera_widget.camera_height}",  # Input frame size
                f"-pix_fmt {self.camera_widget.camera_api.supported_pixel_formats[self.settings.pixel_format]}",  # Input Pixel Format: 8-bit grayscale input to ffmpeg process. Input array 1D
                f"-r {self.settings.fps}",  # Frame rate
                "-i -",  # input comes from a pipe (stdin)
                f"-c:v {ffmpeg_encoder_map[self.camera_widget.GUI.ffmpeg_config['compression_standard']]}",  # Output codec
                f"-s {self.downsampled_width}x{self.downsampled_height}",  # Output frame size after any downsampling.
                "-pix_fmt yuv420p",  # Output pixel format
                f"-preset {self.camera_widget.GUI.ffmpeg_config['encoding_speed']}",  # Encoding speed [fast, medium, slow]
                f"-b:v 0 ",  # Encoder uses variable bit rate https://superuser.com/questions/1236275/how-can-i-use-crf-encoding-with-nvenc-in-ffmpeg
                (
                    f"-cq {self.camera_widget.GUI.ffmpeg_config['crf']}"
                    if GPU_AVAILABLE
                    else f"-crf {self.camera_widget.GUI.ffmpeg_config['crf']}"
                ),  # Controls quality vs filesize
                f'"{self.video_filepath}"',  # Output file path
            ]
        )
        print("FFMPEG_CONFIG", self.camera_widget.GUI.ffmpeg_config)
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

    def stop_recording(self) -> None:
        """Close data files and FFMPEG process."""
        end_time = datetime.now()
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

    def record_new_images(self, new_images):
        """Record newly aquired images and GPIO pinstates."""
        self.recorded_frames += len(new_images["images"])
        # Concatenate the list of numpy buffers into one bytestream
        frame = np.concatenate([img for img in new_images["images"]])
        self.ffmpeg_process.stdin.write(frame)
        for gpio_pinstate in new_images["gpio_data"]:  # Write GPIO pinstate to file.
            self.gpio_writer.writerow(gpio_pinstate)
