import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call
import pandas as pd

from cellmaps_utils.apmstool import APMSDataLoader


class TestAPMSDataLoader(unittest.TestCase):

    def setUp(self):
        self.mock_args = MagicMock(outdir='/fakepath', inputs=['fake_input1.tsv', 'fake_input2.tsv'],
                                   name='Test Name', organization_name='Test Org', project_name='Test Project',
                                   release='1.0', cell_line='Test Line', treatment='Test Treatment',
                                   author='Test Author', gene_set='Test Set')
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


if __name__ == '__main__':
    unittest.main()
