#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_utils.cellmaps_io` package."""

import os
import sys
import shutil
import tempfile
import json
from datetime import date
import unittest
from unittest.mock import patch

from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_utils.exceptions import CellMapsProvenanceError


class TestProvenanceUtil(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_run_cmd_timeout(self):
        temp_dir = tempfile.mkdtemp()
        try:
            py_file = os.path.join(temp_dir, 'sleep.py')
            with open(py_file, 'w') as f:
                f.write('import time\r\n')
                f.write('time.sleep(60)\r\n')
            p = ProvenanceUtil()
            p._run_cmd([sys.executable, py_file], timeout=1)
        except CellMapsProvenanceError as ce:
            self.assertTrue('Process timed out' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_example_dataset_provenance(self):

        # default
        example = ProvenanceUtil.example_dataset_provenance()
        self.assertEqual({'name': 'Name of dataset',
                          'author': 'Author of dataset',
                          'version': 'Version of dataset',
                          'date-published': 'Date dataset was published',
                          'description': 'Description of dataset',
                          'data-format': 'Format of data'}, example)

        # with ids
        example = ProvenanceUtil.example_dataset_provenance(with_ids=True)
        self.assertEqual({'guid': 'ID of dataset'}, example)

        # with required only False
        example = ProvenanceUtil.example_dataset_provenance(requiredonly=False)
        expected_full = {'name': 'Name of dataset',
                          'author': 'Author of dataset',
                          'version': 'Version of dataset',
                          'date-published': 'Date dataset was published',
                          'description': 'Description of dataset',
                          'data-format': 'Format of data',
                          'url': 'URL of datset', 'used-by': '?',
                          'derived-from': '?', 'associated-publication': '?',
                          'additional-documentation': '?'}
        self.assertEqual(expected_full, example)

        # with required only None
        example = ProvenanceUtil.example_dataset_provenance(requiredonly=None)
        self.assertEqual(expected_full, example)

    def test_register_rocrate_actual_invocation(self):
        """
        Registers temp directory as a crate
        with all default values
        :return:
        """
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            crate_file = os.path.join(temp_dir, constants.RO_CRATE_METADATA_FILE)
            self.assertTrue(os.path.isfile(crate_file))
            self.assertTrue(os.path.getsize(crate_file) > 0)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_computation_actual_invocation(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            c_id = prov.register_computation(temp_dir, run_by='runby',
                                             name='name', description='desc',
                                             command='cmd')
            self.assertTrue(len(c_id) > 0)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_computation_with_software_datasets_actual_invocation(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)

            used_dataset = []
            used_software = []
            generated = []
            for x in range(0, 8000):
                used_dataset.append('ark:/d' + str(x))
                used_software.append('ark:/s' + str(x))
                generated.append('ark:/g' + str(x))

            c_id = prov.register_computation(temp_dir, run_by='runby',
                                             name='name', description='desc',
                                             command='cmd',
                                             used_dataset=used_dataset,
                                             used_software=used_software,
                                             generated=generated)
            self.assertTrue(len(c_id) > 0)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_software(self):
        # Todo: due to fairscape-cli bug this is failing
        #       and the test expects the failure for now
        #       once fairscape-cli fixes
        #       https://github.com/fairscape/fairscape-cli/issues/7
        #       remove the exception check
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            s_id = prov.register_software(temp_dir, name='name', description='must be 10 characters',
                                          version='0.1.0', file_format='.py',
                                          url='http://foo.com')
            # this is never reached due to
            # https://github.com/fairscape/fairscape-cli/issues/7
            self.assertTrue(len(s_id) > 0)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_dataset(self):

        temp_dir = tempfile.mkdtemp()
        try:
            subdir = os.path.join(temp_dir, 'input')
            os.makedirs(subdir, mode=0o755)
            src_file = os.path.join(subdir, 'xx')
            with open(src_file, 'w') as f:
                f.write('hi')

            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            d_id = prov.register_dataset(temp_dir,
                                         source_file=src_file,
                                         skip_copy=False,
                                         data_dict={'name': 'Name of dataset',
                                                    'author': 'Author of dataset',
                                                    'version': 'Version of dataset',
                                                    'date-published': 'Date dataset was published MM-DD-YYYY',
                                                    'description': 'Description of dataset',
                                                    'data-format': 'Format of data'})
            self.assertTrue(len(d_id) > 0)

        except CellMapsProvenanceError as ce:
            print(str(ce))
            self.assertEqual('', str(ce))
            self.assertTrue('Error adding dataset' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_register_dataset_skipcopy_true(self):

        temp_dir = tempfile.mkdtemp()
        try:
            src_file = os.path.join(temp_dir, 'xx')
            with open(src_file, 'w') as f:
                f.write('hi')

            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            d_id = prov.register_dataset(temp_dir,
                                         source_file=src_file,
                                         skip_copy=True,
                                         data_dict={'name': 'Name of dataset',
                                                    'author': 'Author of dataset',
                                                    'version': 'Version of dataset',
                                                    'date-published': 'Date dataset was published MM-DD-YYYY',
                                                    'description': 'Description of dataset',
                                                    'data-format': 'Format of data'})
            self.assertTrue(len(d_id) > 0)

        except CellMapsProvenanceError as ce:
            print(str(ce))
            self.assertEqual('', str(ce))
            self.assertTrue('Error adding dataset' in str(ce))
        finally:
            shutil.rmtree(temp_dir)


