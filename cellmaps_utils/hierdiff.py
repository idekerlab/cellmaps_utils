import logging
from ndex2.cx2 import RawCX2NetworkFactory, CX2Network

logger = logging.getLogger(__name__)


class HierarchyDiff:
    """
    A class to compare two hierarchies in CX2 (HCX)
    """

    def __init__(self):
        """
        Constructor
        """
        pass

    def compare_hierarchies_from_files(self, hierarchy_a_path=None, hierarchy_b_path=None):
        """
        Compare two hierarchies from file paths.

        :param hierarchy_a_path: Path to hierarchy to compare
        :type hierarchy_a_path: str
        :param hierarchy_b_path: Path to hierarchy to compare
        :type hierarchy_b_path: str
        """
        factory = RawCX2NetworkFactory()
        hierarchy_a = factory.get_cx2network(hierarchy_a_path)
        hierarchy_b = factory.get_cx2network(hierarchy_b_path)
        return self.compare_hierarchies(hierarchy_a, hierarchy_b)

    @staticmethod
    def compare_hierarchies(hierarchy_a=None, hierarchy_b=None):
        """
        Compare two hierarchies in CX2 format. It looks at each system and outputs a robustness score
        which correlates to how stable the system is in the hierarchies generated. It outputs a hierarchy with
        the robustness score added to the systems.

        :param hierarchy_a: Hierarchy to compare
        :type hierarchy_a: ndex2.cx2.CX2Network
        :param hierarchy_b: Hierarchy to compare
        :type hierarchy_b: ndex2.cx2.CX2Network
        """
        nodes_a = hierarchy_a.get_nodes()
        nodes_b = hierarchy_b.get_nodes()

        # Compute overlap scores for nodes based on CD_MemberList
        all_node_ids = set(nodes_a.keys()).union(nodes_b.keys())
        node_overlap_scores = {}

        for node_id in all_node_ids:
            members_a = set(nodes_a.get(node_id, {}).get('v', {}).get('CD_MemberList', '').split())
            members_b = set(nodes_b.get(node_id, {}).get('v', {}).get('CD_MemberList', '').split())

            if members_a and members_b:
                # Calculate overlap score based on intersection and union
                overlap = len(members_a.intersection(members_b))
                union = len(members_a.union(members_b))
                score = overlap / union if union > 0 else 0
            else:
                score = 0

            node_overlap_scores[node_id] = score

        # Create a new hierarchy to store results
        result_hierarchy = CX2Network()

        # Add nodes from hierarchy_a with robustness scores
        for node_id, data in nodes_a.items():
            score = node_overlap_scores.get(node_id, 0)
            data['v']['robustness_score'] = score
            result_hierarchy.add_node(node_id=node_id, attributes=data['v'])

        # Add nodes from hierarchy_b if they don't already exist in the result hierarchy
        for node_id, data in nodes_b.items():
            if node_id not in nodes_a:
                score = node_overlap_scores.get(node_id, 0)
                data['v']['robustness_score'] = score
                result_hierarchy.add_node(node_id=node_id, attributes=data['v'])

        return result_hierarchy
