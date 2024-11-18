# Todo

> BAR IS LOW FOR IT TO BE HELPFUL. BASIC FUNCTIONALITY IS MOST IMPORTANT

## IPython Tab (for debugging the state of the variables when using the app)

- [ ] embed ipython in the ipython tab
- [ ] Create a function for creating / recreating the camera information
- [ ] Will there be a function that saves out and replaces csv with another csv with the updated information on closing?

## ViewFinder

- Make windows resizeable
  - Resize event is working for one camera window (not including the qlabel)
  - When i add another camera, the size of that window is too big?

  - [ ] The names of the cameras will always have the same mapping to serial numbers for all users.
  - [x] unique id could just be 'serialnumber-api'
  
- Add a screen that says 'No camera selected' to the interface.
- Cameras that are not avialable should not be in the list of cameras that can be selected for each camera widget.
  - BUG: this does not work perfectly: the new widget does work (has the correct types of cameras availablet use.)
  - The old widget does not!
- The list of cameras being added to the list is always the list entry of the list. This can be fixed by refreshing the list of avialable cameras before getting a camear to add to screen.
- add visual indication of if the gpio pins are showing properly
  - this has been implemented. Untestd if it decays propley if the channels are not showing.

- remove the config file from the camerawidget object. create a @save config functino

- [x] added a metadata file which saved start an stop time to a a json file.
- down sampling the image by some scale to be the reduced resolution.


# Latest
The camera widget is initialsing with no label in the dropdown. So maybe its not been assigned by the time i am trying to set it. Try changin the constructer of the camera widget