import yaml
from jinja2 import Environment, FileSystemLoader


DEVICE_FILE = "devices/R1.yml"
TEMPLATE_DIR = "templates/cisco-ios"
OUTPUT_FILE = "build/R1.cfg"


def main():
    # Read the device definition
    with open(DEVICE_FILE, "r") as file:
        device = yaml.safe_load(file)

    # Configure Jinja2
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    configuration = []

    # Render each requested component
    for component in device["components"]:
        template = environment.get_template(f"{component}.j2")
        rendered = template.render(**device)

        configuration.append(rendered)

    # Assemble the final configuration
    configuration.append("end")

    final_configuration = "\n\n".join(configuration)

    # Write the generated configuration
    with open(OUTPUT_FILE, "w") as file:
        file.write(final_configuration)

    print(f"Generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()