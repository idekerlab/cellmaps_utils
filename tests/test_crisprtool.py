import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import uuid
import cellmaps_utils
from cellmaps_utils.crisprtool import CRISPRDataLoader
from cellmaps_utils.crisprtool import CellMapsError


class TestCRISPRDataLoader(unittest.TestCase):

    def setUp(self):
        self.temp_outdir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_outdir, 'run')
        h5adfile = os.path.join(self.temp_outdir, 'fake.h5ad')
        open(h5adfile, 'a').close()
        self.mock_args = MagicMock(outdir=self.output_dir,
                                   organization_name='Test Org',
                                   project_name='Test Project',
                                   release='1.0',
                                   cell_line='Test Line',
                                   treatment='Test Treatment',
                                   tissue='breast; mammary gland',
                                   author='Test Author',
                                   h5ad=h5adfile,
                                   gene_set='Test Set',
                                   feature='Test Feature',
                                   expression=['Test Expression'],
                                   guiderna=['Test GuideRNA'],
                                   dataset='1channel',
                                   skipcopy=False,
                                   num_perturb_guides='1',
                                   num_non_target_ctrls='2',
                                   num_screen_targets='3')
        self.mock_args.name = MagicMock(return_value='Test Name')
        self.loader = CRISPRDataLoader(self.mock_args)

    def tearDown(self):
        shutil.rmtree(self.temp_outdir)

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

        self.loader._dataset = 'uh'
        self.assertEqual(self.loader._get_dataset_description(), '')

    @patch('cellmaps_utils.crisprtool.CRISPRDataLoader._link_or_copy')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_dataset')
    def test_link_and_register_guiderna(self, mock_register_dataset, mock_link_or_copy):
        mock_register_dataset.return_value = 'mock_dataset_id'
        dset_ids = self.loader._link_and_register_h5ad(description='Test Description', keywords=['test'])
        self.assertTrue(len(dset_ids) > 0)
        mock_link_or_copy.assert_called()
        mock_register_dataset.assert_called()

    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_dataset')
    def test_link_and_register_h5ad(self, mock_register_dataset):
        # since the run() method makes the output directory we
        # need to do it ourselves
        os.makedirs(self.loader._outdir, mode=0o755)

        mock_register_dataset.return_value = 'mock_dataset_id'
        self.loader._skipcopy = True
        dset_ids = self.loader._link_and_register_h5ad(description='Test Description', keywords=['test'])
        self.assertTrue(len(dset_ids) > 0)
        mock_register_dataset.assert_called()

    def test_generate_rocrate_dir_path(self):
        self.loader._generate_rocrate_dir_path()
        expected_dir_name = f"{self.mock_args.project_name.lower()}_" \
            f"{self.mock_args.gene_set.lower()}_{self.mock_args.cell_line.lower()}" \
            f"_breast__mammary_gland_{self.mock_args.treatment.lower()}_crispr_" \
            f"{self.mock_args.dataset.lower()}_" \
            f"{self.mock_args.release.lower()}".replace(' ', '_')
        self.assertTrue(self.loader._outdir.endswith(expected_dir_name))

    @patch('cellmaps_utils.crisprtool.CRISPRDataLoader._link_or_copy')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_dataset')
    def test_link_and_register_expression(self, mock_register_dataset, mock_link_or_copy):
        mock_register_dataset.return_value = 'mock_dataset_id'
        dset_ids = self.loader._link_and_register_h5ad(description='Test Description', keywords=['test'])
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

    @patch('os.link', side_effect=OSError('problem'))
    @patch('shutil.copy')
    def test_link_or_copy(self, mock_copy, mock_link):
        temp_dir = tempfile.mkdtemp()
        try:
            src = self.mock_args.feature
            dest = os.path.join(temp_dir, 'copied_feature.csv')
            self.loader._link_or_copy(src, dest)
            mock_link.assert_called_with(src, dest)
            mock_copy.assert_called()
        finally:
            shutil.rmtree(temp_dir)

    def test_create_token_replacement_map(self):
        token_map = self.loader._create_token_replacement_map()
        self.assertTrue('@@H5AD@@' in token_map)

    def test_copy_over_crispr_readme(self):
        # since the run() method makes the output directory we
        # need to do it ourselves
        os.makedirs(self.loader._outdir, mode=0o755)

        self.loader._copy_over_crispr_readme()
        self.assertTrue(os.path.exists(os.path.join(self.loader._outdir,
                                                    'readme.txt')))

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

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_login', return_value='smith')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_computation')
    def test_register_computation(self, mock_register_computation, mock_login):
        self.loader._softwareid = 'softid'
        self.loader._input_data_dict = {'hi': 'there'}
        self.loader._get_fairscape_id = MagicMock(return_value='someid')
        self.loader._register_computation(description='Test Description', keywords=['test'],
                                          generated_dataset_ids=['1'])

        mock_register_computation.assert_called_with(self.loader._outdir,
                                                     name='CRISPR',
                                                     run_by='smith',
                                                     command=str(self.loader._input_data_dict),
                                                     description='Test Description run of cellmaps_utils',
                                                     keywords=['test', 'computation'],
                                                     used_software=[self.loader._softwareid],
                                                     generated=['1'],
                                                     guid='someid')

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_login', return_value='smith')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_software', return_value='12345')
    def test_register_software(self, mock_register_software, mock_login):
        self.loader._get_fairscape_id = MagicMock(return_value='someid')
        self.loader._register_software(description='desc', keywords=['x'])
        self.assertEqual('12345', self.loader._softwareid)
        mock_register_software.assert_called_with(self.loader._outdir,
                                                  name=cellmaps_utils.__name__,
                                                  description='desc ' + cellmaps_utils.__description__,
                                                  author=cellmaps_utils.__author__,
                                                  version=cellmaps_utils.__version__,
                                                  file_format='py',
                                                  keywords=['x', 'tools', cellmaps_utils.__name__],
                                                  url=cellmaps_utils.__repo_url__,
                                                  guid='someid')

    def test_add_subparser(self):
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_parser.add_argument = MagicMock()
        mock_subparsers.add_parser = MagicMock(return_value=mock_parser)
        CRISPRDataLoader.add_subparser(mock_subparsers)
        mock_subparsers.add_parser.assert_called_with('crisprconverter',
                                                      help='Loads CRISPR data into a RO-Crate',
                                                      description='\n\n        Version 0.4.0a1\n\n'
                                                                  '        crisprconverter Loads '
                                                                  'CRISPR data into a RO-Crate by '
                                                                  'creating a \n        directory, '
                                                                  'copying over relevant and using '
                                                                  'FAIRSCAPE CLI to \n        '
                                                                  'register the data files in '
                                                                  'the directory known as an '
                                                                  'RO-Crate\n\n        ',
                                                      formatter_class=cellmaps_utils.constants.ArgParseFormatter)
        mock_parser.add_argument.assert_called()

    def test_run(self):
        # not sure why but magicmock is not doing the right thing
        # with name for mock_args
        self.loader._name = 'Test Name'

        self.assertEqual(0, self.loader.run())
        self.assertTrue(os.path.exists(os.path.join(self.loader._outdir,
                                                    'readme.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.loader._outdir,
                                                    'perturbation.h5ad')))


if __name__ == '__main__':
    unittest.main()
