import subprocess
import json
import subprocess
from pathlib import Path
from tqdm import tqdm

# Get the path to the test folder
test_dir = Path(".") / "data" / "test-large"
script_path = Path(".") / "pyMultiVideo_GUI.pyw"

directories = [d.resolve() for d in test_dir.iterdir() if d.is_dir()]


# Use FFMPROBE to get the number of frames from thje file
def get_video_frame_count(video_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=nb_read_frames",
        "-of",
        "default=nokey=1:noprint_wrappers=1",
        video_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


for dir in tqdm(directories, desc="Processing directories"):
    # Get a list of mp4 files
    mp4_files = [f for f in Path(dir).glob("*.mp4") if f.is_file()]

    for mp4 in mp4_files:
        # Get the name of the file
        frame_count = get_video_frame_count(str(mp4))
        file_name = mp4.name
        # Get the corresponding metadata (json) file
        metadata_file = mp4.with_suffix(".json")
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

        recorded_frame_count = metadata.get("frames_recorded", "N/A")
        print(f"File: {mp4} | Frame count: {frame_count} | Recorded frame count: {recorded_frame_count}")
