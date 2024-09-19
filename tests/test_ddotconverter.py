import os
import shutil
import tempfile
import unittest

from cellmaps_utils import hcx_utils
from cellmaps_utils.ddotconverter import DDOTToHierarchyConverter, DDOTToInteractomeConverter
from ndex2 import constants


class TestDDOTToInteractomeConverter(unittest.TestCase):
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
        self.parent = os.path.join(os.path.dirname(__file__), 'data', 'reactome_ddot.txt')
        self.converter = DDOTToInteractomeConverter(self.output_dir, self.parent)

    def test_generate_interactome_file(self):
        self.converter.generate_interactome_file()
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, 'interactome.cx2')))


class TestDDOTToHierarchyConverter(unittest.TestCase):
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
        self.ontology_ddot_path = os.path.join(os.path.dirname(__file__), 'data', 'ddot_output.ont')
        self.parent = os.path.join(os.path.dirname(__file__), 'data', 'reactome_ddot.txt')

        self.converter = DDOTToHierarchyConverter(self.output_dir, self.ontology_ddot_path,
                                                  parent_ddot_path=self.parent)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_generate_hierarchy_hcx_file(self):
        self.converter.generate_hierarchy_hcx_file()
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, 'hierarchy.cx2')))

    def test_get_hierarchy(self):
        interactome = hcx_utils.get_interactome(None, None, None, None, self.parent)
        hierarchy = self.converter._get_hierarchy(interactome)
        self.assertEqual(len(hierarchy.get_nodes()), 5)
        self.assertEqual(len(hierarchy.get_edges()), 4)
        self.assertEqual(len(hierarchy.get_node(0).get(constants.ASPECT_VALUES).get('HCX::members')),
                         6)
        self.assertEqual(len(hierarchy.get_node(1).get(constants.ASPECT_VALUES).get('HCX::members')),
                         4)
