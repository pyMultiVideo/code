import os
import csv
import json
import subprocess
import numpy as np
from datetime import datetime

from camera_api.generic_camera import FrameData

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
        self.ffmpeg_config = self.camera_widget.GUI.ffmpeg_config

    def start_recording(self, subject_id, save_dir, settings):
        """Open data files and launches FFMPEG process"""
        self.settings = settings
        self.recorded_frames = 0
        self.dropped_frames = 0
        self.camera_buffer_overflow_occurred = False
        self.ffmpeg_buffer_overflow_occurred = False
        self.first_timestamp = None
        self.first_frame_number = None
        # Create Filepaths_config.
        self.subject_id = subject_id
        self.record_start_time = datetime.now()
        filename_stem = f"{self.subject_id}_{self.record_start_time.strftime('%Y-%m-%d-%H%M%S')}"
        self.video_filepath = os.path.join(save_dir, filename_stem + ".mp4")
        self.GPIO_filepath = os.path.join(save_dir, filename_stem + "_frame_info.csv")
        self.metadata_filepath = os.path.join(save_dir, filename_stem + "_metadata.json")

        # Open GPIO file and write header data.
        self.gpio_file = open(self.GPIO_filepath, mode="w", newline="")
        self.gpio_writer = csv.writer(self.gpio_file)
        self.gpio_writer.writerow(
            ["number"] + [f"GPIO{pin}" for pin in range(1, self.camera_widget.camera_api.N_GPIO + 1)] + ["timestamp"]
        )

        # Create metadata file.
        self.metadata = {
            "subject_ID": self.subject_id,
            # Camera Config Settings
            "camera_unique_id": self.settings.unique_id,
            "camera_name": self.settings.name,
            "FPS": "external_trigger" if self.settings.external_trigger else int(self.settings.fps),
            "exposure_time": self.settings.exposure_time,
            "gain": self.settings.gain,
            "pixel_format": self.camera_widget.camera_api.pixel_format.name,
            "device_model": self.camera_widget.camera_api.device_model,
            "device_serial_number": self.camera_widget.camera_api.serial_number,
            # Recording information
            "start_time": self.record_start_time.isoformat(timespec="milliseconds"),
            "end_time": None,
            "duration": None,
            "recorded_frames": 0,
            "dropped_frames": None,
            "camera_buffer_overflow": False,
            "ffmpeg_buffer_overflow": False,
            # FFMPEG config settings
            "downsampling_factor": self.settings.downsampling_factor,
            "compression_standard": self.ffmpeg_config["compression_standard"],
            "encoding_speed": self.ffmpeg_config["encoding_speed"],
            "encoding_crf": self.ffmpeg_config["crf"],
        }
        with open(self.metadata_filepath, "w") as meta_data_file:
            json.dump(self.metadata, meta_data_file, indent=4)

        # Initalise ffmpeg process
        self.downsampled_width = self.camera_widget.image_width // self.settings.downsampling_factor
        self.downsampled_height = self.camera_widget.image_height // self.settings.downsampling_factor
        ffmpeg_command = " ".join(
            [
                self.camera_widget.GUI.ffmpeg_path,  # Path to binary
                "-f rawvideo",  # Input codec (raw video)
                f"-s {self.camera_widget.image_width}x{self.camera_widget.image_height}",  # Input frame size
                f"-pix_fmt {self.camera_widget.camera_api.pixel_format.ffmpeg}",  # Input pixel format for ffmpeg
                f"-r {self.settings.fps}",  # Frame rate
                "-i -",  # input comes from a pipe (stdin)
                f"-c:v {ffmpeg_encoder_map[self.ffmpeg_config['compression_standard']]}",  # Codec
                f"-s {self.downsampled_width}x{self.downsampled_height}",  # Output frame size after any downsampling.
                "-pix_fmt yuv420p",  # Output pixel format
                f"-preset {self.ffmpeg_config['encoding_speed']}",  # Enc. speed [fast, medium, slow]
                (
                    f"-cq {self.ffmpeg_config['crf']}" if GPU_AVAILABLE else f"-crf {self.ffmpeg_config['crf']}"
                ),  # Controls quality vs filesize
                f'"{self.video_filepath}"',  # Output file path
            ]
        )
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
        self.metadata["camera_buffer_overflow"] = self.camera_buffer_overflow_occurred
        self.metadata["ffmpeg_buffer_overflow"] = self.ffmpeg_buffer_overflow_occurred

        with open(self.metadata_filepath, "w") as self.meta_data_file:
            json.dump(self.metadata, self.meta_data_file, indent=4)
        # Close FFMPEG process
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()

    def record_new_images(self, new_frames: list[FrameData], camera_new_dropped_frames=0, ffmpeg_new_dropped_frames=0):
        """Record newly aquired images and GPIO pinstates."""
        if self.first_timestamp is None:
            self.first_timestamp = new_frames[0].timestamp
            self.first_frame_number = new_frames[0].number - 1

        self.recorded_frames += len(new_frames)
        self.dropped_frames += camera_new_dropped_frames + ffmpeg_new_dropped_frames
        if camera_new_dropped_frames:
            self.camera_buffer_overflow_occurred = True
        if ffmpeg_new_dropped_frames:
            self.ffmpeg_buffer_overflow_occurred = True
        # Concatenate the list of numpy buffers into one bytestream and pass to ffmpeg.
        images = np.concatenate([frame_data.image for frame_data in new_frames])
        self.ffmpeg_process.stdin.write(images)
        # Write frame metadata to csv file.
        for frame_data in new_frames:
            rel_timestamp = frame_data.timestamp - self.first_timestamp
            rel_frame_number = frame_data.number - self.first_frame_number
            gpio = [] if self.camera_widget.camera_api.N_GPIO == 0 else list(frame_data.GPIO_pinstate.astype(int))
            self.gpio_writer.writerow([rel_frame_number] + gpio + [rel_timestamp])
