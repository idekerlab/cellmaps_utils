import logging

import numpy as np
import pandas as pd
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

    @staticmethod
    def _calculate_jaccard(setA, setB):
        """
        Calculate the Jaccard similarity between two sets.

        The Jaccard similarity is defined as |A ∩ B| / |A ∪ B|.

        :param setA: First set.
        :type setA: set
        :param setB: Second set.
        :type setB: set
        :return: The Jaccard similarity index.
        :rtype: float
        """
        overlap = len(setA.intersection(setB))
        union = len(setA.union(setB))
        return overlap / union if union > 0 else 0

    def _hierarchy_overlap(self, ref_hierarchy, alt_hierarchy, ji_thre=0.4):
        """
        Computes a pass/fail matrix based on Jaccard similarity between nodes
        in two CX2Network hierarchies. For each node in the alternative hierarchy,
        it calculates the Jaccard index with each node in the reference hierarchy.
        A threshold is applied, and values above the threshold are set to 1, while
        values below are set to 0.

        :param ref_hierarchy: The reference hierarchy to compare against.
        :type ref_hierarchy: ndex2.cx2.CX2Network
        :param alt_hierarchy: The alternative hierarchy being compared.
        :type alt_hierarchy: ndex2.cx2.CX2Network
        :param ji_thre: The threshold above which Jaccard values are marked as 1 (pass).
        :type ji_thre: float
        :return: A DataFrame of pass/fail (1/0) based on Jaccard similarity.
        :rtype: pandas.DataFrame
        """
        ref_nodes = ref_hierarchy.get_nodes()
        nodes = alt_hierarchy.get_nodes()

        # Prepare a DataFrame to hold JI values
        ji_df = pd.DataFrame(index=nodes.keys(), columns=ref_nodes.keys(), dtype=float)

        for node_id, node_obj in nodes.items():
            ont_comp_genes = set(node_obj.get('v', {}).get('CD_MemberList', '').split())
            for ref_node_id, ref_node_obj in ref_nodes.items():
                comp_genes = set(ref_node_obj.get('v', {}).get('CD_MemberList', '').split())
                ji_df.at[node_id, ref_node_id] = self._calculate_jaccard(ont_comp_genes, comp_genes) \
                    if ont_comp_genes and comp_genes else 0

        # Make a "pass/fail" matrix: 0 if JI <= threshold, 1 otherwise
        pass_fail_df = (ji_df > ji_thre).astype(int)

        return pass_fail_df

    def compute_hierarchy_robustness(self, ref_hierarchy, alt_hierarchies, ji_thre=0.4):
        """
        Computes a robustness score for each node in a reference hierarchy based on
        its overlap across multiple alternative hierarchies. The higher the overlap
        (above the threshold), the higher the robustness score.

        :param ref_hierarchy: The reference hierarchy whose nodes' robustness is computed.
        :type ref_hierarchy: ndex2.cx2.CX2Network or dict (raw CX2)
        :param alt_hierarchies: A list of alternative hierarchies to compare against.
        :type alt_hierarchies: list[ndex2.cx2.CX2Network or dict]
        :param ji_thre: The Jaccard threshold used to determine overlap.
        :type ji_thre: float
        :return: The reference hierarchy with an added 'robustness' attribute for each node.
        :rtype: ndex2.cx2.CX2Network
        """
        factory = RawCX2NetworkFactory()
        ref_hier = ref_hierarchy if isinstance(ref_hierarchy, CX2Network) else factory.get_cx2network(ref_hierarchy)
        alt_hiers = []
        for hier in alt_hierarchies:
            alt_hiers.append(hier if isinstance(hier, CX2Network) else factory.get_cx2network(hier))
        r_hier = pd.DataFrame(index=list(ref_hier.get_nodes().keys()))
        r_hier['robustness'] = [0] * len(r_hier)
        for hierarchy in alt_hiers:
            ji_df = self._hierarchy_overlap(ref_hier, hierarchy, ji_thre)
            maxs = ji_df.max(axis=0)
            r_hier.loc[ji_df.columns, 'robustness'] += np.array(maxs).astype(int)
        r_hier['robustness'] /= len(alt_hiers)
        for node_id, robustness in r_hier['robustness'].to_dict().items():
            ref_hier.add_node_attribute(node_id, 'robustness', robustness)

        return ref_hier

    def compare_hierarchies(self, hierarchy_a=None, hierarchy_b=None, ji_thre=0.4):
        """
        Compare two hierarchies in CX2 format by calculating Jaccard overlaps and
        assigning a 'robustness' (overlap) score to each node in the first hierarchy.

        :param hierarchy_a: The first (reference) hierarchy to compare.
        :type hierarchy_a: ndex2.cx2.CX2Network
        :param hierarchy_b: The second (alternative) hierarchy to compare against.
        :type hierarchy_b: ndex2.cx2.CX2Network
        :param ji_thre: The threshold above which Jaccard values are considered an overlap.
        :type ji_thre: float
        :return: The first hierarchy with an added 'robustness' node attribute.
        :rtype: ndex2.cx2.CX2Network
        """
        ji_df = self._hierarchy_overlap(hierarchy_a, hierarchy_b, ji_thre)
        maxs = ji_df.max(axis=0)
        node_overlap_scores = maxs.to_dict()

        # Add nodes annotate nodes in hierarchy_a robustness scores
        for node_id, data in hierarchy_a.get_nodes().items():
            score = node_overlap_scores.get(node_id, 0)
            hierarchy_a.add_node_attribute(node_id, 'robustness', score)

        return hierarchy_a

    def compare_hierarchies_from_files(self, hierarchy_a_path=None, hierarchy_b_path=None, ji_thre=0.4):
        """
        Compare two hierarchies from files then calculating overlap-based scores.

        :param hierarchy_a_path: Path to the first (reference) hierarchy file.
        :type hierarchy_a_path: str
        :param hierarchy_b_path: Path to the second (alternative) hierarchy file.
        :type hierarchy_b_path: str
        :param ji_thre: The threshold above which Jaccard values are considered an overlap.
        :type ji_thre: float
        :return: The first hierarchy (from hierarchy_a_path) with added robustness scores.
        :rtype: ndex2.cx2.CX2Network
        """
        factory = RawCX2NetworkFactory()
        hierarchy_a = factory.get_cx2network(hierarchy_a_path)
        hierarchy_b = factory.get_cx2network(hierarchy_b_path)
        return self.compare_hierarchies(hierarchy_a, hierarchy_b, ji_thre)
