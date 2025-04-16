import zmq
from collections import deque
import json
import cv2

from config.config import server_config


class Image_server:
    """
    non-blocking, passive-pull model

    Ring buffer for storing images

    """

    def __init__(self, camera_widget, pub_socket="tcp://*:5556", pull_socket="tcp://*:5557"):
        """
        Initialize the socket with a given capacity.

        :param capacity: Maximum number of images the buffer can hold
        """
        self.camera_widget = camera_widget

        self.context = zmq.Context()

        # PUB socket to broadcast images
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(pub_socket)

        # PULL socket to receive client data
        self.pull_socket = self.context.socket(zmq.PULL)
        self.pull_socket.bind(pull_socket)

        self.buffer = deque(maxlen=server_config["server_buffer_size"])

    def put(self, image):
        # Put images in the ring buffer
        # image should be wrapped in a dictionary, with the name of the camera it came from
        msg = {self.camera_widget.settings.unique_id: image.to_bytes()}
        # Send the json of the msg
        self.pub_socket.send(json.dumps(msg).encode("utf-8"))

    def get(self):
        """Get any data stored in the pull socket"""
        try:
            if self.pull_socket.poll(timeout=1):
                msg = self.pull_socket.recv_json()

                # Check if the message conforms to some standard (is a json dicitonary made of bytes)

                return msg
        except zmq.Again:
            pass

    def close(self):
        """Close the server sockets and terminate the context safely."""
        self.pub_socket.close()
        self.pull_socket.close()
        self.context.term()
