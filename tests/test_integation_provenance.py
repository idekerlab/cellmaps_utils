#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Integration Tests for `cellmaps_utils` package."""

import os
import sys
import unittest
import tempfile
import shutil
from cellmaps_utils.provenance import ProvenanceUtil

SKIP_REASON = 'CELLMAPS_UTILS_INTEGRATION_TEST ' \
              'environment variable not set, cannot run integration ' \
              'tests'


@unittest.skipUnless(os.getenv('CELLMAPS_UTILS_INTEGRATION_TEST') is not None, SKIP_REASON)
class TestIntegrationCellmapsUtils(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_rocrate_lifecycle(self):
        """Test the lifecycle of RO-Crate operations in `cellmaps_utils`."""
        temp_dir = tempfile.mkdtemp()
        try:
            provenance_util = ProvenanceUtil(raise_on_error=True)

            rocrate_path = os.path.join(temp_dir, "test_rocrate")
            os.mkdir(rocrate_path)
            provenance_util.register_rocrate(rocrate_path, name='Test Crate')
            self.assertTrue(os.path.isfile(os.path.join(rocrate_path, 'ro-crate-metadata.json')))

            dataset_path = os.path.join(rocrate_path, "dataset.txt")
            with open(dataset_path, 'w') as f:
                f.write("sample data")
            provenance_util.register_dataset(rocrate_path, data_dict={
                'name': 'Test Dataset',
                'author': 'Test Author',
                'version': '1.0',
                'date-published': '2023-11-20',
                'description': 'Test dataset description',
                'data-format': 'text'
            }, source_file=dataset_path)

            register_computation_result = provenance_util.register_computation(rocrate_path, name='Test Computation')
            self.assertIsNotNone(register_computation_result)

        finally:
            sys.stdout.write('Removing temp directory: ' + str(temp_dir))
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
