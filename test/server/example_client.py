import zmq
import cv2
import numpy as np
import json

context = zmq.Context()

# SUB socket to receive images
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:5556")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Connection via 'SUBSCRIBE

# PUSH socket to send data
push_socket = context.socket(zmq.PUSH)
push_socket.connect("tcp://localhost:5557")

print("Client started...")

while True:
    if sub_socket.poll(timeout=100):
        msg = sub_socket.recv()
        msg = json.loads(msg.decode("utf-8"))
        img_bytes = list(msg.values())[0]
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if frame is not None:
            cv2.imshow("Client View", frame)

        # Example: Send mock coordinates when 's' key is pressed
        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        elif key == ord("s"):
            h, w = frame.shape[:2]
            msg = {"DRAW_BOX": {"TOP_LEFT": [4, 4], "BOTTOM_RIGHT": [10, 10]}}
            push_socket.send_json(msg)
