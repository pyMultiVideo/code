import time
import threading
from collections import deque
from typing import Optional

import cv2
import numpy as np

from .generic_camera import FrameData, GenericCamera

_MAX_CAMERA_SCAN = 10
_FRAME_BUFFER_MAX = 256

cv2.setLogLevel(0)  # Turn of warnings if camera not found at specified index.


class WebcamCamera(GenericCamera):
    """Generic webcam backend based on OpenCV VideoCapture."""

    def __init__(self, serial_number: str):
        super().__init__(serial_number)

        self.device_model = "Webcam"
        self.N_GPIO = 0
        self.has_manual_control = {
            "fps": True,
            "exposure": False,
            "gain": False,
            "trigger": False,
        }
        self.pixel_format_aliases = {
            "bayer_rggb8": "bayer_rggb8",
            "mono8": "mono8",
        }
        self._active_pixel_format = "bayer_rggb8"

        self._device_index = int(serial_number)
        self._cam = _open_capture(self._device_index)
        if self._cam is None:
            raise RuntimeError(f"Unable to open webcam index {self._device_index}")

        self.image_width = int(self._cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.image_height = int(self._cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Some drivers report 0x0 until the first successful frame grab.
        if self.image_width <= 0 or self.image_height <= 0:
            ok, frame = self._cam.read()
            if ok and frame is not None:
                self.image_height, self.image_width = frame.shape[:2]
            else:
                self.close()
                raise RuntimeError(f"Unable to read initial frame from webcam index {self._device_index}")

        self._frame_number = 0
        self._target_fps = 30.0
        self._buffer_lock = threading.Lock()
        self._frame_buffer: deque[FrameData] = deque(maxlen=_FRAME_BUFFER_MAX)
        self._capture_stop_event = threading.Event()
        self._capture_thread: Optional[threading.Thread] = None
        self.initialize_preferred_pixel_format()

        print(f"Webcam {self.serial_number} initialised")

    # Parameter getters ------------------------------------------------------------------------------

    def get_frame_rate_range(self) -> tuple[int, int]:
        """Return a conservative frame-rate range for webcam controls."""
        return (1, 30)

    def get_exposure_time(self) -> Optional[float]:
        return None

    def get_exposure_time_range(self) -> tuple[int, int]:
        # UI needs a numeric range even when manual exposure control is disabled.
        return (1, 1_000_000)

    def get_gain(self) -> Optional[float]:
        return None

    def get_gain_range(self) -> tuple[int, int]:
        # UI needs a numeric range even when manual gain control is disabled.
        return (0, 100)

    def _get_supported_pixel_formats(self) -> list[str]:
        return ["bayer_rggb8", "mono8"]

    def _get_camera_pixel_format(self) -> str:
        return self._active_pixel_format

    # Parameter setters ------------------------------------------------------------------------------

    def set_frame_rate(self, frame_rate: int) -> None:
        self._target_fps = max(1.0, float(frame_rate))
        # Many webcam drivers treat this as best-effort.
        self._cam.set(cv2.CAP_PROP_FPS, self._target_fps)

    def set_exposure_time(self, *exposure_time) -> None:
        raise NotImplementedError("Manual exposure control is not supported for this webcam backend.")

    def set_gain(self, gain) -> None:
        raise NotImplementedError("Manual gain control is not supported for this webcam backend.")

    def set_external_trigger_enable(self, enable: bool) -> None:
        if enable:
            raise NotImplementedError("Webcams do not support external trigger input.")

    def _set_pixel_format(self, pixel_format: str) -> None:
        if pixel_format not in {"mono8", "bayer_rggb8"}:
            raise ValueError(f"Unsupported webcam pixel format: {pixel_format}")
        self._active_pixel_format = pixel_format

    # Camera control ---------------------------------------------------------------------------------

    def begin_capturing(self) -> None:
        if self._cam is None or not self._cam.isOpened():
            self._cam = _open_capture(self._device_index)
            if self._cam is None:
                raise RuntimeError(f"Unable to reopen webcam index {self._device_index}")
            self.image_width = int(self._cam.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.image_height = int(self._cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self._capture_thread is not None and self._capture_thread.is_alive():
            return

        self._capture_stop_event.clear()
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            name=f"webcam-{self._device_index}",
            daemon=True,
        )
        self._capture_thread.start()

    def stop_capturing(self) -> None:
        self._capture_stop_event.set()
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=1.0)
            self._capture_thread = None
        self._cam.release()
        self._cam = None

    def get_available_images(self) -> list[FrameData]:
        with self._buffer_lock:
            if not self._frame_buffer:
                return []
            frames = list(self._frame_buffer)
            self._frame_buffer.clear()
        return frames

    def close(self):
        self.stop_capturing()

    def _capture_loop(self):
        """Capture frames in a background thread and enqueue FrameData for GUI polling."""
        next_capture_time = time.perf_counter()
        while not self._capture_stop_event.is_set():
            if self._cam is None or not self._cam.isOpened():
                break
            frame_start_time = time.perf_counter()
            ok, frame = self._cam.read()
            # Avoid a tight spin loop if camera read fails repeatedly.
            if not ok or frame is None:
                self._capture_stop_event.wait(0.01)
                continue
            # Convert pixel format.
            if self._active_pixel_format == "mono8":
                if frame.ndim == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                frame = _to_bayer_rggb8(frame)
            # Make FrameData object and put in frame buffer.
            frame_data = FrameData(
                image=np.asarray(frame, dtype=np.uint8).reshape(-1),
                GPIO_pinstate=None,
                timestamp=time.monotonic_ns() // 1000,
                number=self._frame_number,
            )
            self._frame_number += 1
            with self._buffer_lock:
                self._frame_buffer.append(frame_data)
            # Pace capture to requested FPS.
            target_interval = 1.0 / max(self._target_fps, 1.0)
            next_capture_time = max(next_capture_time + target_interval, frame_start_time + target_interval)
            wait_time = next_capture_time - time.perf_counter()
            if wait_time > 0:
                self._capture_stop_event.wait(wait_time)


def _to_bayer_rggb8(frame: np.ndarray) -> np.ndarray:
    """Convert a webcam frame into a single-channel Bayer RGGB mosaic."""
    if frame.ndim == 2:
        return frame
    if frame.ndim == 3 and frame.shape[2] == 4:
        frame = frame[:, :, :3]
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(f"Unsupported webcam frame shape for Bayer conversion: {frame.shape}")
    # OpenCV returns BGR; map channels into an RGGB Bayer pattern.
    bgr = np.asarray(frame, dtype=np.uint8)
    bayer = np.empty(bgr.shape[:2], dtype=np.uint8)
    bayer[0::2, 0::2] = bgr[0::2, 0::2, 2]  # R
    bayer[0::2, 1::2] = bgr[0::2, 1::2, 1]  # G
    bayer[1::2, 0::2] = bgr[1::2, 0::2, 1]  # G
    bayer[1::2, 1::2] = bgr[1::2, 1::2, 0]  # B
    return bayer


def _open_capture(index: int):
    """Open webcam using backend hints appropriate for the current platform."""
    for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]:
        cam = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
        if cam.isOpened():
            return cam
        cam.release()
    return None


def list_available_cameras(VERBOSE=False) -> list[str]:
    """Discover webcam indices available through OpenCV VideoCapture."""
    serial_number_list = []
    for index in range(_MAX_CAMERA_SCAN):
        cam = _open_capture(index)
        if cam is None:
            break
        serial_number_list.append(str(index))
        if VERBOSE:
            print(f"Webcam found at index: {index}")
    if VERBOSE:
        print(f"Number of webcams detected: {len(serial_number_list)}")
    return serial_number_list


def initialise_camera_api(serial_number):
    """Instantiate the WebcamCamera object."""
    return WebcamCamera(serial_number=serial_number)
