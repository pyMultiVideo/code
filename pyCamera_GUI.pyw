import logging
import sys, argparse


# Set up logging
logging.basicConfig(
    level=logging.ERROR, 
    handlers=[logging.FileHandler(
             'ErrorLog.txt', 
              delay=True),], 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

# Dependancy Mangement
try:
    import PyQt6
    import pyqtgraph
    import ffmpeg
    import PySpin
    # for handling usb cameras
    import cv2_enumerate_cameras
    import cv2

except ImportError as e:
    logging.error("  Unable to import dependencies:\n\n" + str(e) + "\n\n")
    sys.exit()
        
# Import GUI now that dependancies are installed        
import GUI.GUI_main as mg
import PyQt6.QtWidgets as QtWidgets

def main(parsed_args, unparsed_args):
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    # Parse the arguments to main window
    gui = mg.GUIApp(parsed_args)
    gui.show()
    sys.excepthook = mg.GUIApp.exception_hook
    app.exec()
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the configuration file", type=str)
    '''
    Logic for config. If there is a config, instead of doing the normal init on the viewfinder tab, 
    we will load the a config file (from the state where there are not camera widgets intialised. )
    '''

    parsed_args, unparsed_args = parser.parse_known_args()
    return parsed_args, unparsed_args
    
# Run the main function if this script is run
if __name__ == '__main__':
    parsed_args, unparsed_args = parse_args()
    print(parsed_args, unparsed_args)
    main(parsed_args, unparsed_args)