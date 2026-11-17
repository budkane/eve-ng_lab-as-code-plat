import os
import requests
from pathlib import Path

class EveNGClient:
    def __init__(self, host, username, password):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False

    def login(self):
        url = f"{self.host}/api/auth/login"

        response = self.session.post(
            url,
            json={
                "username": self.username,
                "password": self.password,
            },
        )

        response.raise_for_status()

        return response.json()
    def connect_interface(
        self,
        lab_path,
        node_id,
        interface_id,
        network_id,
    ):
        return self.put_path(
            f"labs/{lab_path}/nodes/{node_id}/interfaces",
            {
                str(interface_id): str(network_id),
            },
        )
    def connect_nodes(
        self,
        lab_path,
        node_a,
        interface_a,
        node_b,
        interface_b,
    ):
        # 1. Create visible bridge/network
        network = self.create_network(
            lab_path,
            {
                "type": "bridge",
                "name": f"Net-node{node_a}iface_{interface_a}",
                "left": "500",
                "top": "300",
                "visibility": 1,
                "icon": "lan.png",
            },
        )

        network_id = network["data"]["id"]

        # 2. Attach first interface
        self.connect_interface(
            lab_path,
            node_id=node_a,
            interface_id=interface_a,
            network_id=network_id,
        )

        # 3. Attach second interface
        self.connect_interface(
            lab_path,
            node_id=node_b,
            interface_id=interface_b,
            network_id=network_id,
        )

        # 4. Hide the internal network
        self.edit_network(
            lab_path,
            network_id,
            visibility=0,
        )

        return network_id

    def create_lab(self, path, name, version="1", author="", description="", body=""):
        return self.post_path(
            "labs",
            {
                "path": path,
                "name": name,
                "version": version,
                "author": author,
                "description": description,
                "body": body,
            },
        )
    def create_network(self, lab_path, network):
        return self.post_path(
            f"labs/{lab_path}/networks",
            network,
        )

    def create_node(self, lab_path, node):
        return self.post_path(
            f"labs/{lab_path}/nodes",
            node,
        )
  
    def deploy_link(self, lab_path, link):
        endpoint_a = self.resolve_endpoint(
            lab_path,
            f"{link['a']['device']}:{link['a']['interface']}",
        )

        endpoint_b = self.resolve_endpoint(
            lab_path,
            f"{link['b']['device']}:{link['b']['interface']}",
        )

        return self.connect_nodes(
            lab_path,
            node_a=endpoint_a["node_id"],
            interface_a=endpoint_a["interface_id"],
            node_b=endpoint_b["node_id"],
            interface_b=endpoint_b["interface_id"],
    )
    
    def deploy_lab(self, lab):
        lab_name = lab["name"]
        lab_path = f"/Test/{lab_name}.unl"

        # Create the EVE-NG lab
        self.create_lab(
            path="/Test",
            name=lab_name,
            version="1",
            author="Config Builder",
            description=f"Deployed by config-builder: {lab_name}",
        )

        # Create nodes
        for index, node in enumerate(lab["nodes"], start=1):
            eve_node = {
                "type": "qemu",
                "template": "vios",
                "config": "Unconfigured",
                "delay": 0,
                "icon": "Router.png",
                "image": node["image"],
                "name": node["name"],
                "left": f"{100 + (index * 300)}",
                "top": "200",
                "ram": 1024,
                "console": "telnet",
                "cpu": 1,
                "ethernet": 4,
            }

            self.create_node(
                lab_path,
                eve_node,
            )

        # Deploy topology
        topology = []
        for link in lab["links"]:
            endpoint_a, endpoint_b = link["endpoints"]

            topology.append({
                "a": {
                    "device": endpoint_a.split(":", 1)[0],
                    "interface": endpoint_a.split(":", 1)[1],
                },
                "b": {
                    "device": endpoint_b.split(":", 1)[0],
                    "interface": endpoint_b.split(":", 1)[1],
                },
            })

        self.deploy_topology(
            lab_path,
            topology,
        )
        # Deploy Configuration
        for node in lab["nodes"]:
            node_id = self.get_node_id(
                lab_path,
                node["name"],
            )

            config_path = Path("build") / f"{node['device']}.cfg"

            with open(config_path, "r") as file:
                config = file.read()

            self.set_node_config(
                lab_path,
                node_id,
                config,
            )
        
        return lab_path
    
    def deploy_topology(self, lab_path, topology):
        for link in topology:
            self.deploy_link(lab_path, link)
        
    def edit_network(
        self,
        lab_path,
        network_id,
        visibility=None,
    ):
        network = {
            "id": network_id,
        }

        if visibility is not None:
            network["visibility"] = visibility

        return self.put_path(
            f"labs/{lab_path}/networks",
            [network],
        )
    
    def get_lab(self, lab_path):
        return self.get_path(f"labs/{lab_path}")

    def get_networks(self, lab_path):
        return self.get_path(f"labs/{lab_path}/networks")

    def get_node_config(self, lab_path, node_id):
        return self.get_path(
            f"labs/{lab_path}/configs/{node_id}"
        )
    
    def get_node_id(self, lab_path, node_name):
        nodes = self.get_nodes(lab_path)["data"]

        for node_id, node in nodes.items():
            if node["name"] == node_name:
                return int(node_id)

        raise ValueError(f"Node not found: {node_name}")
    
    def get_nodes(self, lab_path):
        return self.get_path(f"labs/{lab_path}/nodes")

    def get_path(self, path):
        url = f"{self.host}/api/{path}"

        response = self.session.get(url)

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()

    def get_templates(self):
        return self.get_path("list/templates/")

    def get_topology(self, lab_path):
        return self.get_path(f"labs/{lab_path}/topology")

    def interface_id(self, interface_name):
        return int(interface_name.split("/")[-1])
    
    def put_path(self, path, data=None):
        url = f"{self.host}/api/{path}"

        response = self.session.put(
            url,
            json=data,
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()
    
    def post_path(self, path, data=None):
        url = f"{self.host}/api/{path}"

        response = self.session.post(
            url,
            json=data,
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()
    
    def resolve_endpoint(self, lab_path, endpoint):
        device_name, interface_name = endpoint.split(":", 1)

        node_id = self.get_node_id(
            lab_path,
            device_name,
        )

        interface_id = self.interface_id(interface_name)

        return {
            "node_id": node_id,
            "interface_id": interface_id,
        }

    def set_node_config(self, lab_path, node_id, config):
        return self.put_path(
            f"labs/{lab_path}/configs/{node_id}",
            {
                "id": node_id,
                "data": config,
            },
        )
        
def main():
    host = os.environ["EVE_NG_HOST"]
    username = os.environ["EVE_NG_USERNAME"]
    password = os.environ["EVE_NG_PASSWORD"]

    client = EveNGClient(
        host,
        username,
        password,
    )

    client.login() 
    network = {
        "type": "bridge",
        "name": "R1-R2",
        "left": "35%",
        "top": "25%",
        "visibility":"0"
    }


#    result = client.get_lab("Test/API-Test.unl")
    nodes = client.get_nodes("Test/API-Test.unl")
    print(nodes)
    result = client.create_network("Test/API-Test.unl", network)
    print("CREATE NETWORK:")
    print(result)
    networks = client.get_networks("Test/API-Test.unl")
    print("NETWORKS:")
    print(networks) 
    
    network_id = client.connect_nodes(
        "Test/API-Test.unl",
        node_a=3,
        interface_a=1,
        node_b=4,
        interface_b=0,
)

    print("NETWORK_ID:", network_id)
    print(f"NETWORK_ID: {network_id}")

    topology = client.get_topology("Test/API-Test.unl")

    print("TOPOLOGY:")
    print(topology)

    links = client.get_path("labs/Test/API-Test.unl/links")

    print("LINKS:")
    print(links)
    result = client.connect_interface(
        "Test/API-Test.unl",
        node_id=3,
        interface_id=1,
        network_id=network_id,
    )

    print("CONNECT:")
    print(result)
    
    interfaces = client.get_path(
        "labs/Test/API-Test.unl/nodes/3/interfaces"
    )
    
    print("INTERFACES:")
    print(interfaces)

    interfaces = client.get_path(
        "labs/Test/API-Test.unl/nodes/4/interfaces"
    )
    
    print("INTERFACES:")
    print(interfaces)
    
    config = client.get_node_config(
        lab_path,
        node_id,
)

    print(config)
if __name__ == "__main__":
    main()