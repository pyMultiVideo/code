from pathlib import Path
import json, sys, subprocess

from metadata_validation_script import get_video_frame_count

# config_path = r"C:\Users\alifa\Documents\pyMV-Local\code\data\test-photo-1\config_ncams_6_downsample_1_fps_120_update_20_upd_per_disp_2_crf_23_speed_slow_comp_h265\test_config.json"
config_path = r"C:\Users\alifa\Documents\pyMV-Local\code\data\test-photo-1\config_ncams_7_downsample_1_fps_60_update_20_upd_per_disp_4_crf_23_speed_slow_comp_h265\test_config.json"
# Load the JSON config file
with open(config_path, "r") as f:
    config_data = json.load(f)

# Construct the command as a list of arguments
command = [
    sys.executable,  # Python executable
    Path(".") / "pyMultiVideo_GUI.pyw",  # Path to GUI
    # Test options specified
    "--experiment-config",
    json.dumps(json.dumps(config_data["experiment_config"])),  # Config file passed as JSON formatted string
    "--camera-config",
    json.dumps(json.dumps(config_data["camera_config"])),  # Config file passed as JSON formatted string
    "--application-config",
    json.dumps(json.dumps(config_data["application_config"])),  # Config file passed as JSON formatted string
    "--record-on-startup",
    config_data["record-on-startup"],  # Application records on startup
    "--close-after",
    config_data["close_after"],  # Time after which the application closes
]

# Join the list into a single string with spaces between each element
command = " ".join(map(str, command))
print(command)
# Start the process
process = subprocess.Popen(
    command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)  # Ensure it runs in a new process group

process.wait()

# Get all mp4 files in the folder containing the config file
mp4_files = list(Path(config_path).parent.glob("*.mp4"))

for mp4 in mp4_files:
    metadata_file = mp4.parent / (mp4.stem + "_metadata.json")
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    frame_count = get_video_frame_count(mp4)
    if metadata_file.exists():
        recorded_frames = metadata["recorded_frames"]
        if frame_count == recorded_frames:
            print("Frame count matches recorded frame count.")
        else:
            print(f"Frame count mismatch. Recorded: {recorded_frames}, Actual: {frame_count}")
