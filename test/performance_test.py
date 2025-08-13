import subprocess, time
from pathlib import Path
import json
import sys
from tqdm import tqdm

# Get the path to the test folder
test_dir = Path(".") / "data" / "test-large"
script_path = Path(".") / "pyMultiVideo_GUI.pyw"
pmv_env = r"C:/Users/alifa/miniconda3/envs/pyMultiCam_env/python.exe"  # Location of pyMultiVideo Environment

# List files in the test directory
directories = [d.resolve() for d in test_dir.iterdir() if d.is_dir()]

# Calculate the approximate run time of the test
total_runtime = 0
for dir in directories:
    test_path = str(dir / "test_config.json")
    with open(test_path, "r") as f:
        config_data = json.load(f)
    minutes, seconds = map(int, config_data["close_after"].split(":"))
    total_runtime += int(config_data["close_after"].replace(":", ""))

hours = total_runtime // 3600
minutes = (total_runtime % 3600) // 60
seconds = total_runtime % 60
print(f"Approximate total runtime of the test: {hours} hours, {minutes} minutes, and {seconds} seconds")

for dir in tqdm(directories, desc="Processing directories"):
    # Get the config file paths for the experiment
    test_path = str(dir / "test_config.json")
    with open(test_path, "r") as f:
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

    print(f"Finished processing directory: {dir.name}")
