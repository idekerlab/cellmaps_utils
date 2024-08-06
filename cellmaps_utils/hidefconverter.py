import json
import logging
import os

import ndex2
from ndex2.cx2 import RawCX2NetworkFactory, CX2Network
import ndex2.constants as constants
import cellmaps_utils.constants as cellmaps_constants
from cellmaps_utils.exceptions import CellMapsError

logger = logging.getLogger(__name__)


class HierarchyToHiDeFConverter:
    """
    A class to convert a hierarchy network (in CX2 format) to a HiDeF format.
    """
    HIDEF_OUT_PREFIX = 'hidef_output_gene_names'

    def __init__(self, output_dir, input_dir=None, hierarchy=None):
        """
        Constructor

        :param input_dir: The directory containing the hierarchy file.
        :type input_dir: str
        :param output_dir: The directory where the output files will be stored.
        :type output_dir: str
        """
        self.output_dir = output_dir
        if hierarchy is None:
            if input_dir is None:
                raise CellMapsError("Either hierarch_path or input_dir should be specified!")
            self.hierarchy_path = os.path.join(input_dir,
                                               cellmaps_constants.HIERARCHY_NETWORK_PREFIX +
                                               cellmaps_constants.CX2_SUFFIX)
        else:
            self.hierarchy_path = hierarchy
        try:
            factory = RawCX2NetworkFactory()
            self.hierarchy = factory.get_cx2network(self.hierarchy_path)
        except Exception as e:
            logger.error(f"Failed to load hierarchy: {e}")
            raise CellMapsError(f"Failed to load hierarchy: {e}")

    def generate_hidef_files(self, nodes_filename=HIDEF_OUT_PREFIX + '.nodes',
                             edges_filename=HIDEF_OUT_PREFIX + '.edges'):
        """
        Generates HiDeF files .nodes and .edges from the hierarchy network.
        """
        try:
            nodes = self.hierarchy.get_nodes()
            edges = self.hierarchy.get_edges()
            formatted_nodes = self._format_aspect(nodes, self._format_node)
            formatted_edges = self._format_aspect(edges, self._format_edge)
            nodes_path = self._write_to_file(nodes_filename, formatted_nodes)
            edges_path = self._write_to_file(edges_filename, formatted_edges)
            return nodes_path, edges_path
        except Exception as e:
            logger.error(f"Error during HiDeF generation: {e}")
            raise CellMapsError(f"Error during HiDeF generation: {e}")

    @staticmethod
    def _format_aspect(aspect, format_function):
        """
        Formats aspect list (nodes or edges) using a specified format function.

        :param aspect: A list of aspect IDs (nodes or edges).
        :type aspect: dict
        :param format_function: A function to format a single entity.
        :type format_function: function
        :return: A list of formatted nodes or edges.
        :rtype: list
        """
        return [format_function(aspect_id) for aspect_id in aspect]

    def _format_node(self, node_id):
        """
        Formats a node for HiDeF output.

        :param node_id: The ID of the node to be formatted.
        :type node_id: int
        :return: A formatted string representing the node.
        :rtype: str
        """
        node = self.hierarchy.get_node(node_id)
        node_attr = node[constants.ASPECT_VALUES]
        formatted_node = (node_attr.get(constants.NODE_NAME_EXPANDED, node_id), node_attr.get('CD_MemberList_Size', 0),
                          node_attr.get('CD_MemberList', ''), node_attr.get('HiDeF_persistence', 0))
        return "\t".join(map(str, formatted_node))

    def _format_edge(self, edge_id):
        """
        Formats an edge for HiDeF output.

        :param edge_id: The ID of the edge to be formatted.
        :type edge_id: int
        :return: A formatted string representing the edge.
        :rtype: str
        """
        edge = self.hierarchy.get_edge(edge_id)
        source_node = self._find_node_name_by_id(edge[constants.EDGE_SOURCE])
        target_node = self._find_node_name_by_id(edge[constants.EDGE_TARGET])
        return f"{source_node}\t{target_node}\tdefault"

    def _find_node_name_by_id(self, node_id):
        """
        Finds the name of a node given its ID.

        :param node_id: The ID of the node.
        :type node_id: int
        :return: The name of the node.
        :rtype: str
        """
        node = self.hierarchy.get_node(node_id)
        return node[constants.ASPECT_VALUES].get(constants.NODE_NAME_EXPANDED, node_id)

    def _write_to_file(self, filename, lines):
        """
        Writes output to a file.

        :param filename: The name of the file to write to.
        :type filename: str
        :param lines: A list of strings to be written to the file.
        :type lines: list
        """
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, 'w') as file:
            file.write('\n'.join(lines))
        return file_path


