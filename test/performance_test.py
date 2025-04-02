import subprocess, time, signal
from pathlib import Path
import json
import sys

# Get the path to the test folder
# test_dir = Path(".") / "data" / "test"
test_dir = Path(".") / "data" / "test-with-fps"
script_path = Path(".") / "pyMultiVideo_GUI.pyw"
# Get the path of the current Python executable
# python_exe = sys.executable
python_exe = r"C:/Users/alifa/miniconda3/envs/pyMultiCam_env/python.exe"

# List files in the test directory
directories = [d for d in test_dir.iterdir() if d.is_dir()]
for dir in directories:
    # Get the config file paths for the experiment
    test_path = str(dir / "test_config.json")
    with open(test_path, "r") as f:
        test_config = json.load(f)

    # Construct the command as a list of arguments
    command = [
        python_exe,  # Python executable
        script_path,  # Path to GUI
        # Test options specified
        "--data-dir",
        '"' + str(test_config["data_dir"]).replace("\\", "/") + '"',
        "--num-cameras",
        str(test_config["n_cameras"]),
        "--camera-updates",
        str(test_config["camera_updates_per_display_update"]),
        "--camera-update-rate",
        str(test_config["camera_update_rate"]),
        "--crf",
        str(test_config["crf"]),
        "--encoding-speed",
        test_config["encoding_speed"],
        "--compression-standard",
        test_config["compression_standard"],
        "--downsampling-factor",
        str(test_config["downsampling_factor"]),
        "--fps",
        str(test_config["fps"]),
        "--record-on-startup",
        "True",
        "--close-after",
        test_config["close_after"],
    ]

    # Join the list into a single string with spaces between each element
    command = " ".join(map(str, command))
    print(command)
    print("TEST START")
    # Start the process
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )  # Ensure it runs in a new process group
    try:
        while process.poll() is None:
            time.sleep(1)  # Wait for the process to finish
    except Exception as e:
        print(f"An error occurred: {e}")
    # break

    print("TEST END")
