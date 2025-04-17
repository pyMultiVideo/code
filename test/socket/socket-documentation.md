# Socket Documentation

If you would like to use the output of the video to do image processing real time, then pyMutliVideo allows this functionality.

## Reference

For each camera you can set a tcp address to a point on the computer images can be sent, which can then be recieved by another script. The [ZeroMQ](https://zeromq.org) library is used to implement this functionality.

The socket is configured in '[SUBSCRIBE](https://zguide.zeromq.org/docs/chapter5/#Pros-and-Cons-of-Pub-Sub)' mode. This ensure that the publishing process (pyMultiVideo) is not affected if the client process crashes, isolating the pyMutliVideo and ensuring it will not be blocked by interaction with client process.

The rate of images put into the socket and getting information from the socket is defined in the `config.py` in the `socket_config` dict by the `put_rate` and `pull_rate` processes respectively.

### Getting images from the socket

Once a Camera widget has been intialised, you will be able to see a Plug icon. If you click this you will be able to start publishing to the address configured in the camera setup tab (under the three dots).

Once you start publishing images to the tcp address, then a separate process will be able to start polling for the images places in this queue.

The following code snippet shows the required decoding of the message from the socket

```python
msg = sub_socket.recv()
msg = json.loads(msg.decode("utf-8"))
```

Once the message has been decoded it will look like the following:

```python
{
  "unique_id": str(self.settings.unique_id), # Camera Unique id (as defined by the pyMultiVideo)
  "timestamp": self.frame_timestamps[-1], # The timestamps of the image that has been sent
  "image": base64.b64encode(np.array(self.latest_image).tobytes()).decode("utf-8"), # The image data encoded in base64 so if can be sent through the socket
  "height": self.camera_height, # image height
  "width": self.camera_width, # image width
}
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
