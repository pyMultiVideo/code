import subprocess, sys
from pathlib import Path

# Construct the command as a list of arguments
command = [
    sys.executable,  # Python executable
    Path(".") / "pyMultiVideo_GUI.pyw",  # Path to GUI
    # Test options specified
    "--data-dir",#
    '"C:\\Users\\alifa\\OneDrive - Nexus365\\Documents\\Video Aquisition Application\\spinnaker-refactor\\code\\data"',
    "--num-cameras",
    "2",
    "--camera-updates",
    str(1),
    "--camera-update-rate",
    str(20),
    "--crf",
    str(23),
    "--encoding-speed",
    "medium",
    "--compression-standard",
    "h264",
    "--downsampling-factor",
    str(3),
    "--fps",
    str(60),
    "--record-on-startup",
    "True",
    "--close-after",
    "00:05",
]

# Join the list into a single string with spaces between each element
command = " ".join(map(str, command))
print(command)
# Start the process
process = subprocess.Popen(
    command, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)  # Ensure it runs in a new process group

