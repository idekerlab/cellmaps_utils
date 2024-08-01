import os
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from cellmaps_utils.hidefconverter import HierarchyToHiDeFConverter, HiDeFToHierarchyConverter
from ndex2 import constants


class TestHierarchyToHiDeFConverter(unittest.TestCase):
    def setUp(self):
        self.directory = 'fakedir'
        self.mock_hierarchy = Mock()

        with patch('ndex2.cx2.RawCX2NetworkFactory.get_cx2network', return_value=self.mock_hierarchy):
            self.converter = HierarchyToHiDeFConverter(self.directory, self.directory)

    def test_format_node(self):
        self.mock_hierarchy.get_node.return_value = {
            constants.ASPECT_VALUES: {
                'name': 'Node1',
                'CD_MemberList_Size': 10,
                'CD_MemberList': 'Member1 Member2',
                'HiDeF_persistence': 0.5
            }
        }
        result = self.converter._format_node(1)
        self.assertEqual(result, "Node1\t10\tMember1 Member2\t0.5")

    def test_format_edge(self):
        self.mock_hierarchy.get_edge.return_value = {
            constants.EDGE_SOURCE: 1,
            constants.EDGE_TARGET: 2
        }
        self.mock_hierarchy.get_node.side_effect = [
            {constants.ASPECT_VALUES: {'name': 'Node1'}},
            {constants.ASPECT_VALUES: {'name': 'Node2'}}
        ]
        result = self.converter._format_edge(1)
        self.assertEqual(result, "Node1\tNode2\tdefault")

    def test_find_node_name_by_id(self):
        self.mock_hierarchy.get_node.return_value = {
            constants.ASPECT_VALUES: {'name': 'Node1'}
        }
        result = self.converter._find_node_name_by_id(1)
        self.assertEqual(result, "Node1")


class TestHiDeFToHierarchyConverter(unittest.TestCase):
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
        self.nodes_file_path = os.path.join(os.path.dirname(__file__), 'data', 'hidef_output.nodes')
        self.edges_file_path = os.path.join(os.path.dirname(__file__), 'data', 'hidef_output.edges')
        self.parent = os.path.join(os.path.dirname(__file__), 'data', 'parent_edgelist')

        self.converter = HiDeFToHierarchyConverter(self.output_dir, self.nodes_file_path, self.edges_file_path,
                                                   parent_edgelist_path=self.parent)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_generate_hierarchy_hcx_file(self):
        self.converter.generate_hierarchy_hcx_file()
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, 'hierarchy.cx2')))

    def test_get_interactome(self):
        interactome = self.converter._get_interactome()
        self.assertEqual(len(interactome.get_nodes()), 6)
        self.assertEqual(len(interactome.get_edges()), 7)

    def test_get_hierarchy(self):
        interactome = self.converter._get_interactome()
        hierarchy = self.converter._get_hierarchy(interactome)
        self.assertEqual(len(hierarchy.get_nodes()), 2)
        self.assertEqual(len(hierarchy.get_edges()), 1)
        self.assertEqual(len(hierarchy.get_node(0).get(constants.ASPECT_VALUES).get('HCX::members')),
                         6)
