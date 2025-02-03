import json
import os

import ndex2
from ndex2.cx2 import CX2Network, RawCX2NetworkFactory

from cellmaps_utils.exceptions import CellMapsError


def get_host_and_uuid_from_network_url(network_url):
    """
    Extracts the host and UUID from a given NDEx network URL.

    :param network_url: The URL of the NDEx network.
    :type network_url: str
    :return: A tuple containing the host and the UUID of the network.
    :rtype: tuple
    """
    if network_url is None:
        return None, None
    parts = network_url.replace('https://', '').replace('http:/', '').split('/')
    host, uuid = parts[0], parts[-1]
    return host, uuid


def get_interactome(host, uuid, username, password, parent_edgelist):
    """
    Retrieves the interactome either from NDEx or from a local edge list.

    :param host: The NDEx server host.
    :type host: str
    :param uuid: The UUID of the interactome network in NDEx.
    :type uuid: str
    :param username: The NDEx username for authentication.
    :type username: str
    :param password: The NDEx password for authentication.
    :type password: str
    :param parent_edgelist: Path to a file containing the interactome edge list.
    :type parent_edgelist: str
    :return: A CX2Network object representing the interactome.
    :rtype: CX2Network
    """
    interactome = CX2Network()
    if parent_edgelist is not None:
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
    elif host is not None and uuid is not None:
        client = ndex2.client.Ndex2(host=host, username=username, password=password)
        factory = RawCX2NetworkFactory()
        client_resp = client.get_network_as_cx2_stream(uuid)
        interactome = factory.get_cx2network(json.loads(client_resp.content))
    return interactome


def get_root_nodes(hierarchy):
    """
    Identifies the root nodes in a hierarchical network.

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


def add_isroot_node_attribute(hierarchy, root_nodes):
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


def add_hcx_network_annotations(hierarchy, interactome=None, output_dir='.',
                                interactome_name='hierarchy_parent.cx2', host='www.ndexbio.org', uuid=None):
    """
    Adds HCX network annotations to the hierarchy.

    :param hierarchy: The hierarchical network in CX2 format.
    :type hierarchy: CX2Network
    :param interactome: The interactome network.
    :type interactome: CX2Network, optional
    :param output_dir: Directory where the interactome file will be saved.
    :type output_dir: str, optional
    :param interactome_name: Name of the interactome file.
    :type interactome_name: str, optional
    :param host: NDEx host for interactome retrieval.
    :type host: str, optional
    :param uuid: UUID of the interactome in NDEx.
    :type uuid: str, optional
    :return: The updated hierarchy network with annotations.
    :rtype: CX2Network
    """
    if not isinstance(hierarchy, CX2Network):
        raise CellMapsError("Hierarchy must be an instance of CX2Network.")
    if uuid is None and interactome is None:
        raise CellMapsError("UUID of interactome or interactome (instance of CX2Network) must be specified!")

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


def add_hcx_members_annotation(hierarchy, interactome, gene_column='CD_MemberList'):
    """
    Adds the 'HCX::members' attribute to nodes in the hierarchy based on the interactome.

    :param hierarchy: The hierarchical network in CX2 format.
    :type hierarchy: CX2Network
    :param interactome: The interactome network.
    :type interactome: CX2Network
    :param gene_column: Column name containing gene members.
    :type gene_column: str, optional
    """
    for node_id, node_obj in hierarchy.get_nodes().items():
        memberlist = hierarchy.get_node(node_id).get('v', {}).get(gene_column, '').split(' ')
        membersids = []
        for member in memberlist:
            id_interactome = interactome.lookup_node_id_by_name(member)
            if id_interactome is not None:
                membersids.append(id_interactome)
        hierarchy.add_node_attribute(node_id, 'HCX::members', membersids, datatype='list_of_integer')


def convert_hierarchical_network_to_hcx(hierarchy, interactome_url, ndex_username=None, ndex_password=None,
                                        gene_column='CD_MemberList'):
    """
    Converts a hierarchical network into HCX format by adding necessary annotations and interactome details.

    :param hierarchy: The hierarchical network in CX2 format or a path to the CX2 file.
    :type hierarchy: CX2Network or str
    :param interactome_url: URL of the interactome network in NDEx.
    :type interactome_url: str
    :param ndex_username: NDEx username for authentication.
    :type ndex_username: str, optional
    :param ndex_password: NDEx password for authentication.
    :type ndex_password: str, optional
    :param gene_column: Column name containing gene members.
    :type gene_column: str, optional
    :return: The updated hierarchy network in CX2 format with HCX annotations.
    :rtype: CX2Network
    """
    factory = RawCX2NetworkFactory()
    if isinstance(hierarchy, str):
        hierarchy = factory.get_cx2network(hierarchy)

    # Get the host and uuid of the interactome
    host, uuid = get_host_and_uuid_from_network_url(interactome_url)
    hierarchy = add_hcx_network_annotations(hierarchy, host=host, uuid=uuid)

    # Create CX2Network object from interactome from NDEx
    client = ndex2.client.Ndex2(host=host, username=ndex_username, password=ndex_password)
    client_resp = client.get_network_as_cx2_stream(uuid)
    interactome = factory.get_cx2network(json.loads(client_resp.content))

    # Add HCX::members attribute to node attributes
    add_hcx_members_annotation(hierarchy, interactome, gene_column)

    # Add isRoot attribute to node attributes
    add_isroot_node_attribute(hierarchy, get_root_nodes(hierarchy))
    return hierarchy
