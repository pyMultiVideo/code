import subprocess
import json
import subprocess
from pathlib import Path
from tqdm import tqdm
import csv


# Get the path to the test folder
test_dir = Path(".") / "data" / "test-photo-1"
script_path = Path(".") / "pyMultiVideo_GUI.pyw"

directories = [d.resolve() for d in test_dir.iterdir() if d.is_dir()]


def get_video_frame_count(video_path):
    """Check the number of frames in a video
    video_path: path to the mp4 file"""
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


def main():
    for dir in tqdm(directories, desc="Processing directories"):
        # Get a list of mp4 files
        mp4_files = [f for f in Path(dir).glob("*.mp4") if f.is_file()]

        for mp4 in mp4_files:
            # Get the name of the file
            frame_count = get_video_frame_count(str(mp4))
            file_name = mp4.name
            # Get the corresponding metadata (json) file
            metadata_file = mp4.with_suffix("").with_name(mp4.stem + "_metadata.json")
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            recorded_frame_count = metadata.get("recorded_frames", "N/A")
            if frame_count != recorded_frame_count:
                print(
                    f"Mismatch detected for {mp4}: Frame count ({frame_count}) != Recorded frame count ({recorded_frame_count})"
                )
                # Write mismatch info to a CSV file
                mismatch_log_path = Path("mismatches.csv")
                write_header = not mismatch_log_path.exists()
                with open(mismatch_log_path, "a", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    if write_header:
                        writer.writerow(["file", "frame_count", "recorded_frame_count"])
                    writer.writerow([str(mp4), frame_count, recorded_frame_count])


if __name__ == "__main__":
    main()
