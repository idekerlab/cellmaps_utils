import json
import os

import ndex2
from ndex2.cx2 import CX2Network, RawCX2NetworkFactory


def get_host_and_uuid_from_network_url(network_url):
    if network_url is None:
        return None, None
    parts = network_url.replace('https://', '').replace('http:/', '').split('/')
    host, uuid = parts[0], parts[-1]
    return host, uuid


def get_interactome(host, uuid, username, password, parent_edgelist):
    """
    Retrieves the interactome either from NDEx or from a local edge list.

    :return: A CX2Network object representing the interactome.
    :rtype: CX2Network
    """
    interactome = CX2Network()
    if host is not None and uuid is not None:
        client = ndex2.client.Ndex2(host=host, username=username, password=password)
        factory = RawCX2NetworkFactory()
        client_resp = client.get_network_as_cx2_stream(uuid)
        interactome = factory.get_cx2network(json.loads(client_resp.content))
    else:
        with open(parent_edgelist, 'r') as f:
            for line in f:
                parts = line.split()
                id_source_node = interactome.lookup_node_id_by_name(parts[0])
                source_node = id_source_node if id_source_node is not None else interactome.add_node(
                    attributes={'name': parts[0]})
                id_target_node = interactome.lookup_node_id_by_name(parts[1])
                target_node = id_target_node if id_target_node is not None else interactome.add_node(
                    attributes={'name': parts[1]})
                interactome.add_edge(source=source_node, target=target_node)
    return interactome


def get_root_nodes(hierarchy):
    """
    In CDAPS the root node has only source edges to children
    so this function counts up number of target edges for each node
    and the one with 0 is the root

    :return: root node ids
    :rtype: set
    """
    all_nodes = set()
    for node_id, node_obj in hierarchy.get_nodes().items():
        all_nodes.add(node_id)

    nodes_with_targets = set()
    for edge_id, edge_obj in hierarchy.get_edges().items():
        nodes_with_targets.add(edge_obj['t'])
    return all_nodes.difference(nodes_with_targets)


def add_isroot_node_attribute(hierarchy, root_nodes=None):
    """
    Using the **root_nodes** set or list, add
    ``HCX::isRoot`` to
    every node setting value to ``True``
    if node id is in **root_nodes**
    otherwise set the value to ``False``
    """
    attr_name = 'HCX::isRoot'
    for node_id, node_obj in hierarchy.get_nodes().items():
        if node_id in root_nodes:
            hierarchy.add_node_attribute(node_id, attr_name, True)
        else:
            hierarchy.add_node_attribute(node_id, attr_name, False)


def add_hcx_network_annotations(hierarchy, interactome, output_dir, interactome_name, host, uuid):
    hierarchy.add_network_attribute('ndexSchema', 'hierarchy_v0.1',
                                    datatype='string')
    hierarchy.add_network_attribute('HCX::modelFileCount', '2',
                                    datatype='integer')

    if host and uuid:
        hierarchy.add_network_attribute('HCX::interactionNetworkHost', host)
        hierarchy.add_network_attribute('HCX::interactionNetworkUUID', uuid)
    else:
        interactome_path = os.path.join(output_dir, interactome_name)
        interactome.write_as_raw_cx2(interactome_path)
        hierarchy.add_network_attribute('HCX::interactionNetworkName', interactome_name,
                                        datatype='string')
    return hierarchy
