import PySpin



def read_gpio_state(camera, line_name):
    try:
        # Select the desired line (pin) to read the status
        node_line_selector = PySpin.CEnumerationPtr(camera.GetNodeMap().GetNode("LineSelector"))
        if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsWritable(node_line_selector):
            print("Error: LineSelector not available or writable.")
            return None

        line_entry = node_line_selector.GetEntryByName(line_name)
        if not PySpin.IsAvailable(line_entry) or not PySpin.IsReadable(line_entry):
            print(f"Error: {line_name} not available.")
            return None
        
        
        
        node_line_selector.SetIntValue(line_entry.GetValue())
        
        # Read the status of the selected line
        node_line_status = PySpin.CBooleanPtr(camera.GetNodeMap().GetNode("LineStatus"))
        if not PySpin.IsAvailable(node_line_status) or not PySpin.IsReadable(node_line_status):
            print("Error: LineStatus not available or readable.")
            return None
        line_state = node_line_status.GetValue()
        print(f"{line_name} state: {line_state}")
        # return line_state
        
    except PySpin.SpinnakerException as ex:
        print(f"Error: {ex}")
        return None


def read_all_gpio_states(camera):
    try:
        
        node_line_selector = PySpin.CEnumerationPtr(camera.GetNodeMap().GetNode("LineSelector"))
        if not PySpin.IsAvailable(node_line_selector) or not PySpin.IsWritable(node_line_selector):
            print("Error: LineSelector not available or writable.")
            return None
        
        line_entries = node_line_selector.GetEntries()
        
        gpio_states = {}
        
        for line_entry in line_entries:
            line_name = line_entry.GetName()
            # node_line_selector.SetIntValue(line_entry.GetName())
            
            # Read the status of the selected line
            node_line_status = PySpin.CBooleanPtr(camera.GetNodeMap().GetNode("LineStatus"))
            if not PySpin.IsAvailable(node_line_status) or not PySpin.IsReadable(node_line_status):
                print("Error: LineStatus not available or readable.")
                return None
            line_state = node_line_status.GetValue()
            print(f"{line_name}: {line_state}")
            
        print(gpio_states)
    
    except PySpin.SpinnakerException as ex:
        print(f"Error: {ex}")
        return None
    
# Main program
system = PySpin.System.GetInstance()
cam_list = system.GetCameras()

if cam_list.GetSize() > 0:
    camera = cam_list.GetByIndex(0)
    camera.Init()

    # Read the states of Line3 and Line4 (assumed to correspond to pins 3 and 4)
    # read_gpio_state(camera, "Line0")
    # read_gpio_state(camera, "Line1")
    # read_gpio_state(camera, "Line2")
    # read_gpio_state(camera, "Line3")

    read_all_gpio_states(camera)

    # Deinitialize and release the camera
    camera.DeInit()
    # camera.Release()
else:
    print("No cameras found.")

# Release system instance
system.ReleaseInstance()
