import logging
import os.path

from ndex2.cx2 import CX2Network, RawCX2NetworkFactory
import ndex2.constants as constants

from cellmaps_utils import hcx_utils
from cellmaps_utils.exceptions import CellMapsError

logger = logging.getLogger(__name__)


class InteractomeToDDOTConverter:

    def __init__(self, output_dir, interactome_path, ddot_file_name='interactome_ddot.txt'):
        self._interactome_path = interactome_path
        self._output_file = os.path.join(output_dir, ddot_file_name)

    def generate_ddot_format_file(self):
        factory = RawCX2NetworkFactory()
        interactome = factory.get_cx2network(self._interactome_path)
        with open(self._output_file, 'w') as f:
            for edge_id, edge_values in interactome.get_edges().items():
                source = edge_values[constants.EDGE_SOURCE]
                target = edge_values[constants.EDGE_TARGET]
                if constants.EDGE_INTERACTION_EXPANDED in edge_values[constants.ASPECT_VALUES]:
                    interaction = edge_values[constants.ASPECT_VALUES][constants.EDGE_INTERACTION_EXPANDED]
                    f.write(f"{source}\t{target}\t{interaction}\n")
                else:
                    f.write(f"{source}\t{target}\n")


class DDOTToInteractomeConverter:

    def __init__(self, output_dir, interactome_ddot_path, interactome_file_name='interactome.cx2'):
        self._interactome_ddot_path = interactome_ddot_path
        self._output_file = os.path.join(output_dir, interactome_file_name)

    def generate_interactome_file(self):
        interactome = CX2Network()
        with open(self._interactome_ddot_path, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                id_source_node = interactome.lookup_node_id_by_name(parts[0])
                source_node = id_source_node if id_source_node is not None else interactome.add_node(
                    attributes={'name': parts[0]})
                id_target_node = interactome.lookup_node_id_by_name(parts[1])
                target_node = id_target_node if id_target_node is not None else interactome.add_node(
                    attributes={'name': parts[1]})
                id_edge = interactome.add_edge(source=source_node, target=target_node)
                if len(parts) >= 3:
                    interactome.add_edge_attribute(id_edge, constants.EDGE_INTERACTION_EXPANDED, parts[3])
        interactome.write_as_raw_cx2(self._output_file)


class HierarchyToDDOTConverter:

    def __init__(self, output_dir, hierarchy_path, ontology_file_name='ontology.ont'):
        self._hierarchy_path = hierarchy_path
        self._output_file = os.path.join(output_dir, ontology_file_name)

    def generate_ontology_ddot_file(self):
        factory = RawCX2NetworkFactory()
        hierarchy = factory.get_cx2network(self._hierarchy_path)
        with open(self._output_file, 'w') as f:
            for _, edge_values in hierarchy.get_edges().items():
                source_id = edge_values[constants.EDGE_SOURCE]
                source = hierarchy.get_node(source_id)[constants.ASPECT_VALUES].get(constants.NODE_NAME_EXPANDED,
                                                                                    source_id)
                target_id = edge_values[constants.EDGE_TARGET]
                target = hierarchy.get_node(target_id)[constants.ASPECT_VALUES].get(constants.NODE_NAME_EXPANDED,
                                                                                    target_id)
                f.write(f"{source}\t{target}\tdefault\n")
            for node_id, node_values in hierarchy.get_nodes().items():
                node_attr = node_values[constants.ASPECT_VALUES]
                node = node_attr.get(constants.NODE_NAME_EXPANDED, node_id)
                genes = node_attr.get('CD_MemberList', '').split(' ')
                for gene in genes:
                    f.write(f"{node}\t{gene}\tgene\n")


class DDOTToHierarchyConverter:

    def __init__(self, output_dir, ontology_ddot_path, parent_ddot_path=None, parent_ndex_url=None,
                 host='ndexbio.org', parent_uuid=None, ndex_user=None, ndex_password=None,
                 hierarchy_filename='hierarchy.cx2', interactome_filename='hierarchy_parent.cx2'):
        self._output_dir = output_dir
        self._hierarchy_file = os.path.join(output_dir, hierarchy_filename)
        self._interactome_filename = interactome_filename
        self._ontology_ddot_path = ontology_ddot_path
        if parent_ndex_url is None and parent_ddot_path is None:
            raise CellMapsError("Specifying either url of parent interactome in NDEx, or edge list of interactome"
                                " is required!")
        if parent_ddot_path is not None and (parent_ndex_url is not None or parent_uuid is not None):
            raise CellMapsError("You need to specify parent network as edge list in file, or as network in NDEx, "
                                "not both!")
        self._parent_url = parent_ndex_url
        self._parent_edgelist = parent_ddot_path
        self._host = host
        self._uuid = parent_uuid
        self._username = ndex_user
        self._password = ndex_password

    def generate_hierarchy_hcx_file(self):
        interactome = hcx_utils.get_interactome(self._host, self._uuid, self._username, self._password,
                                                self._parent_edgelist)
        hierarchy = self._get_hierarchy(interactome)
        hcx_utils.add_hcx_network_annotations(hierarchy, interactome, self._output_dir, self._interactome_filename,
                                              self._host, self._uuid)
        hierarchy.write_as_raw_cx2(self._hierarchy_file)

    def _get_hierarchy(self, interactome):
        """
        Constructs the hierarchy based on the DDOT edge list and node list and uses interactome to add HCX information.

        :param interactome: The interactome network.
        :type interactome: CX2Network
        :return: A CX2Network object representing the hierarchy.
        :rtype: CX2Network
        """
        hierarchy = CX2Network()

        with open(self._ontology_ddot_path, 'r') as f:
            for line in f:
                source, target, edge_type = line.strip().split('\t')
                if 'gene' in edge_type.lower():
                    source_id = hierarchy.lookup_node_id_by_name(source)
                    if source_id is not None:
                        node_attr = hierarchy.get_node(source_id)[constants.ASPECT_VALUES]
                        target_id = interactome.lookup_node_id_by_name(target)
                        if 'CD_MemberList' not in node_attr:
                            hierarchy.add_node_attribute(source_id, 'CD_MemberList', target)
                            hierarchy.add_node_attribute(source_id, 'HCX::members', [target_id])
                        else:
                            hierarchy.add_node_attribute(source_id, 'CD_MemberList',
                                                         node_attr['CD_MemberList'] + ' ' + target)
                            node_attr['HCX::members'].append(target_id)
                            hierarchy.add_node_attribute(source_id, 'HCX::members', node_attr['HCX::members'])
                else:
                    source_id = hierarchy.lookup_node_id_by_name(source)
                    if source_id is None:
                        source_id = hierarchy.add_node(attributes={constants.NODE_NAME_EXPANDED: source})
                    target_id = hierarchy.lookup_node_id_by_name(target)
                    if target_id is None:
                        target_id = hierarchy.add_node(attributes={constants.NODE_NAME_EXPANDED: target})
                    hierarchy.add_edge(source=source_id, target=target_id)

        root_nodes = hcx_utils.get_root_nodes(hierarchy)
        hcx_utils.add_isroot_node_attribute(hierarchy, root_nodes=root_nodes)

        return hierarchy
