import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import uuid
import cellmaps_utils
from cellmaps_utils.c2m2tool import C2M2Creator
from cellmaps_utils.exceptions import CellMapsError


class TestC2M2Creator(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        temp_outdir = tempfile.mkdtemp()
        try:
            mock_args = MagicMock(outdir=temp_outdir)
            creator = C2M2Creator(mock_args)
            self.assertIsNotNone(creator)
        finally:
            shutil.rmtree(temp_outdir)

if __name__ == '__main__':
    unittest.main()
