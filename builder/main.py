import argparse
from build import build

if __name__ == "__main__":
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('zip', help='The path to the target ZIP file')
    args = parser.parse_args()

    print(build(args.zip))
