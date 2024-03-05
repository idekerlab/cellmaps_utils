import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import uuid
from cellmaps_utils.crisprtool import CRISPRDataLoader
from cellmaps_utils.crisprtool import CellMapsError


class TestCRISPRDataLoader(unittest.TestCase):

    def setUp(self):
        self.temp_outdir = tempfile.mkdtemp()
        self.mock_args = MagicMock(outdir=self.temp_outdir,
                                   name='Test Name',
                                   organization_name='Test Org',
                                   project_name='Test Project',
                                   release='1.0',
                                   cell_line='Test Line',
                                   treatment='Test Treatment',
                                   author='Test Author',
                                   gene_set='Test Set',
                                   feature='Test Feature',
                                   expression=['Test Expression'],
                                   guiderna=['Test GuideRNA'],
                                   dataset='1channel',
                                   skipcopy=False)
        self.loader = CRISPRDataLoader(self.mock_args)

    def tearDown(self):
        shutil.rmtree(self.mock_args.outdir)

    @patch('os.path.exists', return_value=True)
    def test_run_directory_exists(self, mock_exists):
        with self.assertRaises(CellMapsError):
            self.loader.run()

    @patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678'))
    def test_get_fairscape_id(self, mock_uuid4):
        expected_id = '12345678-1234-5678-1234-567812345678:' + os.path.basename(self.loader._outdir)
        self.assertEqual(self.loader._get_fairscape_id(), expected_id)

    def test_get_dataset_description(self):
        self.loader._dataset = '1channel'
        self.assertEqual(self.loader._get_dataset_description(),
                         'FASTQs file were obtain by concatenating 3 NGS run over 7 sequencing lanes')
        self.loader._dataset = 'subset'
        self.assertEqual(self.loader._get_dataset_description(), 'Subset run')

    @patch('cellmaps_utils.crisprtool.CRISPRDataLoader._link_or_copy')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_dataset')
    def test_link_and_register_guiderna(self, mock_register_dataset, mock_link_or_copy):
        mock_register_dataset.return_value = 'mock_dataset_id'
        dset_ids = self.loader._link_and_register_guiderna(description='Test Description', keywords=['test'])
        self.assertTrue(len(dset_ids) > 0)
        mock_link_or_copy.assert_called()
        mock_register_dataset.assert_called()

    def test_generate_rocrate_dir_path(self):
        self.loader._generate_rocrate_dir_path()
        expected_dir_name = f"{self.mock_args.project_name.lower()}_{self.mock_args.gene_set.lower()}_{self.mock_args.cell_line.lower()}_{self.mock_args.treatment.lower()}_crispr_{self.mock_args.dataset.lower()}_{self.mock_args.release.lower()}".replace(
            ' ', '_')
        self.assertTrue(self.loader._outdir.endswith(expected_dir_name))

    @patch('cellmaps_utils.crisprtool.CRISPRDataLoader._link_or_copy')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_dataset')
    def test_link_and_register_expression(self, mock_register_dataset, mock_link_or_copy):
        mock_register_dataset.return_value = 'mock_dataset_id'
        dset_ids = self.loader._link_and_register_expression(description='Test Description', keywords=['test'])
        self.assertTrue(len(dset_ids) > 0)
        mock_link_or_copy.assert_called()
        mock_register_dataset.assert_called()

    @patch('os.link')
    @patch('shutil.copy')
    def test_link_or_copy(self, mock_copy, mock_link):
        temp_dir = tempfile.mkdtemp()
        try:
            src = self.mock_args.feature
            dest = os.path.join(temp_dir, 'copied_feature.csv')
            self.loader._link_or_copy(src, dest)
            mock_link.assert_called_with(src, dest)
            mock_copy.assert_not_called()
        finally:
            shutil.rmtree(temp_dir)

    def test_create_token_replacement_map(self):
        token_map = self.loader._create_token_replacement_map()
        self.assertTrue('@@PREFIX@@' in token_map)
        self.assertTrue('@@FEATURE_REF_UNDERLINE@@' in token_map)

    def test_copy_over_crispr_readme(self):
        self.loader._copy_over_crispr_readme()
        self.assertTrue(os.path.exists(os.path.join(self.temp_outdir, 'readme.txt')))

    def test_replace_readme_tokens(self):
        token_map = {
            '@@PREFIX@@': 'TestLine_TestTreatment',
            '@@FEATURE_REF_UNDERLINE@@': '-------------------------'
        }
        test_lines = [
            "This is a test line with @@PREFIX@@.",
            "Underline test @@FEATURE_REF_UNDERLINE@@.",
            "No token here."
        ]
        expected_outcomes = [
            "This is a test line with TestLine_TestTreatment.",
            "Underline test -------------------------.",
            "No token here."
        ]
        for test_line, expected_outcome in zip(test_lines, expected_outcomes):
            self.assertEqual(self.loader._replace_readme_tokens(test_line, tokenmap=token_map), expected_outcome)


if __name__ == '__main__':
    unittest.main()
