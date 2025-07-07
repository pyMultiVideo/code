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


def open_error_dialog():
    """Startup error dialog"""
    app = QApplication(sys.argv)
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Application Startup Error")
    msg_box.setTextFormat(Qt.TextFormat.RichText)
    msg_box.setText(
        "An error occurred while starting the application.<br>"
        'Please check <a href="ErrorLog.txt">ErrorLog.txt</a> for more details.'
    )
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


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
    # Experiment Config
    parser.add_argument("--experiment-config", help="Path to the experiment configuration file in JSON format")
    # Camera Conifg
    parser.add_argument("--camera-config", help="Path to the camera configuration file in JSON format", type=str)
    # Config.py
    parser.add_argument(
        "--application-config", help="Path to the application configuration file in JSON format", type=str
    )
    # Recording options
    parser.add_argument("--record-on-startup", help="if true: Cameras start recording on startup", type=bool)
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
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6 import QtGui
from GUI.GUI_main import GUIMain


def main(parsed_args, unparsed_args):
    app = QApplication(sys.argv)
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
    try:
        parsed_args, unparsed_args = parse_args()
        main(parsed_args, unparsed_args)
    except Exception as e:
        logging.error("Startup failure", exc_info=True)
        open_error_dialog()
        sys.exit()
