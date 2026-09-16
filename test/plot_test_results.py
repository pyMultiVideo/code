from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from matplotlib import cm
import numpy as np

ROOT = Path(__file__).resolve().parent.parent  # pyMV code folder.


def plot_performance_metrics(test_name="perf-test", x=None, y="percent_dropped_frames", hue=None):
    """Plot performance metrics from the results.tsv file in a test data directory.
    By default the first sweep parameter is used for the x-axis, the second sweep parameter
    is used for the hue, and the y-axis is percent_dropped_frames.
    """
    # Load test parameters
    test_params_path = ROOT / "data" / test_name / "test_parameters.json"
    with open(test_params_path, "r") as f:
        test_params = json.load(f)
    sweep_params = list(test_params["parameter_sweeps"].keys())
    if x is None:
        x = sweep_params[0]
    if hue is None:
        hue = sweep_params[1] if len(sweep_params) > 1 else None
    # Load data table.
    data_dir = ROOT / "data" / test_name
    results_df = data_dir / "results.tsv"
    df = pd.read_csv(results_df.resolve(), sep="\t")
    # Check frame count from openCV matches that from the metadata file.
    if not df["openCV_frame_count"].equals(df["recorded_frames"]):
        print("Warning: Frame count from openCV does not match that from the metadata file.")
    # Make plot
    plt.figure(1).clf()
    sns.lineplot(data=df, x=x, y=y, hue=hue)
    plt.show()


if __name__ == "__main__":
    plot_performance_metrics()
