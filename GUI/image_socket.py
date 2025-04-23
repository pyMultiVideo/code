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

    def send(self, topic, msgpacked_metadata, image_bytes):
        """Send a message using the send_multipart

        Args:
            topic (bytes): The type of data being send to the socket
            metadata (bytes): Dictionary of the metadata being sent
            image (bytes): bytes array of the data being sent to the PUB socket
        """
        self.pub_socket.send_multipart([topic, msgpacked_metadata, image_bytes])

    def get(self, timeout):
        """Try to recieve data in the pull socket"""
        try:
            if self.pull_address.poll(timeout=timeout):
                msg = self.pull_address.recv_json()
                return msg
        except zmq.Again:
            return

    def close(self):
        """Close the sockets and terminate the zmq context safely."""
        self.pub_socket.close()
        self.pull_address.close()
        self.context.term()
