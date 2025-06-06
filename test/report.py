# %% Import data
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

sns.set_style("ticks")

# Test name
test_name = "test-small"
data_folder = Path(".") / "data"
results_df = data_folder / test_name / "results.tsv"
df = pd.read_csv(results_df.resolve(), sep="\t")
# Convert 'duration' and 'real_duration' to datetime format
df["duration"] = pd.to_timedelta(df["duration"])
df["real_duration"] = pd.to_timedelta(df["real_duration"])

# %% Fix since dropped frames not working correctly
# Calculate percentage of dropped frames (Fix because pMV is not doing this correctly)
df["dropped_frames"] = (df["FPS"] * df["duration"].dt.total_seconds()) - df["recorded_frames"]
df["percent_dropped_frames"] = (df["dropped_frames"] / (df["FPS"] * df["duration"].dt.total_seconds())) * 100


N_CAMERAS = 2  # The number of cameras (for GUI config and FFMPEG Config)
# %% Create a figure
# Figure Title
fig, axes = plt.subplots(3, 3, figsize=(15, 15))
testing_parameters = data_folder / test_name / "testing_parameters.json"
with open(testing_parameters.resolve(), "r") as f:
    testing_params = json.load(f)
for i, (key, value) in enumerate(testing_params.items()):
    fig.text(0.1, 1.05 - i * 0.012, f"{key}: {value}", ha="left", va="center", fontsize=12)
fig.text(0.1, 0.92, "Camera Config", ha="left", va="center", fontsize=20, rotation="horizontal")
fig.text(0.1, 0.63, f"GUI Config (for {N_CAMERAS} cameras)", ha="left", va="center", fontsize=20, rotation="horizontal")
fig.text(
    0.1, 0.34, f"FFMPEG Config (for {N_CAMERAS} cameras)", ha="left", va="center", fontsize=20, rotation="horizontal"
)

# Adjust spacing between rows
fig.subplots_adjust(hspace=0.5, wspace=0.5)
# Camera Config Settings
axes[0, 0].set_title("Number of Cameras")
lineplot_n_cameras = sns.lineplot(
    ax=axes[0, 0],
    data=df,
    x="experiment_config_n_cameras",
    y="percent_dropped_frames",
    hue="experiment_config_n_cameras",
    marker="o",
    legend=True,
)
if lineplot_n_cameras.legend_ is not None:
    lineplot_n_cameras.legend_.set_title("Number of Cameras")
axes[0, 0].xaxis.set_major_locator(plt.MaxNLocator(integer=True))
axes[0, 0].set_xlabel("Number of Cameras")
axes[0, 0].set_ylabel("Dropped Frames (%)")

axes[0, 1].set_title("Downsampling")
lineplot_downsampling = sns.lineplot(
    ax=axes[0, 1],
    data=df,
    x="downsampling_factor",
    y="percent_dropped_frames",
    hue="experiment_config_n_cameras",
    marker="o",
    legend=False,
)
if lineplot_downsampling.legend_ is not None:
    lineplot_downsampling.legend_.set_title("Number of Cameras")
axes[0, 1].set_xlabel("Downsample Factor")
axes[0, 1].set_ylabel("Dropped Frames (%)")
axes[0, 2].set_title("Frames per second vs Dropped Frames (%)")
lineplot_fps = sns.lineplot(
    ax=axes[0, 2],
    data=df,
    x="FPS",
    y="percent_dropped_frames",
    hue="experiment_config_n_cameras",
    marker="o",
    legend=False,
)
if lineplot_fps.legend_ is not None:
    lineplot_fps.legend_.set_title("Number of Cameras")
axes[0, 2].set_xlabel("Frames per second")
axes[0, 2].set_ylabel("Dropped Frames (%)")

# GUI Settings

axes[1, 0].set_title("Camera Update Rate vs Dropped Frames (%)")
lineplot_update_rate = sns.lineplot(
    ax=axes[1, 0],
    data=df[df["experiment_config_n_cameras"] == N_CAMERAS],
    x="FPS",
    y="percent_dropped_frames",
    hue="application_config_gui_config_camera_update_rate",
    marker="o",
    legend=True,
)
if lineplot_update_rate.legend_ is not None:
    lineplot_update_rate.legend_.set_title("Camera Update Rate")
axes[1, 0].set_xlabel("Frames per second")
axes[1, 0].set_ylabel("Dropped Frames (%)")

axes[1, 1].set_title("Camera Updates per Display Update vs Dropped Frames (%)")
lineplot_updates_per_display = sns.lineplot(
    ax=axes[1, 1],
    data=df[df["experiment_config_n_cameras"] == N_CAMERAS],
    x="FPS",
    y="percent_dropped_frames",
    hue="application_config_gui_config_camera_updates_per_display_update",
    marker="o",
    legend=True,
)
if lineplot_updates_per_display.legend_ is not None:
    lineplot_updates_per_display.legend_.set_title("Updates per Display update")
axes[1, 1].set_xlabel("Frames per second")
axes[1, 1].set_ylabel("Dropped Frames (%)")
sns.lineplot(
    ax=axes[1, 1],
    data=df[df["experiment_config_n_cameras"] == N_CAMERAS],
    x="FPS",
    y="percent_dropped_frames",
    hue="application_config_gui_config_camera_updates_per_display_update",
    marker="o",
    legend=True,
)
axes[1, 1].set_xlabel("Frames per second")
axes[1, 1].set_ylabel("Dropped Frames (%)")

axes[1, 2].axis("off")

# FFMPEG settings plots

axes[2, 0].set_title("CRF")
lineplot_crf = sns.lineplot(
    ax=axes[2, 0],
    data=df[df["experiment_config_n_cameras"] == N_CAMERAS],
    x="FPS",
    y="percent_dropped_frames",
    hue="application_config_ffmpeg_config_crf",
    marker="o",
    legend=True,
)
if lineplot_crf.legend_ is not None:
    lineplot_crf.legend_.set_title("CRF")
axes[2, 0].set_xlabel("Frames per second")
axes[2, 0].set_ylabel("Dropped Frames (%)")

axes[2, 1].set_title("Encoding Speed by Number of Cameras")
lineplot_encoding_speed = sns.lineplot(
    ax=axes[2, 1],
    data=df[df["experiment_config_n_cameras"] == N_CAMERAS],
    x="FPS",
    y="percent_dropped_frames",
    hue="application_config_ffmpeg_config_encoding_speed",
    legend=True,
)
if lineplot_encoding_speed.legend_ is not None:
    lineplot_encoding_speed.legend_.set_title("Encoding speed")
axes[2, 1].set_xlabel("Frames per second")
axes[2, 1].set_ylabel("Dropped Frames (%)")

axes[2, 2].set_title("Compression Standard by Number of Cameras")
lineplot_compression = sns.lineplot(
    ax=axes[2, 2],
    data=df[df["experiment_config_n_cameras"] == N_CAMERAS],
    x="FPS",
    y="percent_dropped_frames",
    hue="application_config_ffmpeg_config_compression_standard",
    legend=True,
)
if lineplot_compression.legend_ is not None:
    lineplot_compression.legend_.set_title("Compression standard")
axes[2, 2].set_xlabel("Frames per second")
axes[2, 2].set_ylabel("Dropped Frames (%)")


# Save plot
plt.savefig(data_folder / test_name / "results_summary.png", dpi=450, bbox_inches="tight")

# %%
