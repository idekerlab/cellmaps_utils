#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Integration Tests for `cellmaps_utils` package."""

import os

import unittest
from cellmaps_utils import cellmaps_utilscmd

SKIP_REASON = 'CELLMAPS_UTILS_INTEGRATION_TEST ' \
              'environment variable not set, cannot run integration ' \
              'tests'

@unittest.skipUnless(os.getenv('CELLMAPS_UTILS_INTEGRATION_TEST') is not None, SKIP_REASON)
class TestIntegrationCellmaps_utils(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_something(self):
        """Tests parse arguments"""
        self.assertEqual(1, 1)
