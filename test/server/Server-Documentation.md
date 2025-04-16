# Server Documentation

## I want to do real time image analysis!

Example scenario: You would like to do basic image process on the images that you acquire from pymultivideo.

zmq is used as the library for handling this. 

## When you click the `Start server` button

- A 'Server Object will be created' with address defined in the 'more settings' part of the camera settings tab. 
- As defined by the config the rate at which images are put to the socket is defined.

- The type of connection that you must start is a 'SUBSCRIBE' connection. This allows very simple functionality: 
  - You can set a connection do socket with the local host address that is defined in the settings.
  - If another script is listening to Local server, if can grab the latest image that is acquired from the camera widget.
  - You can do what ever processing you want to this image 

- You pyMultiVideo can recieve one type of input back: 
```python
{
    'BOX': X_COORDINATE, Y_COORDNATE
}
```

Every x Hz, pyMultiVideo will check the push queue, looking for any of these json formatted strings and use them to plot the box. 

If the message does not conform to the standard, then it will not be able display it.
What does the error message look like?
