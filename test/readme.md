# Running Test

To run an evaluation of the performance of pyMultiVideo, the scripts are located here.

## Why run a test

When using the application for scientific applications, you might want to verify that the application can run without dropping frames on the computer you are using it on.

You can run a performance test to see what the performance of the application will be for your computer as well as working out what parameters you can change to improve the performance of the application.

## How to run a test

You should run these scripts from the `/code` folder _not_ the `/code/test` folder, otherwise the data files are not recognsed.

1. Create the config file for each test that will be run.
   - Use the `config-files.py` module to create the directory structure in which the tests (over the parameters of the GUI / FFMPEG encoding / camera settings that you would like to use)
2. Run ther `performance_test.py` module. This will look through each directory in the _tests_ folder and use the _config.json_ file located within it to run a version of pyMultiVideo and record for a period of time.
3. Run `table.py`. This will generate a table summary of the performance test that was run
4. Run `results_figure.ipynb` to get a summary.png in the tests folder that will tell you how different parameters affect the performance of the pyMutliVideo application.

### Metadata validation

The metadata files are used to generate the figures for the manuscript. The `metadata_validation_script.py` can be used to ensure that the metadata files do reflect the behaviour of the video files.
