#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_utils` package."""


import unittest
from cellmaps_utils.runner import CellmapsutilsRunner


class TestCellmapsutilsrunner(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_constructor(self):
        """Tests constructor"""
        myobj = CellmapsutilsRunner(0)

        self.assertIsNotNone(myobj)

    def test_run(self):
        """ Tests run()"""
        myobj = CellmapsutilsRunner(4)
        self.assertEqual(4, myobj.run())
