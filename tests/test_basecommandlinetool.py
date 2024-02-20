#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `BaseCommandLineTool`."""

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
