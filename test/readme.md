# Running Test

Scripts to run an evaluation of the performance of pyMultiVideo are located in the test foler.

## Why run a test

When using the application for scientific applications, you might want to verify that the application can run without dropping frames on the computer you are using it on.

You can run a performance test to see what the performance of the application will be for your computer as well as working out what parameters you can change to improve the performance of the application.

## How to run a test

1. Create the config file for each test that will be run.
   - Use `make_test_config.py` to create the directory structure and config files for the performance test.
   - Camera count defaults to one camera. Include `n_cameras` in `parameter_sweeps` only when camera count should vary:

    ```python
    test_parameters = {
       "test_name": "perf-test",
       "recording_duration": 10,
       "parameter_sweeps": {
          "fps": [30, 60, 90, 120, 150],
          "n_cameras": [1, 2],
       },
    }
    ```

    Values omitted from `parameter_sweeps` inherit defaults from `config/config.py`.
   For a camera-count sweep, use
   `"parameter_sweeps": {"n_cameras": [1, 2], ...}`. A scalar sweep value is also
   accepted and creates one configuration. The generator creates one configuration
   for every combination of supplied sweep values.
2. Run the `performance_test.py` module. This will look through each directory in the _tests_ folder and use the _config.json_ file located within it to run a version of pyMultiVideo and record for a period of time.
3. Run `make_data_table.py`. This will generate a `results.tsv` table summary of the performance test that was run.
4. Run `plot_test_results.py` to plot how the sweep parameters affect the performance of the pyMultiVideo application.
