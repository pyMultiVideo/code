"""
Adapted from the interactive_and_realtime_inference.ipynb

Example of realtime inference taking place from the socket.
Notes:
    - This requires you to download the files (model) from that example.
    - Gives an output of the inference time of the machine when it is running on your computer.

"""

import matplotlib.pyplot as plt
import sleap
import numpy as np
import zmq
import msgpack
import os
from time import perf_counter

# Get the directory this file is being run in
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


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
        os.path.join(CURRENT_DIR, "centroid_model.zip"),
        os.path.join(CURRENT_DIR, "centered_instance_id_model.zip"),
    ],
    batch_size=16,
)
# Load the example SLEAP model
# predictor = sleap.load_model(
#     [
#         os.path.join(CURRENT_DIR, "model", "C57B6_BigMaze_Neuropixel-1.240508_094436.centroid.n=665.zip"),
#         os.path.join(CURRENT_DIR, "model", "C57B6_BigMaze_Neuropixel-1.240508_105332.centered_instance.n=665.zip"),
#     ],
#     batch_size=16,
# )
inference_times = []
print("Start polling socket...")
try:
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
            # convert the frame to dim: 1 x metadata["height"] x metadata["width"] x 1
            frame = frame[np.newaxis, :, :, np.newaxis]

            # Measure time taken for prediction
            start_time = perf_counter()
            frame_predictions = predictor.inference_model.predict_on_batch(frame)
            end_time = perf_counter() - start_time

            inference_times.append(end_time * 1000)  # Convert to milliseconds
except KeyboardInterrupt:
    print("Keyboard interrupt received. Exiting...")
finally:
    # Print inference times
    if inference_times:
        first_inference_time, inference_times = inference_times[0], inference_times[1:]
        print(f"First inference time: {first_inference_time:.1f} ms")
        print(f"Inference times: {np.mean(inference_times):.1f} +- {np.std(inference_times):.1f} ms")
    else:
        print("No inference times recorded.")
    # Plot inference times and save them to the directory of this folder
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), dpi=120, facecolor="w")

    # Subplot 1: Inference latency over time
    ax1.plot(inference_times, ".")
    ax1.set_xlabel("Time (frames)")
    ax1.set_ylabel("Inference latency (ms)")
    ax1.grid(True)
    ax1.set_title("Inference Latency Over Time")

    # Subplot 2: Histogram of inference latencies
    ax2.hist(inference_times, bins=30)
    ax2.set_xlabel("Inference latency (ms)")
    ax2.set_ylabel("PDF")
    ax2.set_title("Histogram of Inference Latencies")

    plt.tight_layout()
    output_path = os.path.join(CURRENT_DIR, "inference_times_plot.png")
    plt.savefig(output_path)
    print(f"Figure saved to {output_path}")
