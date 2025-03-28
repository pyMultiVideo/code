import time
from multiprocessing import Process
import serial
from collections import namedtuple


Datatuple = namedtuple("Datatuple", ["time", "type", "subtype", "content"])

class Image_processer:
    def __init__(self, camera_widget, child_conn, update_rate=1000, comport="COM1"):
        self.camera_widget = camera_widget  # reference to camera widget
        # Initalise what you want into the image processer class
        self.child_conn = child_conn
        self.update_rate = update_rate

        # Begin a file that saved data at the timestamps required
        self.output_file = open("output_log.txt", "a")
        # Open a serial port to the computer
        try:
            self.serial_port = serial.Serial(comport, baudrate=9600, timeout=1)
            print(f"Serial port {comport} opened successfully.")
        except serial.SerialException as e:
            print(f"Failed to open serial port {comport}: {e}")
            self.serial_port = None
        pass

    # Beginning and Ending processes ----------------------------------------------------------------------

    def start_process(self):
        self.process_thread = Process(target=self.process)
        self.process_thread.start()

    def terminate_process(self):
        # Function that closes the image processing
        # Sends a termination signal to stop the process loop
        self.child_conn.close()
        self.process_thread.join()
        print("Child connection closed. Image processing terminated.")

    # Python Process that runs ----------------------------------------------------------------------

    def process(self):
        """
        What will you do with the output?
        - Display on GUI
        - send as an event to pyControl
        - Save the location to disk: Save the eval of this
        """
        while True:
            start_time = time.time()

            if self.child_conn.poll():
                self.data = self.child_conn.recv()
                # Process the received data here
                print("Received data:", data)

                if "TERMINATE" in data:
                    print("Terminate signal received. Closing process.")
                    self.terminate_process()

                # Example
                processed_data = {"save_point": (100, 100)}  # Send a location to be drawn
                processed_data = {"draw_point": (100, 100)}  # Send a location to be drawn
                processed_data = {"draw_frame": None}  # byte array? np.array?
                processed_data = {"event": "poke1"}  # Send a pyControl Event
                # If you want to draw a point, send it back to the main
                self.child_conn.send(processed_data)
            elapsed_time = time.time() - start_time
            time.sleep(max(0, self.update_rate / 1000 - elapsed_time))

    # Outcome of the data -----------------------------------------------------------------------------------------------

    def save_data(self, processed_data):
        # What metadata would you save with this? the timestam
        timestamp = self.data['timestamp'] # camera timestamp
        self.output_file.write(f"{timestamp}, {processed_data}\n")
        self.output_file.flush()

    def send_event(self, event):
        # How to send pycontrol events to pycontrol task?
        if self.serial_port and self.serial_port.is_open:
            try:
                datatuple = Datatuple(time=time.time(), type="event", subtype="custom", content=event)
                self.serial_port.write(f"{datatuple}\n".encode("utf-8"))
                print(f"Datatuple '{datatuple}' sent to serial port.")
            except serial.SerialException as e:
                print(f"Failed to send datatuple '{datatuple}' to serial port: {e}")
        else:
            print("Serial port is not open. Cannot send datatuple.")

        pass
