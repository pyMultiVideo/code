# Performance tests

This folder contains code to run an evaluation of the performance of pyMultiVideo.  The tests evaluate the fraction of dropped frames as a function of acqusition parameters such as the number of cameras, frame rate, etc.  This can be useful for characterising what acqusition parameters your computer will support without dropping frames, and identifying which parameters you can change to improve the performance of the application.

## How to run a test

The basic workflow for running a peformance test is:

1.  Specify a test configuration and make the required applicaiton config files using the `generate_test_configs` function in *make_test_config.py*.  A test configuration specifies which acqusition parameters will be systematically varied during the test, and the values of parameters which will be held constant.

2. Run the test using the `run_performance_test` function in the *performance_test.py* module.  This will automatically run a series of recordings using the GUI while systematically varying different acqusition paramters.

3. Generate a data table from the output of the recordings, using the `make_data_table` function in the *make_data_table.py* module. This will generate a `results.tsv` file containing the data used for plotting the test results.
4. Plot the test results using the `plot_test_results` function in the *plot_test_results.py* module.  This generates a plot showing how the fraction of dropped frames varies a function of the acqusition paramters varied during the test.

The *test_script.py* module implements and runs a set of different performance tests evaluating the effect of different acqusition parameters.

Note:  The performance test code should be run using the `pmv` python environment used for running pyMultivideo.  You will need to pip install the additional python modules specified in `requirements-test.txt` file into the environment in order for the performance test code to run.
