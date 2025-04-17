import zmq


class Image_socket:
    """Wrapper around zmq socket for publishing the images acquired to a address"""

    def __init__(self, camera_widget, pub_address, pull_address):
        # Reference to parent widget
        self.camera_widget = camera_widget
        self.context = zmq.Context()
        # PUB socket to broadcast images
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(pub_address)
        # PULL socket to receive client data
        self.pull_address = self.context.socket(zmq.PULL)
        self.pull_address.bind(pull_address)

    def put(self, msg):
        # image should be wrapped in a dictionary, with the name of the camera it came from
        self.pub_socket.send(msg)

    def get(self):
        """Try to recieve data in the pull socket"""
        try:
            if self.pull_address.poll(timeout=1):
                msg = self.pull_address.recv_json()
                return msg
        except zmq.Again:
            return

    def close(self):
        """Close the sockets and terminate the zmq context safely."""
        self.pub_socket.close()
        self.pull_address.close()
        self.context.term()