class HiDeFToHierarchyConverter:
    """
    A class to convert a edge list and node list in HiDeF format to hierarchy in HCX.

    .. versionadded:: 0.5.0
           The class was added to enable conversion from HiDeF-formatted edge and node files to hierarchy in HCX.
    """

    def __init__(self, output_dir, nodes_file_path, edges_file_path, parent_ndex_url=None, parent_edgelist_path=None):
        """
        Initializes the converter with file paths and optional parent network details.

        :param output_dir: Directory where the output files will be stored.
        :type output_dir: str
        :param nodes_file_path: File path for the nodes file.
        :type nodes_file_path: str
        :param edges_file_path: File path for the edges file.
        :type edges_file_path: str
        :param parent_ndex_url: URL of parent interactome in NDEx (optional).
        :type parent_ndex_url: str, optional
        :param parent_edgelist_path: Path to the edge list of the interactome (optional).
        :type parent_edgelist_path: str, optional
        """
        self.output_dir = output_dir
        self.nodes_file_path = nodes_file_path
        self.edges_file_path = edges_file_path
        if parent_ndex_url is None and parent_edgelist_path is None:
            raise CellMapsError("Specifying either url of parent interactome in NDEx, or edge list of the interactome"
                                " is required!")
        self.parent_url = parent_ndex_url
        self.parent_edgelist = parent_edgelist_path
        self.host = None
        self.uuid = None

    def generate_hierarchy_hcx_file(self, hierarchy_filename='hierarchy.cx2',
                                    interactome_filename='hierarchy_parent.cx2'):
        """
        Generates the HiDeF hierarchy file in CX2 format. If the object is initialized with parent network's edge list,
        the interactome in CX2 format will be generated in output directory as well. If the object is initialized with
        uuid of parent network, only hierarchy will be generated.

        :param hierarchy_filename: The name of the file to write the hierarchy.
        :type hierarchy_filename: str
        :param interactome_filename: The name of the file to write the interactome (parent network of the hierarchy).
        :type interactome_filename: str
        """
        hierarchy_path = os.path.join(self.output_dir, hierarchy_filename)
        interactome = self._get_interactome()
        hierarchy = self._add_hcx_network_annotations(self._get_hierarchy(interactome), interactome,
                                                      interactome_filename)
        hierarchy.write_as_raw_cx2(hierarchy_path)

    def _get_interactome(self):
        """
        Retrieves the interactome either from NDEx or from a local edge list.

        :return: A CX2Network object representing the interactome.
        :rtype: CX2Network
        """
        interactome = CX2Network()
        if self.parent_url is not None:
            self.host, _, _, self.uuid = self.parent_url.replace('https://', '').replace('http:/', '').split('/')
            client = ndex2.client.Ndex2(host=self.host)
            factory = RawCX2NetworkFactory()
            client_resp = client.get_network_as_cx2_stream(self.uuid)
            interactome = factory.get_cx2network(json.loads(client_resp.content))
        else:
            with open(self.parent_edgelist, 'r') as f:
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

    def _get_hierarchy(self, interactome):
        """
        Constructs the hierarchy based on the HiDeF edge list and node list and uses interactome to add HCX information.

        :param interactome: The interactome network.
        :type interactome: CX2Network
        :return: A CX2Network object representing the hierarchy.
        :rtype: CX2Network
        """
        hierarchy = CX2Network()

        with open(self.nodes_file_path, 'r') as f:
            for line in f:
                name, size, genes, persistence = line.strip().split('\t')
                hcx_members = []
                for gene in genes.split():
                    hcx_members.append(interactome.lookup_node_id_by_name(gene))
                node_attributes = {
                    constants.NODE_NAME_EXPANDED: name,
                    'CD_MemberList_Size': size,
                    'CD_MemberList': genes,
                    'HCX::members': hcx_members,
                    'HiDeF_persistence': persistence
                }
                hierarchy.add_node(attributes=node_attributes)

        with open(self.edges_file_path, 'r') as f:
            for line in f:
                source, target, _ = line.strip().split('\t')
                source_id = hierarchy.lookup_node_id_by_name(source)
                target_id = hierarchy.lookup_node_id_by_name(target)
                if source_id is not None and target_id is not None:
                    hierarchy.add_edge(source=source_id, target=target_id)

        root_nodes = self._get_root_nodes(hierarchy)
        self._add_isroot_node_attribute(hierarchy, root_nodes=root_nodes)

        return hierarchy

    def _add_hcx_network_annotations(self, hierarchy, interactome, interactome_name):

        hierarchy.add_network_attribute('ndexSchema', 'hierarchy_v0.1',
                                        datatype='string')
        hierarchy.add_network_attribute('HCX::modelFileCount', '2',
                                        datatype='integer')

        if self.host and self.uuid:
            hierarchy.add_network_attribute('HCX::interactionNetworkHost', self.host)
            hierarchy.add_network_attribute('HCX::interactionNetworkUUID', self.uuid)
        else:
            interactome_path = os.path.join(self.output_dir, interactome_name)
            interactome.write_as_raw_cx2(interactome_path)
            hierarchy.add_network_attribute('HCX::interactionNetworkName', interactome_name,
                                            datatype='string')
        return hierarchy

    @staticmethod
    def _get_root_nodes(hierarchy):
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

    @staticmethod
    def _add_isroot_node_attribute(hierarchy, root_nodes=None):
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
