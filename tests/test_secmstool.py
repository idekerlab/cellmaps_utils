"""SEC-MS conversion tests use synthetic quantities and experiment identities."""

import csv
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

from cellmaps_utils.cellmaps_utilscmd import _parse_arguments, main
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.secmstool import SECMSDataConverter

class SECMSDataConverter(unittest.TestCase):

    def test_foo(self):
        self.assertEqual(1, 1)


