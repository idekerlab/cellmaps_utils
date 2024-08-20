import json
import logging
import os

import ndex2
from ndex2.cx2 import RawCX2NetworkFactory, CX2Network
import ndex2.constants as constants
import cellmaps_utils.constants as cellmaps_constants
from cellmaps_utils import hcx_utils
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

    def __init__(self, output_dir, nodes_file_path, edges_file_path, parent_ndex_url=None, parent_edgelist_path=None,
                 ndex_user=None, ndex_password=None):
        """
        Initializes the converter with file paths and optional parent network details.

        Parent network can be specified as edge list or link to interactome in NDEx needs to be provided, if the
        network is private, username and password need to be specified.

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
        :param ndex_user: NDEx username (optional).
        :type ndex_user: str, optional
        :param ndex_password: NDEx password (optional).
        :type ndex_password: str, optional
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
        self.username = ndex_user
        self.password = ndex_password

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
        self.host, self.uuid = hcx_utils.get_host_and_uuid_from_network_url(self.parent_url)
        interactome = hcx_utils.get_interactome(self.host, self.uuid, self.username, self.password,
                                                self.parent_edgelist)
        hierarchy = hcx_utils.add_hcx_network_annotations(self._get_hierarchy(interactome), interactome,
                                                          self.output_dir, interactome_filename, self.host, self.uuid)
        hierarchy.write_as_raw_cx2(hierarchy_path)

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

        root_nodes = hcx_utils.get_root_nodes(hierarchy)
        hcx_utils.add_isroot_node_attribute(hierarchy, root_nodes=root_nodes)

        return hierarchy
