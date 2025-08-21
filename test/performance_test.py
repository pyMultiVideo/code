import subprocess, time
from pathlib import Path
import json
import sys
from tqdm import tqdm
import fire


def run_performance_test(test_dir="data/test-large", script_path="pyMultiVideo_GUI.pyw"):
    test_dir = Path(test_dir)
    script_path = Path(script_path)

    directories = [d.resolve() for d in test_dir.iterdir() if d.is_dir()]

    total_runtime = 0
    for dir in directories:
        test_path = dir / "test_config.json"
        with open(test_path, "r") as f:
            config_data = json.load(f)
        minutes, seconds = map(int, config_data["close_after"].split(":"))
        total_runtime += int(config_data["close_after"].replace(":", ""))

    hours = total_runtime // 3600
    minutes = (total_runtime % 3600) // 60
    seconds = total_runtime % 60
    print(f"Approximate total runtime of the test: {hours} hours, {minutes} minutes, and {seconds} seconds")

    for dir in tqdm(directories, desc="Processing directories"):
        test_path = dir / "test_config.json"
        with open(test_path, "r") as f:
            config_data = json.load(f)

        command = [
            sys.executable,
            script_path,
            "--experiment-config",
            json.dumps(json.dumps(config_data["experiment_config"])),
            "--camera-config",
            json.dumps(json.dumps(config_data["camera_config"])),
            "--application-config",
            json.dumps(json.dumps(config_data["application_config"])),
            "--record-on-startup",
            config_data["record-on-startup"],
            "--close-after",
            config_data["close_after"],
        ]

        command = " ".join(map(str, command))
        process = subprocess.Popen(command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        try:
            while process.poll() is None:
                time.sleep(1)
        except Exception as e:
            print(f"An error occurred: {e}")

        print(f"Finished processing directory: {dir.name}")


if __name__ == "__main__":
    fire.Fire(run_performance_test)
