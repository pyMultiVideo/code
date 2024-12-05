import logging
import sys
import argparse
# Dependancy Mangement
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.ERROR, 
    handlers=[logging.FileHandler(
             'ErrorLog.txt', 
              delay=True),], 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )


# Dependancy Mangement
def check_module(module_name):
    if importlib.util.find_spec(module_name) is None:
        logging.error(f"Unable to import dependency: {module_name}")
        sys.exit()

check_module('PyQt6')
check_module('pyqtgraph')
check_module('ffmpeg')
check_module('PySpin')
check_module('cv2_enumerate_cameras')
check_module('cv2')
        
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