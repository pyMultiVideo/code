"""Shared canonical pixel-format registry used across camera backends and GUI consumers."""

import cv2


PIXEL_FORMAT_REGISTRY = {
    "bayer_rggb8": {
        "display_name": "Bayer RG8",
        "ffmpeg": "bayer_rggb8",
        "cv2_code": getattr(cv2, "COLOR_BayerRG2BGR"),
    },
    "gray": {
        "display_name": "Mono 8",
        "ffmpeg": "gray",
        "cv2_code": None,
    },
}

DEFAULT_PIXEL_FORMAT_PRIORITY = [
    "bayer_rggb8",
    "gray",
]


def get_pixel_format_info(pixel_format_key: str) -> dict:
    """Return the canonical metadata for a pixel-format key."""
    return PIXEL_FORMAT_REGISTRY[pixel_format_key]
