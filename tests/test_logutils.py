#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_utils.cellmaps_io` package."""

import os
import argparse
import shutil
import tempfile
import unittest

from cellmaps_utils import logutils


class TestCellmapsIO(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_setup_logging(self):
        """ Tests logging setup"""
        try:
            logutils.setup_cmd_logging(None)
            self.fail('Expected AttributeError')
        except AttributeError:
            pass

        # args.logconf is None
        p = argparse.Namespace()
        p.logconf = None
        p.verbose = 0
        logutils.setup_cmd_logging(p)

        # args.logconf set to a file
        try:
            temp_dir = tempfile.mkdtemp()

            logfile = os.path.join(temp_dir, 'log.conf')
            with open(logfile, 'w') as f:
                f.write("""[loggers]
keys=root

[handlers]
keys=stream_handler

[formatters]
keys=formatter

[logger_root]
level=DEBUG
handlers=stream_handler

[handler_stream_handler]
class=StreamHandler
level=DEBUG
formatter=formatter
args=(sys.stderr,)

[formatter_formatter]
format=%(asctime)s %(name)-12s %(levelname)-8s %(message)s""")

            p = argparse.Namespace()
            p.logconf = logfile
            p.verbose = 0

            logutils.setup_cmd_logging(p)

        finally:
            shutil.rmtree(temp_dir)
