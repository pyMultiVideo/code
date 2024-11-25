# Todo

> BAR IS LOW FOR IT TO BE HELPFUL. BASIC FUNCTIONALITY IS MOST IMPORTANT

## Important bugs

USB camera take a long time to initalise compared to the FLIR spinnaker cameras

- This seems to be the case for the simplest of python scripts. So i don't think that htis is because of me...
  
Camera now in aqusition mode when you remove and add new cameras.

## encoding from the buffer

Instead of encoding video one frame at a time, the video buffer should be emptied and encoded for all frames in the buffer to make sure that no frames are lost during encoding

- how do i make sure that the buffer is encodering the frames and setting the gpio data with the same allignement?

## Feature requests

- Add being able to start the application from a config file
  - Pass the config file to the main gui (as a dictionary of parsed arguments)
  - On intialistaion of the view finder application, it checks if there have been any config files parsed. if so load them instead of doing the default behaviour.

### Automated testing of code

- Including testing how much of the computer resources are alllocated to streaming video before the software stops working optimally

### Grid layout

- Change the grid layout to be veritcal layout
  - upon changing the checkbox:
    - remove all the initalised layouts. Change them to another layout object and use that instead.
    - Should be parameter in the config.  that can be saved.
    - derf function to that is more flexiable that is called from the add to camera layout function

### Multithreading

- Multithreading wiodgets? [Multithreading widgets](https://www.pythonguis.com/tutorials/multithreading-pyqt6-applications-qthreadpool/)
- FMMPEG already uses its own subprocess to the video encoding.
- Displaying the video on separate threads would be the goal of this software.

### Passing Camera config file to the camera widget that are used to do the startup

- Define new datastructure that can optionally be sent to the camera initalisation function.
- This will use that file to set the camera attributes instead of the default ones.
This changes aqusision settings.
