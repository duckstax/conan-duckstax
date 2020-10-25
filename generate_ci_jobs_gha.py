#!/usr/bin/env python3
import argparse
import json
import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', action='store', type=str, required=True)
    args = parser.parse_args()
    with open(args.config) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        print(json.dumps(data["matrix"]))


if __name__ == '__main__':
    main()
