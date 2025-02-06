dictionary = {
    "input": {},
    "output": {
        # Encoders available to ffmpeg 
        # {'GUI Name: ffmpeg_encoder name'}
        "encoder": {
            "GPU (H264)": "h264_nvenc",
            "GPU (H265)": "hevc_nvenc",
            "CPU (H264)": "libx264",
            "CPU (H265)": "libx265",
        },
        "pxl_fmt": {"yuv420p": "yuv420p"},
    },
}
