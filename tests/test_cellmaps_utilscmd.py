#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_utils` package."""

import os
import tempfile
import shutil

import unittest
from cellmaps_utils import cellmaps_utilscmd


class TestCellmaps_utils(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_parse_arguments(self):
        """Tests parse arguments"""
        res = cellmaps_utilscmd._parse_arguments('hi', [])

        self.assertEqual(res.verbose, 0)
        self.assertEqual(res.exitcode, 0)
        self.assertEqual(res.logconf, None)

        someargs = ['-vv', '--logconf', 'hi', '--exitcode', '3']
        res = cellmaps_utilscmd._parse_arguments('hi', someargs)

        self.assertEqual(res.verbose, 2)
        self.assertEqual(res.logconf, 'hi')
        self.assertEqual(res.exitcode, 3)

    def test_main(self):
        """Tests main function"""

        # try where loading config is successful
        try:
            temp_dir = tempfile.mkdtemp()
            res = cellmaps_utilscmd.main(['myprog.py'])
            self.assertEqual(res, 0)
        finally:
            shutil.rmtree(temp_dir)
