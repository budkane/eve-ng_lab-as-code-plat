import os

from eve_ng import EveNGClient
from lab import load_lab


def main():
    client = EveNGClient(
        os.environ["EVE_NG_HOST"],
        os.environ["EVE_NG_USERNAME"],
        os.environ["EVE_NG_PASSWORD"],
    )

    lab = load_lab("labs/ospf-basic/lab.yml")

    client.login()

    lab_path = client.deploy_lab(lab)

    node_id = client.get_node_id(
    lab_path,
    "R1",
)

    with open("build/R1.cfg", "r") as file:
        config = file.read()

    client.set_node_config(
        lab_path,
        node_id,
        config,
    )

    print("Configuration applied to R1")
    print(client.get_node_config(lab_path, 1))


if __name__ == "__main__":
    main()