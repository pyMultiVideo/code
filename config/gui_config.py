import shutil

# Find ffmpeg path dynamically. 
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path is None:
    raise FileNotFoundError("FFmpeg binary not found. Please install FFmpeg and ensure it's in your PATH.")
print(f"FFmpeg found at: {ffmpeg_path}")

dictionary = {
    # This has no impact of the rate at which the buffer is emptied
    "update_display_rate": 30,  # (Hz) the rate at which the function for updating the display is called.
    # For the spinnaker cameras, this is always going to be fast enough when the camera buffer is set to 10.
    # 150 Hz / 10 = 15 Hz (This would be the minimum required function-call rate to keep up)
    "video_encoder_function_call_rate": 30,  # (Hz) the rate at which the function which is called to encode the video from the buffer is called.
    # The default directory for the data from the application to be stored.
    "data_folder_directory": "data",
    # The location where the ffmpeg.exe is located. 
    "PATH_TO_FFMPEG": ffmpeg_path,
}
