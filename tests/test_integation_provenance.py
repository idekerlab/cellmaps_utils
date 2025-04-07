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
            self.assertTrue(os.path.isfile(os.path.join(rocrate_path,
                                                        'ro-crate-metadata.json')))

            soft_id = provenance_util.register_software(rocrate_path,
                                                        name='my software',
                                                        author='bob smith',
                                                        version='1.0.0',
                                                        file_format='py',
                                                        url='https://foo.com',
                                                        keywords=['key1', 'key2'])

            self.assertIsNotNone(soft_id)

            i_data = os.path.join(temp_dir, 'input.txt')
            open(i_data, 'a').close()
            i_dset_id = provenance_util.register_dataset(rocrate_path,
                                                         data_dict={'name': 'Input Dataset',
                                                                    'author': 'Test i Author',
                                                                    'version': '2.0',
                                                                    'date-published': '2023-11-20',
                                                                    'description': 'Test input description',
                                                                    'data-format': 'text'},
                                                         source_file=i_data,
                                                         skip_copy=False)

            dataset_path = os.path.join(rocrate_path, "dataset.txt")
            with open(dataset_path, 'w') as f:
                f.write("sample data")
            dset_id = provenance_util.register_dataset(rocrate_path,
                                                       data_dict={'name': 'Test Dataset',
                                                                  'author': 'Test Author',
                                                                  'version': '1.0',
                                                                  'date-published': '2023-11-20',
                                                                  'description': 'Test dataset description',
                                                                  'data-format': 'text'},
                                                       skip_copy=True,
                                                       source_file=dataset_path)

            self.assertIsNotNone(dset_id)
            register_computation_result = provenance_util.register_computation(rocrate_path,
                                                                               name='Test Computation',
                                                                               used_software=[soft_id],
                                                                               used_dataset=[i_dset_id],
                                                                               generated=[dset_id],
                                                                               keywords=['c1'])
            self.assertIsNotNone(register_computation_result)

            software_found = False
            inputdataset_found = False
            outputdataset_found = False
            computation_found = False
            rocrate_dict = provenance_util.get_rocrate_as_dict(rocrate_path)
            for entry in rocrate_dict['@graph']:
                entrykey = None
                if 'metadataType' in entry:
                    entrykey = 'metadataType'
                if '@type' in entry:
                    entrykey = '@type'
                if entrykey is None:
                    continue
                if 'Software' in entry[entrykey]:
                    self.assertEqual('my software', entry['name'])
                    self.assertEqual('https://foo.com', entry['url'])
                    self.assertEqual('bob smith', entry['author'])
                    self.assertEqual('Must be at least 10 characters', entry['description'])
                    self.assertEqual('1.0.0', entry['version'])
                    software_found = True
                if 'Dataset' in entry[entrykey] and entry['name'] == 'Input Dataset':
                    self.assertEqual('Test input description', entry['description'])
                    self.assertEqual('Test i Author', entry['author'])
                    inputdataset_found = True
                if 'Dataset' in entry[entrykey] and entry['name'] == 'Test Dataset':
                    self.assertEqual('Test dataset description', entry['description'])
                    self.assertEqual('Test Author', entry['author'])
                    outputdataset_found = True
                if 'Computation' in entry[entrykey]:
                    self.assertEqual('Test Computation', entry['name'])
                    self.assertEqual('Must be at least 10 characters', entry['description'])
                    self.assertEqual([soft_id], entry['usedSoftware'])
                    self.assertEqual([i_dset_id], entry['usedDataset'])
                    self.assertEqual([dset_id], entry['generated'])
                    computation_found = True

            self.assertTrue(computation_found)
            self.assertTrue(software_found)
            self.assertTrue(inputdataset_found)
            self.assertTrue(outputdataset_found)
        finally:
            shutil.rmtree(temp_dir)

    def test_rocrate_lifecycle_with_bulk_dataset(self):
        """Test the lifecycle of RO-Crate operations in `cellmaps_utils`."""
        temp_dir = tempfile.mkdtemp()
        try:
            provenance_util = ProvenanceUtil(raise_on_error=True)

            rocrate_path = os.path.join(temp_dir, "test_rocrate")
            os.mkdir(rocrate_path)
            provenance_util.register_rocrate(rocrate_path, name='Test Crate')
            self.assertTrue(os.path.isfile(os.path.join(rocrate_path,
                                                        'ro-crate-metadata.json')))

            soft_id = provenance_util.register_software(rocrate_path,
                                                        name='my software',
                                                        author='bob smith',
                                                        version='1.0.0',
                                                        file_format='py',
                                                        url='https://foo.com',
                                                        keywords=['key1', 'key2'])

            self.assertIsNotNone(soft_id)

            i_data = os.path.join(rocrate_path, 'input.txt')
            open(i_data, 'a').close()
            bulkdataset = []
            bulkdataset.append({'name': 'Input Dataset',
                                'author': 'Test i Author',
                                'version': '2.0',
                                'date-published': '2023-11-20',
                                'description': 'Test input description',
                                'data-format': 'text',
                                'source_file': i_data})

            dataset_path = os.path.join(rocrate_path, "dataset.txt")
            with open(dataset_path, 'w') as f:
                f.write("sample data")
            bulkdataset.append({'name': 'Input Dataset 2',
                                'author': 'Test Author',
                                'version': '1.0',
                                'date-published': '2023-11-20',
                                'description': 'Test input description 2',
                                'data-format': 'text',
                                'source_file': dataset_path})

            gen_dset = provenance_util.register_datasets_in_bulk(rocrate_path=rocrate_path,
                                                                 datasets=bulkdataset)

            register_computation_result = provenance_util.register_computation(rocrate_path,
                                                                               name='Test Computation',
                                                                               used_software=[soft_id],
                                                                               used_dataset=[],
                                                                               generated=gen_dset,
                                                                               keywords=['c1'])
            self.assertIsNotNone(register_computation_result)

            software_found = False
            inputdataset_found = False
            outputdataset_found = False
            computation_found = False
            rocrate_dict = provenance_util.get_rocrate_as_dict(rocrate_path)
            for entry in rocrate_dict['@graph']:
                entrykey = None
                if 'metadataType' in entry:
                    entrykey = 'metadataType'
                if '@type' in entry:
                    entrykey = '@type'
                if entrykey is None:
                    continue
                if 'Software' in entry[entrykey]:
                    self.assertEqual('my software', entry['name'])
                    self.assertEqual('https://foo.com', entry['url'])
                    self.assertEqual('bob smith', entry['author'])
                    self.assertEqual('Must be at least 10 characters', entry['description'])
                    self.assertEqual('1.0.0', entry['version'])
                    software_found = True
                if 'Dataset' in entry[entrykey] and entry['name'] == 'Input Dataset':
                    self.assertEqual('Test input description', entry['description'])
                    self.assertEqual('Test i Author', entry['author'])
                    inputdataset_found = True
                if 'Dataset' in entry[entrykey] and entry['name'] == 'Input Dataset 2':
                    self.assertEqual('Test input description 2', entry['description'])
                    self.assertEqual('Test Author', entry['author'])
                    outputdataset_found = True
                if 'Computation' in entry[entrykey]:
                    self.assertEqual('Test Computation', entry['name'])
                    self.assertEqual('Must be at least 10 characters', entry['description'])
                    self.assertEqual([soft_id], entry['usedSoftware'])
                    self.assertEqual([], entry['usedDataset'])
                    self.assertEqual(gen_dset, entry['generated'])
                    computation_found = True

            self.assertTrue(computation_found)
            self.assertTrue(software_found)
            self.assertTrue(inputdataset_found)
            self.assertTrue(outputdataset_found)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
