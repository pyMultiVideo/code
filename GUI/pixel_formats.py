"""Shared pixel-format registry used across camera backends and GUI consumers."""

from dataclasses import dataclass

import cv2


@dataclass(frozen=True)
class PixelFormat:
    """Pixel format name mapping."""

    name: str  # Format name used in GUI and metadata files.
    ffmpeg: str  # Format name used in ffmpeg command line.
    cv2_code: int | None  # OpenCV color conversion code, None if monochrome.


PIXEL_FORMAT_REGISTRY = {  # Pixel format registry mapping supported format names to PixelFormat objects.
    "bayer_rggb8": PixelFormat(
        name="bayer_rggb8",
        ffmpeg="bayer_rggb8",
        cv2_code=getattr(cv2, "COLOR_BayerRG2BGR"),
    ),
    "mono8": PixelFormat(
        name="mono8",
        ffmpeg="gray",
        cv2_code=None,
    ),
}
