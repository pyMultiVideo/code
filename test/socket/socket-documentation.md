# Socket Documentation

If you would like to use the output of the video to do image processing real time, then pyMutliVideo allows this functionality.

## Reference

For each camera you can set a tcp address to a point on the computer images can be sent, which can then be recieved by another script. The [ZeroMQ](https://zeromq.org) library is used to implement this functionality.

The socket is configured in '[SUBSCRIBE](https://zguide.zeromq.org/docs/chapter5/#Pros-and-Cons-of-Pub-Sub)' mode. This ensure that the publishing process (pyMultiVideo) is not affected if the client process crashes, isolating the pyMutliVideo and ensuring it will not be blocked by interaction with client process.

The rate of images put into the socket and getting information from the socket is defined in the `config.py` in the `socket_config` dict by the `put_rate` and `pull_rate` processes respectively.

### Getting images from the socket

Once a Camera widget has been intialised, you will be able to see a Plug icon. If you click this you will be able to start publishing to the address configured in the camera setup tab (under the three dots).

Once you start publishing images to the tcp address, then a separate process will be able to start polling for the images places in this queue.

To access the data being published to the zmq socket you should connect the socket

```python
import zmq # Import ZeroMQ library
context = zmq.Context() 
# SUB socket to receive images
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:5555") # Connect to the publishing socket
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Connection via SUBSCRIBE
```

The data that is being sent in a 'multipart' message, in the following three parts:

topic: bytes, metadata_packed: bytes, image_bytes: bytes

> Note: All the data that is sent through the socket must be encoded in bytes. 

`topic` a byte string of type of data being send (in this case it will be an image.)

`metadata_packed` a string of bytes encoding the image metadata as a msgpacked string. To make sending the image metadata as efficient possible. This is done using the `msgpack` library which can send `dict` files in a common efficient format. 

`image_bytes` a string of bytes that encodes the image data that is being sent from pyMultiVideo

The following code example will generate process the image from the SUBCRIBE socket.

```python
# Get the data from the zmq socket
topic, metadata_packed, image_bytes = sub_socket.recv_multipart()
# Filter by topic
if topic.decode("utf-8") != "image":  
    continue
# Contains metadata about the image
metadata = msgpack.unpackb(metadata_packed)
```

Once the message has been decoded it will look like the following:

```python
{
  "unique_id": str(self.settings.unique_id), # Camera Unique id (as defined by the pyMultiVideo)
  "timestamp": self.frame_timestamps[-1], # The timestamps of the image that has been sent
  "height": self.camera_height, # image height
  "width": self.camera_width, # image width
}
```

You can use the image `height` and `width` to reshape the `frame` into orginal dimensions of the image being sent.

```python
frame = np.frombuffer(image_bytes, dtype=np.uint8).reshape(
    (metadata["height"], metadata["width"])
)  # Reshape the image to the image dimensions
```

You can use this information for your image processing.

### Sending information back to pyMultiVideo

You might like to send some visual information indicating the location of a detected point back to pyMultiVideo

The message must be formatted in the following way, otherwise, it will not be displayed.

```python
{"DRAW_BOX": {"TOP_LEFT": [int(x), int(y)], "BOTTOM_RIGHT": [int(x + w), int(y + h)]}}
```

If this information stops being sent to pyMutliVideo's pull socket, then the rectangles will stop being displayed and eventually deleted from the screen.

## Examples

In this directory, there is an example of a minimal script demonstrating the ability to do face tracking and displaying the location of the face on the display output.
