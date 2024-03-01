import shutil
import unittest
from unittest.mock import MagicMock, patch
import os
from datetime import date
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_utils.tabletool import TableFromROCrates


class TestTableFromROCrates(unittest.TestCase):

    def setUp(self):
        self.outdir = os.path.join(os.getcwd(), 'tests/data/temp_dir/')
        self.theargs = MagicMock(outdir=self.outdir,
                                 rocrates=[os.path.join(os.getcwd(), 'tests/data/ro-crate-metadata.json')],
                                 date=date.today().strftime('%Y-%m-%d'),
                                 release='1.0',
                                 downloadurlprefix='https://example.com/data/')
        self.provenance_utils = ProvenanceUtil()
        self.table_from_rocrates = TableFromROCrates(theargs=self.theargs, provenance_utils=self.provenance_utils)
        self.rocrate_dict = {
            '@graph': [
                {'name': 'cellmaps_utils', 'url': 'https://example.com/software/cellmaps_utils', 'metadataType': 'EVI#Software'},
                {'name': 'Computation X', 'metadataType': 'EVI#Computation'},
                {'name': 'Output Dataset', 'url': 'https://example.com/dataset/output', 'metadataType': 'EVI#Dataset'}
            ]
        }

    def tearDown(self):
        if os.path.exists(self.outdir):
            shutil.rmtree(self.outdir)

    def test_run(self):
        self.assertEqual(self.table_from_rocrates.run(), 0)
        files = os.listdir(self.outdir)
        self.assertEqual(len(files), 1)

    def test_get_rocrate_type(self):
        self.assertEqual(self.table_from_rocrates._get_rocrate_type('IF images'), TableFromROCrates.DATA_ROCRATE)
        self.assertEqual(self.table_from_rocrates._get_rocrate_type('Hierarchy'), TableFromROCrates.MODEL_ROCRATE)
        self.assertEqual(self.table_from_rocrates._get_rocrate_type('Other'), TableFromROCrates.INTERMEDIATE_ROCRATE)

    def test_get_cell_line(self):
        self.assertEqual(self.table_from_rocrates._get_cell_line(['MDA-MB-468']), 'MDA-MB-468')
        self.assertEqual(self.table_from_rocrates._get_cell_line(['Other']), 'Unknown')

    def test_get_treatment(self):
        self.assertEqual(self.table_from_rocrates._get_treatment(['untreated', 'vorinostat']), 'untreated,vorinostat')
        self.assertEqual(self.table_from_rocrates._get_treatment(['paclitaxel']), 'paclitaxel')
        self.assertEqual(self.table_from_rocrates._get_treatment(['unknown']), '')

    def test_get_geneset(self):
        self.assertEqual(self.table_from_rocrates._get_geneset(['chromatin', 'metabolic']), 'chromatin,metabolic')
        self.assertEqual(self.table_from_rocrates._get_geneset(['other']), 'Unknown')

    @patch('os.path.isfile')
    @patch('os.path.getsize')
    def test_get_rocrate_size(self, mock_getsize, mock_isfile):
        mock_isfile.return_value = True
        mock_getsize.return_value = 1048576
        self.assertEqual(self.table_from_rocrates._get_rocrate_size('path/to/rocrate'), '1')

    def test_get_rocrate_download_link(self):
        self.assertEqual(self.table_from_rocrates._get_rocrate_download_link('file.tar.gz'), 'https://example.com/data/file.tar.gz')

    def test_get_software_url(self):
        self.assertEqual(self.table_from_rocrates._get_software_url(self.rocrate_dict), 'cellmaps_utils')

    def test_get_next_software_from_rocrate_dict(self):
        software_generator = self.table_from_rocrates._get_next_software_from_rocrate_dict(self.rocrate_dict)
        software = next(software_generator)
        self.assertEqual(software['name'], 'cellmaps_utils')

    def test_get_next_computation_from_rocrate_dict(self):
        computation_generator = self.table_from_rocrates._get_next_computation_from_rocrate_dict(self.rocrate_dict)
        computation = next(computation_generator)
        self.assertEqual(computation['name'], 'Computation X')

    def test_get_computation_name(self):
        self.assertEqual(self.table_from_rocrates._get_computation_name(self.rocrate_dict), 'Computation X')

    def test_get_next_output_dataset_url(self):
        dataset_url_generator = self.table_from_rocrates._get_next_output_dataset_url(self.rocrate_dict)
        dataset_url = next(dataset_url_generator)
        self.assertEqual(dataset_url, 'https://example.com/dataset/output')

    def test_get_output_dataset_url(self):
        self.assertEqual(self.table_from_rocrates._get_output_dataset_url(self.rocrate_dict), 'https://example.com/dataset/output')


if __name__ == '__main__':
    unittest.main()
