"""
Adapted from the interactive_and_realtime_inference.ipynb

Example of realtime inference taking place from the socket.
Notes:
    - This requires you to download the files (model) from that example.

"""

import sleap
import numpy as np
import zmq
import msgpack

sleap.disable_preallocation()  # This initializes the GPU and prevents TensorFlow from filling the entire GPU memory
sleap.versions()
sleap.system_summary()

context = zmq.Context()
# SUB socket to receive images
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:5555")
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Connection via SUBSCRIBE


# Load the example SLEAP model
predictor = sleap.load_model(
    [
        "/Users/student/PycharmProjects/code/test/SLEAP/centroid_model.zip",
        "/Users/student/PycharmProjects/code/test/SLEAP/centered_instance_id_model.zip",
    ],
    batch_size=16,
)


while True:
    if sub_socket.poll(timeout=0):  # Wait for 1 second
        topic, metadata_packed, image_bytes = sub_socket.recv_multipart()
        if topic.decode("utf-8") != "image":  # Filter by topic
            continue
        # Contains metadata about the image
        metadata = msgpack.unpackb(metadata_packed)
        print(metadata) 
        # Convert bytes to image array
        frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape(
            (metadata["height"], metadata["width"])
        )  # Reshape the image to the image dimensions

        frame_predictions = predictor.inference_model.predict_on_batch(np.expand_dims(frame, axis=0))
