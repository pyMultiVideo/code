"""
This example should how you could use a connection to a socket to retrieve the image data and do some image processing on the image.
This processing can then be used for your own use (sending it as an input to another scientific task)

Here, we show that it is possible to track the location of a face, and send a box that is the coordinates of the face and send it back to
pyMultiVideo for display on the GUI. out
"""

import zmq
import cv2
import numpy as np
import json
import base64

context = zmq.Context()

# SUB socket to receive images
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:5555")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Connection via SUBSCRIBE

# PUSH socket to send data
push_socket = context.socket(zmq.PUSH)
push_socket.connect("tcp://localhost:5556")

print("Client started...")


while True:
    if sub_socket.poll(timeout=1000):  # Wait for 1 second
        msg = sub_socket.recv()
        msg = json.loads(msg.decode("utf-8"))
        img_data = base64.b64decode(msg["image"])
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img_array = img_array.reshape((msg["height"], msg["width"]))  # Assuming 3 channels (RGB)
        # Detect face
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(img_array, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        # Add the most likely face coordinates to the message
        if len(faces) > 0:
            largest_face = max(
                faces, key=lambda rect: rect[2] * rect[3]
            )  # rect[2] * rect[3] is the area of the rectangle
            x, y, w, h = largest_face
            msg = {"DRAW_BOX": {"TOP_LEFT": [int(x), int(y)], "BOTTOM_RIGHT": [int(x + w), int(y + h)]}}
            push_socket.send_string(json.dumps(msg))
