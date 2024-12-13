import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call
import pandas as pd

import cellmaps_utils
from cellmaps_utils.apmstool import APMSDataLoader
from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsError


class TestAPMSDataLoader(unittest.TestCase):

    def setUp(self):
        self.mock_args = MagicMock(outdir='/fakepath',
                                   inputs=['fake_input1.tsv',
                                           'fake_input2.tsv'],
                                   name='Test Name',
                                   organization_name='Test Org',
                                   project_name='Test Project',
                                   release='1.0',
                                   cell_line='Test Line',
                                   treatment='Test Treatment',
                                   author='Test Author',
                                   gene_set='Test Set',
                                   set_name=None,
                                   tissue='breast; mammory gland')
        self.loader = APMSDataLoader(self.mock_args)

    def test_initialization(self):
        self.assertEqual(self.loader._outdir, os.path.abspath('/fakepath'))
        self.assertEqual(self.loader._inputs, ['fake_input1.tsv', 'fake_input2.tsv'])

    @patch('uuid.uuid4', return_value='123456')
    def test_get_fairscape_id(self, mock_uuid4):
        expected_id = '123456:fakepath'
        result = self.loader._get_fairscape_id()
        self.assertEqual(result, expected_id)

    def test_generate_rocrate_dir_path(self):
        self.loader._generate_rocrate_dir_path()
        expected_dir_name = os.path.join('/fakepath',
                                         'test_project_test_set_test_line_test_treatment_apms_1.0').lower().replace(' ',
                                                                                                                    '_')
        self.assertEqual(self.loader._outdir, expected_dir_name)

    @patch('shutil.copy')
    @patch('os.path.dirname', return_value='/fake/dir')
    @patch('os.path.join', side_effect=lambda *args: '/'.join(args))
    def test_copy_over_apms_readme(self, mock_join, mock_dirname, mock_copy):
        self.loader._outdir = '/fakepath/test_dir'
        self.loader._copy_over_apms_readme()

        expected_source_path = '/fake/dir/apms_readme.txt'
        expected_destination_path = '/fakepath/test_dir/readme.txt'

        expected_join_calls = [
            call(os.path.dirname(__file__), 'apms_readme.txt'),
            call(self.loader._outdir, 'readme.txt')
        ]
        mock_join.assert_has_calls(expected_join_calls, any_order=True)
        mock_copy.assert_called_once_with(expected_source_path, expected_destination_path)

    @patch('pandas.read_csv')
    def test_merge_and_save_apms_data(self, mock_read_csv):
        df1 = pd.DataFrame({'Gene': ['A', 'B'], 'Value': [1, 2]})
        df2 = pd.DataFrame({'Gene': ['C', 'D'], 'Value': [3, 4]})
        mock_read_csv.side_effect = [df1, df2]

        temp_dir = tempfile.mkdtemp()
        try:
            self.loader._inputs = ['fake_input1.tsv', 'fake_input2.tsv']
            self.loader._outdir = temp_dir

            apms_path = self.loader._merge_and_save_apms_data()
            expected_path = os.path.join(self.loader._outdir, 'apms.tsv')
            self.assertEqual(apms_path, expected_path)
            self.assertTrue(os.path.exists(apms_path))
            self.assertTrue(os.path.getsize(apms_path) > 0)
        finally:
            shutil.rmtree(temp_dir)

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_login', return_value='smith')
    @patch('cellmaps_utils.provenance.ProvenanceUtil.register_computation')
    def test_register_computation(self, mock_register_computation, mock_login):
        self.loader._softwareid = 'softid'
        self.loader._input_data_dict = {'hi': 'there'}
        self.loader._get_fairscape_id = MagicMock(return_value='someid')
        self.loader._register_computation(description='Test Description', keywords=['test'],
                                          generated_dataset_ids=['1'])

        mock_register_computation.assert_called_with(self.loader._outdir,
                                                     name='AP-MS',
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

    def test_merge_and_save_apms_data(self):
        temp_dir = tempfile.mkdtemp()
        try:
            first_tsv = os.path.join(temp_dir, 'first.tsv')
            second_tsv = os.path.join(temp_dir, 'second.tsv')

            df = pd.DataFrame({'NumReplicates': [1], 'NumReplicates.x': [3]})
            df.to_csv(first_tsv, sep='\t', index=False)

            df = pd.DataFrame({'NumReplicates.x': [4]})
            df.to_csv(second_tsv, sep='\t', index=False)

            self.loader._inputs = [first_tsv, second_tsv]
            self.loader._outdir = temp_dir
            apms_path = os.path.join(temp_dir, constants.APMS_TSV_FILE)
            self.assertEqual(apms_path, self.loader._merge_and_save_apms_data())
            df = pd.read_csv(apms_path, sep='\t')
            self.assertEqual([1, 4], list(df['NumReplicates.x']))
        finally:
            shutil.rmtree(temp_dir)

    def test_run_outdir_already_exists(self):
        temp_dir = tempfile.mkdtemp()
        try:
            self.loader._name = 'Test Name'
            self.loader._outdir = temp_dir

            # get new rocrate dir
            # create the directory to cause the next part to fail
            self.loader._generate_rocrate_dir_path()
            os.makedirs(self.loader._outdir, mode=0o755)
            # put _outdir back to temp_dir
            # maybe we shouldnt do this cause
            # outdir changes values...
            self.loader._outdir = temp_dir

            self.loader.run()
            self.fail('Expected exception')
        except CellMapsError as ce:
            self.assertTrue(' already exists' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_run(self):
        temp_dir = tempfile.mkdtemp()
        try:
            input_tsv = os.path.join(temp_dir, 'input.tsv')
            df = pd.DataFrame({'NumReplicates': [1], 'NumReplicates.x': [3]})
            df.to_csv(input_tsv, sep='\t', index=False)
            out_dir = os.path.join(temp_dir, 'run')
            self.mock_args = MagicMock(outdir=out_dir,
                                       inputs=[input_tsv],
                                       name='Test Name',
                                       organization_name='Test Org',
                                       project_name='Test Project',
                                       release='1.0',
                                       cell_line='Test Line',
                                       treatment='Test Treatment',
                                       author='Test Author',
                                       gene_set='Test Set',
                                       set_name=None,
                                       tissue='breast; mammory gland')
            self.loader = APMSDataLoader(self.mock_args)
            # not sure why but magicmock is not doing the right thing
            # with name for mock_args
            self.loader._name = 'Test Name'

            self.assertEqual(0, self.loader.run())
            self.assertTrue(os.path.exists(os.path.join(self.loader._outdir,
                                                        'readme.txt')))
            apms_path = os.path.join(self.loader._outdir,
                                     constants.APMS_TSV_FILE)
            self.assertTrue(os.path.exists(apms_path))
            df = pd.read_csv(apms_path, sep='\t')
            self.assertEqual([1], list(df['NumReplicates.x']))
        finally:
            shutil.rmtree(temp_dir)

    def test_add_subparser(self):
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_parser.add_argument = MagicMock()
        mock_subparsers.add_parser = MagicMock(return_value=mock_parser)
        APMSDataLoader.add_subparser(mock_subparsers)
        mock_subparsers.add_parser.assert_called_with('apmsconverter',
                                                      help='Loads AP-MS data into a RO-Crate',
                                                      description='\n\n        '
                                                                  'Version ' + str(cellmaps_utils.__version__) +
                                                                  '\n\n        '
                                                                  'apmsconverter Loads AP-MS '
                                                                  'data into a RO-Crate\n        ',
                                                      formatter_class=cellmaps_utils.constants.ArgParseFormatter)
        mock_parser.add_argument.assert_called()


if __name__ == '__main__':
    unittest.main()
