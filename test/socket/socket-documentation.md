# Socket Documentation

If you would like to use the output of the video to do image processing real time, then pyMutliVideo allows this functionality.

## Reference for how this works

For each camera you can set a tcp address to a point on the computer images can be sent, which can then be recieved by another script. The ZeroMQ library is used to implement this functionality.

The socket is configured in 'subscribe' mode. This ensure that the client process that is being used to do image processing can not block pyMultiVideo from dropping its frames during recording by being blocked by some process.

The rate of Putting images in the socket and getting information from the socket is defined in the `config.py` in the `socket_config` dict.

### Getting images from the socket

Once the message has been decoded it will look like the following:

```python
{
  "unique_id": str(self.settings.unique_id),
  "timestamp": self.frame_timestamps[-1],
  "image": base64.b64encode(np.array(self.latest_image).tobytes()).decode("utf-8"),
  "height": self.camera_height,
  "width": self.camera_width,
}
```

### Sending information back to pyMultiVideo

The only information that you can send pyMutliVideo that is will use is the information to draw a rectangle anywhere on the camera viewfinder.

The message must be formatted in the following way, otherwise, it can not be displaed.

```python
{"DRAW_BOX": {"TOP_LEFT": [int(x), int(y)], "BOTTOM_RIGHT": [int(x + w), int(y + h)]}}
```

If this information stops being sent to pyMutliVideo's pull socket, then the rectangles will stop being displayed and eventually deleted from the screen.

## I want to do real time image analysis

Example scenario: You would like to do basic image process on the images that you acquire from pymultivideo.

zmq is used as the library for handling this.

- A 'Server Object will be created' with address defined in the 'more settings' part of the camera settings tab.
- As defined by the config the rate at which images are put to the socket is defined.

- The type of connection that you must start is a 'SUBSCRIBE' connection. This allows very simple functionality:
  - You can set a connection do socket with the local host address that is defined in the settings.
  - If another script is listening to Local server, if can grab the latest image that is acquired from the camera widget.
  - You can do what ever processing you want to this image

- This function is on a timer, that is sent in the config file.

What does the error message look like?

## Examples

In this directory, there is an example of a minimal script demonstrating the ability to do face tracking and displaying the location of the face on the display output.
