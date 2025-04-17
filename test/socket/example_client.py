import zmq
import cv2
import numpy as np
import json
import base64

context = zmq.Context()

# SUB socket to receive images
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:5555")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Connection via 'SUBSCRIBE

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
        if img_array is not None:
            cv2.imshow("Client View", img_array)

    # Generate random coordinates for the box
    height, width = 100, 100
    top_left_x = np.random.randint(0, width // 2)
    top_left_y = np.random.randint(0, height // 2)
    bottom_right_x = np.random.randint(width // 2, width)
    bottom_right_y = np.random.randint(height // 2, height)
    print("Sending message")
    msg = {"DRAW_BOX": {"TOP_LEFT": [top_left_x, top_left_y], "BOTTOM_RIGHT": [bottom_right_x, bottom_right_y]}}
    push_socket.send_string(json.dumps(msg))
