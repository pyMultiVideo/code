import os

# Get the path of the root folder dynamicallyd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dictionary = {
    "ROOT": ROOT,
    "camera_dir": os.path.join(ROOT, "config"),
    "encoder_dir": os.path.join(ROOT, "config"),
    "data_dir": os.path.join(ROOT, "data"),
    "config_dir": os.path.join(ROOT, "config"),
    "assets_dir": os.path.join(ROOT, "assets", "icons"),
}
