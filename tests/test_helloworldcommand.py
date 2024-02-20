#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `HelloWorldCommand`."""

import os
import argparse
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.basecmdtool import HelloWorldCommand


class TestHelloWorldCommand(unittest.TestCase):
    """Tests for `HelloWorldCommand`"""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_run(self):

        cmdtool = HelloWorldCommand(MagicMock())
        self.assertEqual(0, cmdtool.run())

    def test_add_subparser(self):
        subparsers = MagicMock()
        subparsers.add_parser(return_value=True)
        self.assertTrue(HelloWorldCommand.add_subparser(subparsers))

