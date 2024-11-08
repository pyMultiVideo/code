import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", help="Path to the configuration file", type=str)
args = parser.parse_args()

print(args.config)