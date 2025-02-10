# core python
import csv
import sys
import json
import subprocess
import logging
from datetime import datetime
import os
from collections import deque

# video
import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QIcon, QFont

# gui
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from .message_dialogs import show_warning_message
from tools import cbox_update_options
from tools import CameraSetupConfig
from tools import init_camera_api
from config import ffmpeg_config_dict
from config import gui_config_dict
from config import paths_config_dict


class ViewfinderWidget(QWidget):
    """
    Widget for each camera to be viewed
    """

    def __init__(
        self,
        parent,
        label,
        subject_id,
    ):
        super(ViewfinderWidget, self).__init__(parent)
        self.view_finder = parent
        self.camera_setup_tab = self.view_finder.GUI.camera_setup_tab
        # Camera object is the camera api that is being used that has generic versions of the core functions
        self.logger = logging.getLogger(__name__)
        self.paths = paths_config_dict
        # Camera attributes
        self.label = label
        self.subject_id = subject_id
        # Check if the camera label is in the database. If is it, we can use the Settings Config information
        # to set the camera settings.

        if self.label in self.camera_setup_tab.get_camera_labels():
            self.camera_settings = self.camera_setup_tab.getCameraSettingsConfig(
                self.label
            )
        self.fps = self.camera_settings.fps
        self.pxl_fmt = self.camera_settings.pxl_fmt
        self.unique_id = self.camera_settings.unique_id
        self.downsampling_factor = 1

        self.camera_api = init_camera_api(self.unique_id, self.camera_settings)

        self.cam_width = self.camera_api.width
        self.cam_height = self.camera_api.height

        # Layout

        self.video_feed = pg.ImageView()
        self.video_feed.ui.histogram.hide()
        self.video_feed.ui.roiBtn.hide()
        self.video_feed.ui.menuBtn.hide()
        # Disable zoom and pan
        self.video_feed.view.setMouseEnabled(x=False, y=False)
        # Recording Information
        self.recording_status_item = pg.TextItem()
        self.recording_status_item.setPos(10, 10)
        self.video_feed.addItem(self.recording_status_item)
        self.recording_status_item.setText("NOT RECORDING", color="r")

        """Initialise the GPIO data"""
        # Initial state of the colour painted to the image
        self.gpio_over_lay_color = np.random.randint(0, 256, size=3)

        self.gpio_status_item = pg.TextItem()
        self.gpio_status_font = QFont()
        self.gpio_status_item.setPos(10, 70)
        self.video_feed.addItem(self.gpio_status_item)
        self.gpio_status_item.setText("GPIO Status", color="purple")

        self.gpio_status_indicator = pg.TextItem()
        self.gpio_status_font = QFont()
        self.gpio_status_indicator.setPos(170, 70)
        self.video_feed.addItem(self.gpio_status_indicator)

        self.recording_time_text = pg.TextItem()
        self.recording_time_text.setPos(200, 10)
        self.video_feed.addItem(self.recording_time_text)
        self.recording_time_text.setText("", color="r")

        # Framerate information
        self.frame_rate_text = pg.TextItem()
        self.frame_rate_text.setPos(10, 40)
        self.video_feed.addItem(self.frame_rate_text)
        self.frame_rate_text.setText("FPS:", color="r")

        self.camera_setup_groupbox = QGroupBox(f"{self.label}")

        # Header Layout for groupbox
        self.camera_header_layout = QHBoxLayout()

        # Subject ID
        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_text = QTextEdit()
        self.subject_id_text.setFixedHeight(30)
        self.subject_id_text.setText(self.subject_id)
        self.subject_id_text.textChanged.connect(self.update_subject_id)

        # Button for recording video
        self.start_recording_button = QPushButton("")
        self.start_recording_button.setIcon(
            QIcon(os.path.join(self.paths["assets_dir"], "record.svg"))
        )
        self.start_recording_button.setFixedWidth(30)
        # self.start_recording_button.setFixedHeight(30)
        self.start_recording_button.setEnabled(False)
        self.start_recording_button.clicked.connect(self.start_recording)

        # Button for stopping recording
        self.stop_recording_button = QPushButton("")
        self.stop_recording_button.setIcon(
            QIcon(os.path.join(self.paths["assets_dir"], "stop.svg"))
        )
        self.stop_recording_button.setFixedWidth(30)
        # self.stop_recording_button.setFixedHeight(30)
        self.stop_recording_button.setEnabled(False)
        self.stop_recording_button.clicked.connect(self.stop_recording)

        self.camera_id_label = QLabel("Camera ID:")
        # Dropdown for selecting the camera
        self.camera_dropdown = QComboBox()
        # set the current text to the camera label
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)
        self.update_camera_dropdown()
        self.camera_dropdown.setCurrentText(self.label)
        # Add the widgets to the layout
        self.camera_header_layout.addWidget(self.camera_id_label)
        self.camera_header_layout.addWidget(self.camera_dropdown)
        self.camera_header_layout.addWidget(self.subject_id_label)
        self.camera_header_layout.addWidget(self.subject_id_text)
        self.camera_header_layout.addWidget(self.start_recording_button)
        self.camera_header_layout.addWidget(self.stop_recording_button)
        # Set the layout for the groupbox
        self.camera_setup_groupbox.setLayout(self.camera_header_layout)
        self.camera_setup_groupbox.setFixedHeight(75)

        self.camera_setup_hlayout = QVBoxLayout()

        self.camera_setup_hlayout.addWidget(self.camera_setup_groupbox)
        self.camera_setup_hlayout.addWidget(self.video_feed)

        self.setLayout(self.camera_setup_hlayout)
        self._init_recording()

    def _init_recording(self):
        # Set the recording flag to False
        self.recording = False
        # Default width and hieght for the camera widget
        self.width = self.cam_width
        self.height = self.cam_height

        self.validate_subject_id_input()

        self.camera_api.begin_capturing()
        # self.display_frame(self.camera_object.get_next_image())

        # initialise an object for keeping track of framerates
        self.frame_timestamps = deque(maxlen=10)
        self.FRAMERATEWARNINGSUPPRESSED = False

    def fetch_image_data(self) -> None:
        """
        Function that gets both the GPIO and the image data from the camera and sends them
        to the encoding function to be saved to disk.

        The current implementation calls the camera API to empty its buffer.
        The first image from this buffer is saved to the attribute 'self.img_buffer'
        This can then be used to display the image to the GUI.

        """
        try:
            # Retrieve the latest image from the camera
            self.buffered_data = self.camera_api.get_available_images()
            if len(self.buffered_data["images"]) == 0:
                return  # exit the function and wait to be called by the viewfinder tab.
            # Assign the first image of to the data to be displayed
            self._image_data = self.buffered_data["images"][0]
            self._GPIO_data = [int(x) for x in self.buffered_data["gpio_data"][0]]
            self.display_average_frame_rate()
            self.display_recording_time()
            # If the recording flag is True
            if self.recording is True:
                self.recorded_frames += len(self.buffered_data["timestamps"])
                # encode the frames
                self.encode_frame_from_camera_buffer(
                    frame_buffer=self.buffered_data["images"]
                )
                # encode the GPIO data
                self.write_gpio_data_from_buffer(
                    gpio_buffer=self.buffered_data["gpio_data"]
                )
        except Exception as e:
            print(f"Error fetching image data: {e}")
            # print(self.camera_object.buffer_list)

            pass

    def display_average_frame_rate(self):
        """
        Function that checks if the rate of frame aquisiton is as correct.
        This is being done using the `self.timestamps` list.

        Note: The framerate being less than the required framerate is good because is it aquring faster than required.

        """
        self.frame_timestamps.extend(self.buffered_data["timestamps"])

        # Calculate the time differences between consecutive timestamps
        time_diffs = [
            (self.frame_timestamps[i + 1] - self.frame_timestamps[i]).total_seconds()
            for i in range(len(self.frame_timestamps) - 1)
        ]
        # Calculate the average time difference
        avg_time_diff = sum(time_diffs) / len(time_diffs)

        # Calculate the framerate
        calculated_framerate = 1 / avg_time_diff

        # if calculated_framerate < int(self.fps) + 1:
        if abs(calculated_framerate - int(self.fps)) < 1:
            color = "r"
            # if self.FRAMERATEWARNINGSUPPRESSED is False:
            #     # if the framerate is too low raise a warining to the user?
            #     self.FRAMERATEWARNINGSUPPRESSED = show_warning_message(
            #         input_text="The required aquisition framerate is note being met. You could be dropping frames. ",
            #         okayButtonPresent=False,
            #         ignoreButtonPresent=True,
            #     )
        else:
            color = "g"
        # Display the implied framerate from the calcualtion
        self.frame_rate_text.setText(f"FPS: {calculated_framerate:.2f}", color=color)

    def display_recording_time(self):
        """
        Function to display the length of recording time.
        """
        if self.recording:
            elapsed_time = datetime.now() - datetime.strptime(
                self.metadata["begin_time"], "%Y-%m-%d %H:%M:%S"
            )
            elapsed_seconds = elapsed_time.total_seconds()
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.recording_time_text.setText(
                f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}", color="g"
            )
        else:
            self.recording_time_text.setText("", color="r")

    def update_camera_dropdown(self):
        """Update the camera options
        NOTE: this function is wrapped in functions to disconnect and reconnect the signal to the dropdown when the function changes the text in the dropdown
        the combobox is filled with the other camera label and the correct camera is not an option in the dropdown.
        """
        # disconnect self.camera_dropdown from the current function
        self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        cbox_update_options(
            cbox=self.camera_dropdown,
            options=self.camera_setup_tab.get_camera_labels(),
            used_cameras_labels=list(
                [cam.label for cam in self.view_finder.camera_groupboxes]
            ),
            selected=self.label,
        )
        self.camera_dropdown.currentTextChanged.connect(self.change_camera)

    def get_mp4_filename(self) -> str:
        """Get the filename for the mp4 file. This is done using GUI information"""
        self.subject_id = self.subject_id_text.toPlainText()

        self.recording_filename = os.path.join(
            self.view_finder.save_dir_textbox.toPlainText(),
            f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4",
        )

        self.logger.info(f"Saving recording to: {type(self.recording_filename)}")

    def get_gpio_filename(self, header=None) -> str:
        """
        This Python function creates a CSV file with a specified header containing GPIO data.

        :param header: The `header` parameter in the `get_gpio_filename` function is a list of strings
        that represent the column headers for the CSV file that will be created. In this case, the
        default header list is `['Line1', 'Line2', 'Line3', 'Line4']`, but
        :type header: list
        """
        # Get the subject ID from the text field
        self.subject_id = self.subject_id_text.toPlainText()
        self.GPIO_filename = os.path.join(
            self.view_finder.save_dir_textbox.toPlainText(),
            f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_GPIO_data.csv",
        )
        if header is None:
            header = ["Line1", "Line2", "Line3", "Line4"]
        with open(self.GPIO_filename, mode="w", newline="") as self.f:
            writer = csv.writer(self.f)
            writer.writerow(header)

    def get_metadata_filename(self) -> str:
        """Get the filename for the metadata file"""
        self.subject_id = self.subject_id_text.toPlainText()
        self.metadata_filename = os.path.join(
            self.view_finder.save_dir_textbox.toPlainText(),
            f"{self.subject_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_metadata.json",
        )

    def display_frame(self, image_data: np.array) -> None:
        """
        Display the image on the GUI
        This function also calls the the relevent functions to add overlays on the image.
        """
        try:
            # Display the image on the GUI
            self.video_feed.setImage(image_data.T)
            # Display the GPIO data on the image
            # self.get_GPIO_data()
            # self.draw_GPIO_overlay()
            # # # Recording status overlay
            self.draw_status_overlay()
        except Exception as e:
            print(f"Error displaying image: {e}")

    def draw_status_overlay(self):
        """
        Draw the status of the recording on the image. This simply changes the color of an attribute that is been placed
        onto the image during initialisation.
        """
        if self.recording is True:
            status = "RECORDING"
            color = "g"
        elif self.recording is False:
            status = "NOT RECORDING"
            color = "r"
        self.recording_status_item.setText(status, color=color)

    def update_gpio_overlay(self, DECAY=0.9) -> None:
        """Draw the GPIO data on the image"""

        if self._GPIO_data is None:
            self.gpio_over_lay_color = DECAY * np.array(self.gpio_over_lay_color)
        elif self._GPIO_data is not None:
            # If all of the channels are 1 normal exponential decay, if any are 0 then bump the color back to the highest point again
            if all(state == 0 for state in self._GPIO_data):
                self.gpio_over_lay_color = DECAY * np.array(self.gpio_over_lay_color)
            else:
                new_color = self.gpio_over_lay_color.copy()
                for line_index, gpio_state in enumerate(self._GPIO_data):
                    if line_index == 3:
                        # skip the last line
                        continue
                    if gpio_state == 0:
                        new_color[line_index] = 0
                    elif gpio_state == 1:
                        new_color[line_index] = 255
                self.gpio_over_lay_color = (DECAY) * np.array(new_color) + (
                    1 - DECAY
                ) * np.array(self.gpio_over_lay_color)

        # update the color of the ellipse
        self.gpio_status_indicator.setText("\u2b24", color=self.gpio_over_lay_color)

    def refresh(self):
        """refresh the camera widget"""
        self.update_camera_dropdown()

    def _init_ffmpeg_process(self) -> None:
        """
        This function initalising the ffmpeg process.
        This uses the ffmpeg-python API. This api does little more than make the syntax for ffmpeg nicer.
        The FFMPEG process is a separate process (according to task-manager) that is running in the background.
        It runs on the GPU (if you let the encoder be a GPU encoder) and is not blocking the main thread.
        TODO: There needs to be proper error handling for the ffmpeg process. At the moment, if the process fails, the user will not know.
        """
        downsampled_width = int(self.cam_width / self.downsampling_factor)
        downsampled_height = int(self.cam_height / self.downsampling_factor)

        if getattr(sys, "frozen", False):
            ffmpeg_path = gui_config_dict["PATH_TO_FFMPEG"]
        else:
            ffmpeg_path = gui_config_dict["PATH_TO_FFMPEG"]

        ffmpeg_command = [
            ffmpeg_path,
            "-y",  # overwrite output file if it exists
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-s",
            f"{downsampled_width}x{downsampled_height}",
            "-r",
            self.fps,  # Set framerate to camera resolution
            "-i",
            "pipe:",  # input comes from a pipe
            "-vcodec",
            ffmpeg_config_dict["output"]["encoder"][self.view_finder.encoder],
            "-pix_fmt",
            ffmpeg_config_dict["output"]["pxl_fmt"][self.pxl_fmt],
            "-preset",
            "fast",
            "-crf",
            "23",
            self.recording_filename,  # Output filename
        ]

        print(ffmpeg_command)
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

    def encode_frame_ffmpeg_process(self, frame: np.array) -> None:
        """
        The `encode_frame_ffmpeg_process` function encodes the frame using the ffmpeg pgrocess.

        :param frame: np.array - frame to be encoded
        """
        try:
            # Write the frame to the ffmpeg process
            self.ffmpeg_process.stdin.write(frame.tobytes())

        except Exception as e:
            print(f"Error encoding frame: {e}")

    def encode_frame_from_camera_buffer(self, frame_buffer: list[np.ndarray]) -> None:
        """
        Encodes the frames from the camera buffer and writes them to the file.
        """
        try:
            while frame_buffer:
                # Get the frame from the buffer (front of the queue)
                frame = frame_buffer.pop(0)
                # Encode the frame
                self.encode_frame_ffmpeg_process(frame)

        except Exception as e:
            print(f"Error encoding frame: {e}")

    def write_gpio_data_to_csv(self, gpio_data: list[bool]) -> None:
        """
        The function `encode_gpio_data` writes GPIO data to a file in CSV format.
        :param gpio_data: The `gpio_data` parameter is a list of boolean values representing the GPIO
        data that needs to be encoded and written to a file. The `encode_gpio_data` method takes this
        list of boolean values and writes them to a file specified by `self.GPIO_filename`. If an error
        occurs during the encoding
        :type gpio_data: list[bool]
        """
        try:
            # Converts the list of bools to a list of ints, because writing ints takes a smaller number of charaters than
            # writing the string 'True' or 'False'.
            gpio_data = [int(x) for x in gpio_data]
            # Write the GPIO data to the file
            with open(self.GPIO_filename, mode="a", newline="") as self.f:
                writer = csv.writer(self.f)
                writer.writerow(gpio_data)

        except Exception as e:
            print(f"Error encoding GPIO data: {e}")

    def write_gpio_data_from_buffer(self, gpio_buffer: list[list[bool]]) -> None:
        """
        This function is used to write the GPIO data to a file from the buffer.
        The buffer will return a list of list of booleans.
        The length of the outer list is the number of frames that were emptied from the buffer.
        This function is a wrapper for the `encode_gpio_data` function.
        Parameters:
        - buffer_list: list[list[bool]] - list of GPIO data to be written to the file

        """
        try:
            for gpio_data in gpio_buffer:
                self.write_gpio_data_to_csv(gpio_data)
        except Exception as e:
            print(f"Error encoding GPIO data: {e}")

    def create_metadata_file(self):
        """Function to creat the metadata file and write its initial information to json"""
        # create metadata file
        self.get_metadata_filename()

        self.metadata = {
            "subject_ID": self.subject_id,
            "camera_unique_id": self.unique_id,
            "recording_filename": self.recording_filename,
            "GPIO_filename": self.GPIO_filename,
            "recorded_frames": self.recorded_frames,
            "begin_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recorded_frames": None,
            "end_time": None,
        }

        with open(self.metadata_filename, "w") as self.meta_data_file:
            json.dump(self.metadata, self.meta_data_file, indent=4)

    def close_metadata_file(self):
        """Function to close the metadata file"""
        self.metadata["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.metadata["recorded_frames"] = self.recorded_frames
        with open(self.metadata_filename, "w") as self.meta_data_file:
            # add the end time to the metadata file
            json.dump(self.metadata, self.meta_data_file, indent=4)

    def update_subject_id(self):
        """Update the subject ID"""
        self.subject_id = self.subject_id_text.toPlainText()
        self.logger.info(f"Subject ID changed to: {self.subject_id}")
        self.validate_subject_id_input()
        # call the refresh function from th viewfinder class
        self.view_finder.refresh()

    def validate_subject_id_input(self):
        """Change the colour of the subject ID text field"""
        if self.subject_id_text.toPlainText() == "":
            self.start_recording_button.setEnabled(False)
        else:
            self.start_recording_button.setEnabled(True)

    ### Recording Controls

    def start_recording(self) -> None:
        """
        Function to start the recording of the video.
        - Set the recording flag to True
        - Initalise the ffmpeg process
        - Create the metadata file
        - Update the GUI buttons to the correct state
        """
        # Get the filenames
        self.get_mp4_filename()
        self.get_gpio_filename()
        self.get_metadata_filename()
        # Initalise ffmpeg process
        self._init_ffmpeg_process()
        # Set the recording flag to True
        self.recording = True
        # Reset the number of recorded frames to zero
        self.recorded_frames = 0
        # Create the metadata file
        self.create_metadata_file()
        # update labels on GUI
        self.stop_recording_button.setEnabled(True)
        self.camera_dropdown.setEnabled(False)
        # self.downsampling_factor_label.setEnabled(False)
        self.start_recording_button.setEnabled(False)
        self.subject_id_text.setEnabled(False)
        # self.fps_label.setEnabled(False)
        # self.pxl_fmt_label.setEnabled(False)
        # self.downsampling_factor_text.setEnabled(False)
        # Tabs can't be changed whilst recording
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(False)

    def stop_recording(self) -> None:
        """
        Function to stop the recording of the video.
        - Set the recording flag to False
        - Closes the metadata file (by writing the relevent information to it and saving it)
        - Sets the GUI buttons to the correct state
        - De-inits the ffmpeg process
        """
        self.recording = False
        self.close_metadata_file()
        # Set other buttons to now be enabled
        self.stop_recording_button.setEnabled(False)
        self.start_recording_button.setEnabled(True)
        self.subject_id_text.setEnabled(True)
        self.camera_dropdown.setEnabled(True)
        # Tabs can be changed
        self.view_finder.GUI.tab_widget.tabBar().setEnabled(True)
        self.logger.info("Recording Stopped")
        self.ffmpeg_process.stdin.close()
        self.ffmpeg_process.wait()

    def change_camera(self) -> None:
        self.logger.info("Changing camera")
        # shut down old camera
        if self.camera_api is not None:
            self.camera_api.stop_capturing()
        # Get the new camera ID
        new_camera_label = str(self.camera_dropdown.currentText())
        # from the setups tab, get the unique id of the camera
        camera_unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(
            new_camera_label
        )
        self._change_camera(camera_unique_id, new_camera_label)

    def _change_camera(self, new_unique_id, new_camera_label) -> None:
        # Set the new camera name
        self.unique_id = new_unique_id
        self.label = new_camera_label
        # Get the new camera settings
        self.camera_settings = self.camera_setup_tab.getCameraSettingsConfig(self.label)
        # Set the new camera object
        self.camera_api = init_camera_api(new_unique_id, self.camera_settings)
        self.camera_api.begin_capturing()
        # Call the display function once
        # self.display_frame(self.camera_object.get_next_image())
        #  Update the list cameras that are currently being used.
        self.camera_setup_groupbox.setTitle(self.label)

    def change_downsampling_factor(self) -> None:
        """Change the downsampling factor of the camera"""
        self.logger.info("Changing downsampling factor")
        # Get the new downsampling factor
        downsampling_factor = int(self.downsampling_factor_text.currentText())
        # Set the new downsampling factor
        self.downsampling_factor = downsampling_factor

    ### Config related functions.

    def get_camera_config(self):
        """Get the camera configuration"""
        return CameraSetupConfig(
            label=self.label,
            # downsample_factor=self.downsampling_factor,
            subject_id=self.subject_id,
        )

    def set_camera_widget_config(self, camera_config: CameraSetupConfig):
        """Set the settings assocaitd with the camera widget into the GUI"""
        # Check if the camera label is in the database
        if camera_config.label not in self.camera_setup_tab.get_camera_labels():
            self.logger.error(
                f"Camera label {camera_config.label} not found in database"
            )
            return

        self.label = camera_config.label
        # self.downsampling_factor = camera_config.downsample_factor
        self.unique_id = self.camera_setup_tab.get_camera_unique_id_from_label(
            self.label
        )
        self.subject_id = camera_config.subject_id
        self._change_camera(new_unique_id=self.unique_id, new_camera_label=self.label)
        self.logger.info(f"Camera configuration set to: {camera_config}")

    ### Functions for changing the camera settings for a camera

    def rename(self, new_label):
        """Function to rename the camera"""
        # remove the current label from the camera_dropdown widget
        # self.camera_dropdown.currentTextChanged.disconnect(self.change_camera)
        self.camera_dropdown.removeItem(self.camera_dropdown.findText(self.label))
        self.label = new_label
        self.camera_dropdown.setCurrentText(new_label)
        self.camera_setup_groupbox.setTitle(new_label)

    def change_fps(self):
        """Change the FPS of the camera"""
        self.logger.info("Changing FPS")
        # Set the new FPS
        self.camera_settings.fps = str(self.fps_cbox.currentText())
        # This function requires reinitalisation of the camera with the new FPS
        self.camera_api.set_frame_rate(int(self.camera_settings.fps))

    def change_pxl_fmt(self):
        """Change the pixel format of the camera"""
        self.logger.info("Changing pixel format")
        # Set the new pixel format to the camera settings datastructure
        self.camera_settings.pxl_fmt = str(self.pxl_fmt_cbox.currentText())
        # This function requires reinitalisation of the camera with the new pixel format
        self.camera_api.set_pixel_format(self.camera_settings.pxl_fmt)

    ### Visibility Controls

    def toggle_control_visibility(self) -> None:
        """
        Toggle the visibility of the camera controls
        """
        # add a button to connect to this funciton.
        is_visible = self.camera_setup_groupbox.isVisible()
        self.camera_setup_groupbox.setVisible(not is_visible)

    ### Functions for disconnecting the camera from the GUI

    def disconnect(self):
        """
        Function for disconnecting the camera from the GUI.
        This function does the following:
        - Ends the recording from the camera object
        - Removes the camera from the grid layout
        - Deletes the camera widget when PyQt6 is ready to delete it
        It should be possible to also remove the camera from the groupboxes list from this function, however
        I have done this after this function is called, in the other places this function is called.
        """
        self.camera_api.stop_capturing()
        self.view_finder.camera_layout.removeWidget(self)
        # This post might suggest that the self.deleteLater() function is causing the application to crash.
        # https://stackoverflow.com/questions/37564728/pyqt-how-to-remove-a-layout-from-a-layout
        # self.deleteLater()
