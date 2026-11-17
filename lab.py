import argparse
from pathlib import Path

import yaml

from render import render_device


def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def load_lab(lab_file):
    return load_yaml(lab_file)


def load_device(device_name):
    device_file = Path("devices") / f"{device_name}.yml"
    return load_yaml(device_file)

def parse_endpoint(endpoint):
    device, interface = endpoint.split(":", 1)

    return {
        "device": device,
        "interface": interface,
    }

def load_topology(lab):
    topology = []

    for link in lab["links"]:
        endpoint_a, endpoint_b = link["endpoints"]

        topology.append({
            "a": parse_endpoint(endpoint_a),
            "b": parse_endpoint(endpoint_b),
        })

    return topology

def main():
    parser = argparse.ArgumentParser(
        description="Build a lab from a lab definition."
    )

    parser.add_argument(
        "lab",
        help="Path to the lab YAML definition.",
    )

    args = parser.parse_args()

    lab = load_lab(args.lab)
    topology = load_topology(lab)

    print(f"Lab: {lab['name']}")

    print("\nBuilding devices:")

    for node in lab["nodes"]:
        device_name = node["device"]
        device_file = Path("devices") / f"{device_name}.yml"

        device = load_device(device_name)

        print(
            f"\n  {device['name']} "
            f"({device['platform']})"
        )

        render_device(device_file)

    print("\nTopology:")

    for link in topology:
        print(
            f"  {link['a']['device']}:{link['a']['interface']} "
            f"<-> "
            f"{link['b']['device']}:{link['b']['interface']}"
        )
if __name__ == "__main__":
    main()