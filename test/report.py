

# %% Import data
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

sns.set_style("ticks")

# Test name
test_name = "test-with-fps"
data_folder = Path("..") / "data"

results_df = data_folder / test_name / "results.tsv"
testing_parameters = data_folder / test_name / "testing_parameters.json"
with open(testing_parameters.resolve(), "r") as f:
    testing_params = json.load(f)
df = pd.read_csv(results_df.resolve(), sep="\t")
# Convert 'duration' and 'real_duration' to datetime format
df["duration"] = pd.to_timedelta(df["duration"])
df["real_duration"] = pd.to_timedelta(df["real_duration"])

# %% Create a figure
# Figure Title
fig, axes = plt.subplots(3, 3, figsize=(15, 15))
# fig.suptitle(f"Test Name: {testing_params['test_name']}", fontsize=16, ha='left')
for i, (key, value) in enumerate(testing_params.items()):
    fig.text(0.1, 1.05 - i * 0.012, f"{key}: {value}", ha="left", va="center", fontsize=12)
fig.text(0.1, 0.92, "Camera Config", ha="left", va="center", fontsize=20, rotation="horizontal")
fig.text(0.1, 0.63, "GUI Config", ha="left", va="center", fontsize=20, rotation="horizontal")
fig.text(0.1, 0.34, "FFMPEG Config", ha="left", va="center", fontsize=20, rotation="horizontal")

# Adjust spacing between rows
fig.subplots_adjust(hspace=0.5, wspace=0.5)

# Camera Config Settings
# Add titles to the first row of subplots
axes[0, 0].set_title("Number of Cameras")
sns.lineplot(ax=axes[0, 0], data=df, x="n_cameras", y="percent_dropped_frames", marker="o")
axes[0, 0].xaxis.set_major_locator(plt.MaxNLocator(integer=True))  # Ensure x ticks are integers
axes[0, 0].set_xlabel("Number of Cameras")
axes[0, 0].set_ylabel("Dropped Frames (%)")

axes[0, 1].set_title("Downsampling")
sns.lineplot(ax=axes[0, 1], data=df, x="downsampling_factor", y="percent_dropped_frames", marker="o")
axes[0, 1].set_xlabel("Downsample Factor")
axes[0, 1].set_ylabel("Dropped Frames (%)")
# Plot how frames per second affect performance
# sns.lineplot(ax=axes[0, 2], data=df, x="fps", y="performance", marker="o")
axes[0, 2].set_title("Frames per Second vs Dropped Frames (%)")
sns.lineplot(ax=axes[0, 2], data=df, x="fps", y="percent_dropped_frames", marker="o")
axes[0, 2].set_xlabel("Frames per Second")
axes[0, 2].set_ylabel("Dropped Frames (%)")

# GUI Settings
axes[1, 0].set_title("Camera Updates")
sns.lineplot(ax=axes[1, 0], data=df, x="camera_update_rate", y="percent_dropped_frames", marker="o")
axes[1, 0].set_xlabel("Camera Update Rate")
axes[1, 0].set_ylabel("Dropped Frames (%)")
axes[1, 1].set_title("Camera Updates Per Display Update vs Dropped Frames (%)")
sns.lineplot(ax=axes[1, 1], data=df, x="camera_updates_per_display_update", y="percent_dropped_frames", marker="o")
axes[1, 1].set_xlabel("Camera Updates Per Display Update")
axes[1, 2].axis("off")

# FFMPEG settings plots
axes[2, 0].set_title("CRF")
sns.lineplot(ax=axes[2, 0], data=df, x="crf", y="percent_dropped_frames", marker="o")
axes[2, 0].set_xlabel("CRF")
axes[2, 0].set_ylabel("Dropped Frames (%)")
axes[2, 1].set_title("Encoding Speed")
sns.boxplot(ax=axes[2, 1], data=df, x="encoding_speed", y="percent_dropped_frames")
axes[2, 1].set_xlabel("Encoding Speed")
axes[2, 1].set_ylabel("Dropped Frames (%)")

axes[2, 2].set_title("Compression Standard")
sns.boxplot(ax=axes[2, 2], data=df, x="compression_standard", y="percent_dropped_frames")
axes[2, 2].set_xlabel("Compression Standard")
axes[2, 2].set_ylabel("Dropped Frames (%)")
# Show plot
plt.savefig(data_folder / test_name / "results_summary.png", dpi=450, bbox_inches="tight")

# %%
