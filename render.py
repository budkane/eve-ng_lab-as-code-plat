
import argparse
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


def render_device(device_file):
    device_path = Path(device_file)

    # Read the device definition
    with device_path.open("r") as file:
        device = yaml.safe_load(file)

    # Validate required fields
    required_fields = ["name", "platform", "components"]

    for field in required_fields:
        if field not in device:
            raise ValueError(
                f"Device definition '{device_file}' is missing "
                f"required field: '{field}'"
            )

    # Select templates based on platform
    template_dir = Path("templates") / device["platform"]

    environment = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    configuration = []

    # Render each requested component
    for component in device["components"]:
        template_path = f"{component}/main.j2"

        try:
            template = environment.get_template(template_path)
        except TemplateNotFound:
            raise RuntimeError(
                f"Component '{component}' does not exist "
                f"for platform '{device['platform']}'"
            )

        rendered = template.render(**device)
        configuration.append(rendered)

    # Add final configuration command
    configuration.append("end")

    # Assemble configuration
    final_configuration = "\n\n".join(configuration)

    # Determine output filename from device name
    output_dir = Path("build")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{device['name']}.cfg"

    # Write generated configuration
    with output_file.open("w") as file:
        file.write(final_configuration)

    print(f"Generated {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate device configurations from YAML."
    )

    parser.add_argument(
        "device",
        nargs="?",
        help="Path to the device YAML definition.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate configurations for all device definitions.",
    )

    args = parser.parse_args()

    if args.all:
        device_files = sorted(Path("devices").glob("*.yml"))

        if not device_files:
            raise RuntimeError("No device definitions found in devices/")

        for device_file in device_files:
            render_device(device_file)

    elif args.device:
        render_device(args.device)

    else:
        parser.error("provide a device file or use --all")

if __name__ == "__main__":
    main()
