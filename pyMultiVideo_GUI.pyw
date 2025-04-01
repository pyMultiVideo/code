import logging
import sys
import argparse

from config.config import gui_config

# Dependancy Mangement
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.ERROR,
    handlers=[
        logging.FileHandler("ErrorLog.txt", delay=True),
    ],
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Dependency Mangement
def check_module(module_name):
    if importlib.util.find_spec(module_name) is None:
        logging.error(f"Unable to import dependency: {module_name}")
        sys.exit()


### Terminal Commands -----------------------------------------------------------------------


def valid_time(value):
    try:
        hours, minutes = map(int, value.split(":"))
        if hours < 0 or minutes < 0 or minutes >= 60:
            raise ValueError
        return value
    except ValueError:
        raise argparse.ArgumentTypeError("Time must be in the format HH:MM with valid values.")


def parse_args():
    """
    Run the application with config option specified. By default, this overwrite options specificied in config/config.py or specific camera configs
    """
    parser = argparse.ArgumentParser()
    # Experiment options
    parser.add_argument("--experiment-config", help="Experiment_config.json")
    parser.add_argument("--data-dir", help="Path to directory which will contain the data", type=str)
    parser.add_argument("--num-cameras", help="Number of cameras launched to record at the same time", type=int)
    # Add a mutual exclusion group to ensure only --experiment-config or (--data-directory / --num_cameras) are defined
    # group = parser.add_mutually_exclusive_group(required=False)
    # group.add_argument("--experiment-config", help="Experiment_config.json")
    # group.add_argument(
    #     "--data-options",
    #     nargs=2,
    #     metavar=("data_directory", "num_cameras"),
    #     help="Specify data directory and number of cameras",
    # )

    # GUI config options
    parser.add_argument("--camera-update-rate", help="Rate at which to get new images from camera buffer", type=int)
    parser.add_argument(
        "--camera_updates_per_display_update",
        help="How often images are fetched from camera per update of video display",
        type=int,
    )
    parser.add_argument("--font-size", help="Font size to use in GUI", type=int)
    # FFMPEG config options
    parser.add_argument("--crf", help="True: Cameras start recording on startup", type=int)
    parser.add_argument(
        "--encoding-speed",
        help='Controls encoding speed vs file size, value values ["fast", "medium", "slow"]',
        type=str,
    )
    parser.add_argument("--compression-standard", help='["h265" , "h264"]', type=str)
    # Recording options
    parser.add_argument("--record-on-startup", help="if True: Cameras start recording on startup", type=bool)
    parser.add_argument(
        "--downsampling-factor",
        help="Recording downsampling factor ['1', '2', '3', '4']. If specified it will OVERWRITE the camera-config settigs for all the cameras",
        type=int,
    )
    parser.add_argument(
        "--fps",
        help="FPS (Hz) of all the cameras",
        type=int,
    )
    parser.add_argument(
        "--close-after",
        help="Amount of time the application will be open for (Specific time in HH:MM)",
        type=valid_time,
    )
    # return the arguments to the main function
    return parser.parse_known_args()


# Running Application ----------------------------------------------------------------

check_module("PyQt6")
check_module("pyqtgraph")

# Import GUI now that dependancies are verified.
import PyQt6.QtWidgets as QtWidgets
from PyQt6 import QtGui
from GUI.GUI_main import GUIMain


def main(parsed_args, unparsed_args):
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QtGui.QFont()
    font.setPixelSize(gui_config["font_size"])
    app.setFont(font)
    # Parse the arguments to main window
    gui = GUIMain(parsed_args)
    gui.show()
    sys.excepthook = gui.exception_hook
    app.exec()


# Run the main function if this script is run
if __name__ == "__main__":
    parsed_args, unparsed_args = parse_args()
    main(parsed_args, unparsed_args)
