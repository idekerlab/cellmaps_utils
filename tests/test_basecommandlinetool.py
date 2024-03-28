#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `BaseCommandLineTool`."""
import json
import os
import argparse
import shutil
import tempfile
import unittest

from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.basecmdtool import BaseCommandLineTool


class TestBaseCommandLineTool(unittest.TestCase):
    """Tests for `BaseCommandLineTool`"""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_run(self):
        cmdtool = BaseCommandLineTool()
        try:
            cmdtool.run()
            self.fail('Expected exception')
        except CellMapsError as ce:
            self.assertTrue('Must be implemented by subclass' in str(ce))

    def test_add_subparser(self):
        try:
            BaseCommandLineTool.add_subparser(None)
            self.fail('Expected exception')
        except CellMapsError as ce:
            self.assertTrue('Must be implemented by subclass' in str(ce))

    def test_save_dataset_info_to_json(self):
        temp_dir = tempfile.mkdtemp()

        info_dict = {
            'name': 'Test Name',
            'organization_name': 'Test Organization',
            'project_name': 'Test Project',
            'release': 'Test Release',
            'cell_line': 'Test Cell Line',
            'treatment': 'Test Treatment',
            'author': 'Test Author',
            'gene_set': 'Test Gene Set'
        }

        file_name = "dataset_info.json"

        try:
            tool = BaseCommandLineTool()
            tool.save_dataset_info_to_json(temp_dir, info_dict, file_name)
            expected_file_path = os.path.join(temp_dir, file_name)
            self.assertTrue(os.path.exists(expected_file_path))
            with open(expected_file_path, 'r') as file:
                content = file.read()
                content_dict = json.loads(content)
                self.assertEqual(content_dict, info_dict)
        finally:
            shutil.rmtree(temp_dir)
