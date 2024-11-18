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
    import ffmpeg
    import PySpin

except ImportError as e:
    logging.error("  Unable to import dependencies:\n\n" + str(e) + "\n\n")
    sys.exit()
        
# Import GUI now that dependancies are installed        
import GUI.main_gui as mg

def main(parsed_args, unparsed_args):

    app = mg.QtWidgets.QApplication(sys.argv)
    # set pyqt6 style
    app.setStyle('Fusion')
    gui = mg.GUIApp()
    # sys.excepthook = mg.GUIApp.exception_hook
    app.exec()
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the configuration file", type=str)
    
    parsed_args, unparsed_args = parser.parse_known_args()
    return parsed_args, unparsed_args
    
# Run the main function if this script is run
if __name__ == '__main__':
    parsed_args, unparsed_args = parse_args()
    
    main(parsed_args, unparsed_args)