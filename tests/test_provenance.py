#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_utils.cellmaps_io` package."""

import os
import subprocess
import sys
import shutil
import tempfile
import json
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_utils.exceptions import CellMapsProvenanceError


class TestProvenanceUtil(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""
        log_provenance_file = os.path.join(os.getcwd(), 'provenance_errors.json')
        if os.path.exists(log_provenance_file):
            os.remove(log_provenance_file)

    def test_run_cmd_timeout(self):
        temp_dir = tempfile.mkdtemp()
        try:
            py_file = os.path.join(temp_dir, 'sleep.py')
            with open(py_file, 'w') as f:
                f.write('import time\r\n')
                f.write('time.sleep(60)\r\n')
            p = ProvenanceUtil(raise_on_error=True)
            p._run_cmd([sys.executable, py_file], timeout=1)
        except CellMapsProvenanceError as ce:
            self.assertTrue('Process timed out' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_keywords(self):
        prov = ProvenanceUtil(raise_on_error=True)
        self.assertEqual(['--keywords', ''], prov._get_keywords(keywords=''))
        self.assertEqual([], prov._get_keywords(keywords=[]))
        self.assertEqual(['--keywords', 'a', '--keywords', 3],
                         prov._get_keywords(keywords=['a', 3]))
        try:
            prov._get_keywords(keywords=1.0)
            self.fail('Expected exception')
        except CellMapsProvenanceError as ce:
            self.assertTrue('Keywords must' in str(ce))

    def test_example_dataset_provenance(self):

        # default
        example = ProvenanceUtil.example_dataset_provenance()
        self.assertEqual({'name': 'Name of dataset',
                          'author': 'Author of dataset',
                          'version': 'Version of dataset',
                          'date-published': 'Date dataset was published',
                          'description': 'Description of dataset',
                          'data-format': 'Format of data'}, example)

        # with ids
        example = ProvenanceUtil.example_dataset_provenance(with_ids=True)
        self.assertEqual({'guid': 'ID of dataset'}, example)

        # with required only False
        example = ProvenanceUtil.example_dataset_provenance(requiredonly=False)
        expected_full = {'name': 'Name of dataset',
                         'author': 'Author of dataset',
                         'version': 'Version of dataset',
                         'date-published': 'Date dataset was published',
                         'description': 'Description of dataset',
                         'data-format': 'Format of data',
                         'url': 'URL of datset', 'used-by': '?',
                         'derived-from': '?', 'associated-publication': '?',
                         'additional-documentation': '?'}
        self.assertEqual(expected_full, example)

        # with required only None
        example = ProvenanceUtil.example_dataset_provenance(requiredonly=None)
        self.assertEqual(expected_full, example)

    def test_get_login(self):
        prov = ProvenanceUtil(raise_on_error=True)
        res = prov.get_login()
        self.assertTrue(res is not None)

        orig_logname = None
        if 'LOGNAME' in os.environ:
            orig_logname = os.environ['LOGNAME']
        try:
            # set LOGNAME to different value
            os.environ['LOGNAME'] = 'smith'

            # check we get it back and then reset it
            self.assertEqual('smith', prov.get_login())
        finally:
            if orig_logname is not None:
                os.environ['LOGNAME'] = orig_logname

    def test_get_rocrate_as_dict_none_for_path(self):
        prov = ProvenanceUtil()
        try:
            prov.get_rocrate_as_dict(None)
        except CellMapsProvenanceError as ce:
            self.assertEqual('rocrate_path is None', str(ce))

    def test_get_rocrate_as_dict_no_metadata_file(self):
        prov = ProvenanceUtil(raise_on_error=False)
        temp_dir = tempfile.mkdtemp()
        try:
            res = prov.get_rocrate_as_dict(temp_dir)
            self.assertEqual({'@id': None, 'name': '', 'description': '',
                              'keywords': [''],
                              'isPartOf': [{"@type": "Organization",
                                            "name": ""},
                                           {"@type": "Project",
                                            "name": ""}]}, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_rocrate_as_dict_invalid_rocrate_metadata(self):
        prov = ProvenanceUtil(raise_on_error=True)
        temp_dir = tempfile.mkdtemp()
        try:
            rocrate = os.path.join(temp_dir, constants.RO_CRATE_METADATA_FILE)
            with open(rocrate, 'w') as f:
                f.write('invalidjsonasdfasdfasdfsa\n')
            prov.get_rocrate_as_dict(rocrate_path=rocrate)
        except CellMapsProvenanceError as ce:
            self.assertTrue('Error parsing' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_register_rocrate(self):
        """
        Registers temp directory as a crate
        with all default values
        :return:
        """
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='some 10 charactert name',
                                  description=' some 10 character desc')
            crate_file = os.path.join(temp_dir, constants.RO_CRATE_METADATA_FILE)
            self.assertTrue(os.path.isfile(crate_file) or
                            os.path.exists(os.path.join(temp_dir, 'provenance_errors.json')))
        finally:
            shutil.rmtree(temp_dir)

    def test_register_rocrate_no_keywords(self):
        """
        Registers temp directory as a crate
        with all default values
        :return:
        """
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil(raise_on_error=True)
            prov.register_rocrate(temp_dir, keywords=None)
            self.fail('Expected exception')
        except CellMapsProvenanceError as ce:
            self.assertTrue('Error creating crate' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_register_rocrate_invalid_path(self):
        """
        Registers temp directory as a crate
        with all default values
        :return:
        """
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil(raise_on_error=True)
            prov.register_rocrate(os.path.join(temp_dir, 'doesnotexist'))
            self.fail('Expected exception')
        except CellMapsProvenanceError as ce:
            self.assertTrue('No such' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_register_computation(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='some 10 charactert name',
                                  description=' some 10 character desc')
            c_id = prov.register_computation(temp_dir, run_by='runby',
                                             name='name', description='desc needs to be 10 characters',
                                             command='cmd')
            self.assertIsNotNone(c_id)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_computation_with_software_datasets(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='some 10 charactert name',
                                  description=' some 10 character desc')

            used_dataset = []
            used_software = []
            generated = []
            for x in range(0, 8000):
                used_dataset.append('ark:/d' + str(x))
                used_software.append('ark:/s' + str(x))
                generated.append('ark:/g' + str(x))

            c_id = prov.register_computation(temp_dir, run_by='runby',
                                             name='name', description='desc must be 10 chars',
                                             command='cmd',
                                             used_dataset=used_dataset,
                                             used_software=used_software,
                                             generated=generated)
            self.assertIsNotNone(c_id)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_software(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            s_id = prov.register_software(temp_dir, name='name',
                                          description='must be 10 characters',

                                          version='0.1.0', file_format='.py',
                                          url='http://foo.com')
            self.assertIsNotNone(s_id)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_software_invalid_rocrate(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil(raise_on_error=True)
            prov.register_rocrate(os.path.join(temp_dir, 'doesnotexist'))
            prov.register_software(temp_dir, name='name',
                                   description='must be 10 characters',
                                   version='0.1.0', file_format='.py',
                                   url='http://foo.com')
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertTrue('Caught Exception' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_register_dataset(self):

        temp_dir = tempfile.mkdtemp()
        try:
            subdir = os.path.join(temp_dir, 'input')
            os.makedirs(subdir, mode=0o755)
            src_file = os.path.join(subdir, 'xx')
            with open(src_file, 'w') as f:
                f.write('hi')

            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='some 10 character name', description='10 character description')
            d_id = prov.register_dataset(temp_dir,
                                         source_file=src_file,
                                         skip_copy=False,
                                         data_dict={'name': 'Name of dataset',
                                                    'author': 'Author of dataset',
                                                    'version': 'Version of dataset',
                                                    'date-published': 'Date dataset was published MM-DD-YYYY',
                                                    'description': 'Description of dataset',
                                                    'data-format': 'Format of data'})
            self.assertIsNotNone(d_id)

        finally:
            shutil.rmtree(temp_dir)

    def test_register_dataset_with_schema(self):
        temp_dir = tempfile.mkdtemp()
        try:
            subdir = os.path.join(temp_dir, 'input')
            os.makedirs(subdir, mode=0o755)
            src_file = os.path.join(subdir, 'xx')
            with open(src_file, 'w') as f:
                f.write('hi')

            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='some 10 character name', description='10 character description')
            d_id = prov.register_dataset(temp_dir,
                                         source_file=src_file,
                                         skip_copy=False,
                                         data_dict={'name': 'Name of dataset',
                                                    'author': 'Author of dataset',
                                                    'version': 'Version of dataset',
                                                    'date-published': 'Date dataset was published MM-DD-YYYY',
                                                    'description': 'Description of dataset',
                                                    'schema': 'https://foo.com',
                                                    'data-format': 'Format of data'})
            self.assertIsNotNone(d_id)

        finally:
            shutil.rmtree(temp_dir)

    def test_register_dataset_with_keywords(self):

        temp_dir = tempfile.mkdtemp()
        try:
            subdir = os.path.join(temp_dir, 'input')
            os.makedirs(subdir, mode=0o755)
            src_file = os.path.join(subdir, 'xx')
            with open(src_file, 'w') as f:
                f.write('hi')

            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir)
            d_id = prov.register_dataset(temp_dir,
                                         source_file=src_file,
                                         skip_copy=False,
                                         data_dict={'name': 'Name of dataset',
                                                    'author': 'Author of dataset',
                                                    'version': 'Version of dataset',
                                                    'date-published': 'Date dataset was published MM-DD-YYYY',
                                                    'description': 'Description of dataset',
                                                    'data-format': 'Format of data',
                                                    'keywords': ['one', 'two x', 'three x']})
            self.assertIsNotNone(d_id)

        finally:
            shutil.rmtree(temp_dir)

    def test_register_dataset_skipcopy_true(self):

        temp_dir = tempfile.mkdtemp()
        try:
            src_file = os.path.join(temp_dir, 'xx')
            with open(src_file, 'w') as f:
                f.write('hi')

            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='some 10 character name',
                                  description='some 10 character desc')
            d_id = prov.register_dataset(temp_dir,
                                         source_file=src_file,
                                         skip_copy=True,
                                         data_dict={'name': 'Name of dataset',
                                                    'author': 'Author of dataset',
                                                    'version': 'Version of dataset',
                                                    'date-published': 'Date dataset was published MM-DD-YYYY',
                                                    'description': 'Description of dataset',
                                                    'data-format': 'Format of data'})
            self.assertIsNotNone(d_id)

        finally:
            shutil.rmtree(temp_dir)

    def test_get_rocrate_as_dict(self):

        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='foo', guid='12345',
                                  description='some 10 character desc')
            crate_dict = prov.get_rocrate_as_dict(temp_dir)
            self.assertIn('@id', set(crate_dict.keys()))
            self.assertIn('name', set(crate_dict.keys()))
            self.assertIn('isPartOf', set(crate_dict.keys()))
            self.assertIn('description', set(crate_dict.keys()))
            self.assertIn('keywords', set(crate_dict.keys()))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_id_of_rocrate_with_dict(self):
        prov = ProvenanceUtil()
        test_dict = {'@id': 'test-id'}
        result = prov.get_id_of_rocrate(test_dict)
        self.assertEqual(result, 'test-id')

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_rocrate_as_dict')  # Replace with your actual import
    def test_get_id_of_rocrate_with_path(self, mock_get_rocrate_as_dict):
        mock_get_rocrate_as_dict.return_value = {'@id': 'test-id'}

        prov = ProvenanceUtil()
        result = prov.get_id_of_rocrate('path/to/rocrate')
        mock_get_rocrate_as_dict.assert_called_once_with('path/to/rocrate')
        self.assertEqual(result, 'test-id')

    def test_get_name_project_org_of_rocrate(self):
        mock_data = {
            'name': 'foo',
            'description': '10 character desc sdfsdf',
            'keywords': [],
            'isPartOf': [
                {"@type": "Organization", "name": "org"},
                {"@type": "Project", "name": "proj"}
            ]
        }

        prov = ProvenanceUtil()
        result = prov.get_name_project_org_of_rocrate(mock_data)
        self.assertEqual(('foo', 'proj', 'org'), result)

    def test_get_merged_rocrate_provenance_attrs_none_for_rocrate(self):
        prov = ProvenanceUtil(raise_on_error=True)
        try:
            prov.get_merged_rocrate_provenance_attrs()
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertEqual('rocrate is None', str(ce))

    def test_get_merged_rocrate_provenance_attrs_none_for_rocrate_invalidtype(self):
        prov = ProvenanceUtil(raise_on_error=True)
        try:
            prov.get_merged_rocrate_provenance_attrs(rocrate=int(5))
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertTrue('rocrate must be type str, list or dict' in str(ce))

    def test_get_merged_rocrate_provenance_attrs_none_for_rocrate_norocrates_in_list(self):
        prov = ProvenanceUtil(raise_on_error=True)
        try:
            prov.get_merged_rocrate_provenance_attrs(rocrate=[])
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertEqual('No rocrates in list', str(ce))

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_rocrate_provenance_attributes')
    def test_get_merged_rocrate_provenance_attrs_single_crate_nooverrides(self, mock_get_attrs):
        mock_attrs = MagicMock()
        mock_attrs.get_name.return_value = 'some name'
        mock_attrs.get_project_name.return_value = 'some project name'
        mock_attrs.get_organization_name.return_value = 'some organization name'
        mock_attrs.get_keywords.return_value = ['keyword1']
        mock_get_attrs.return_value = mock_attrs

        prov = ProvenanceUtil()
        prov_attrs = prov.get_merged_rocrate_provenance_attrs(rocrate='rocrate_path')

        self.assertEqual('some name', prov_attrs.get_name())
        self.assertEqual('some project name', prov_attrs.get_project_name())
        self.assertEqual('some organization name', prov_attrs.get_organization_name())
        self.assertEqual('keyword1 some name', prov_attrs.get_description())
        self.assertEqual(['keyword1', 'some name'], prov_attrs.get_keywords())

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_rocrate_provenance_attributes')
    def test_get_merged_rocrate_provenance_attrs_single_crate_with_overrides(self, mock_get_attrs):
        mock_attrs = MagicMock()
        mock_attrs.get_name.return_value = 'some name'
        mock_attrs.get_project_name.return_value = 'some project name'
        mock_attrs.get_organization_name.return_value = 'some organization name'
        mock_attrs.get_keywords.return_value = ['keyword1']
        mock_get_attrs.return_value = mock_attrs

        prov = ProvenanceUtil()
        prov_attrs = prov.get_merged_rocrate_provenance_attrs(
            rocrate='rocrate_path',
            override_name='new name',
            override_project_name='new proj',
            override_organization_name='new org'
        )

        self.assertEqual('new name', prov_attrs.get_name())
        self.assertEqual('new proj', prov_attrs.get_project_name())
        self.assertEqual('new org', prov_attrs.get_organization_name())
        self.assertEqual('keyword1 some name', prov_attrs.get_description())
        self.assertEqual(['keyword1', 'some name'], prov_attrs.get_keywords())

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_rocrate_provenance_attributes')
    def test_get_merged_rocrate_provenance_attrs_single_crate_four_extrakeywords(self, mock_get_attrs):
        mock_attrs = MagicMock()
        mock_attrs.get_name.return_value = 'some name'
        mock_attrs.get_project_name.return_value = 'some project name'
        mock_attrs.get_organization_name.return_value = 'some organization name'
        mock_attrs.get_keywords.return_value = ['keyword1', 'keyword2', 'keyword3', 'keyword4']
        mock_get_attrs.return_value = mock_attrs

        prov = ProvenanceUtil()
        prov_attrs = prov.get_merged_rocrate_provenance_attrs(
            rocrate='rocrate_path',
            extra_keywords=['embedding']
        )
        self.assertEqual('some name', prov_attrs.get_name())
        self.assertEqual('some project name', prov_attrs.get_project_name())
        self.assertEqual('some organization name', prov_attrs.get_organization_name())
        self.assertTrue('keyword1 keyword2 keyword3 ' in prov_attrs.get_description())
        self.assertTrue('keyword4' in prov_attrs.get_description())
        self.assertTrue('embedding' in prov_attrs.get_description())
        self.assertTrue('some name' in prov_attrs.get_description())
        self.assertEqual(['keyword1', 'keyword2',
                          'keyword3', 'keyword4', 'some name',
                          'embedding'], prov_attrs.get_keywords())

    @patch('cellmaps_utils.provenance.ProvenanceUtil.get_rocrate_provenance_attributes')
    def test_get_merged_rocrate_provenance_attrs_two_crates(self, mock_get_attrs):
        mock_attrs_one = MagicMock()
        mock_attrs_one.get_name.return_value = 'one name'
        mock_attrs_one.get_project_name.return_value = 'one project name'
        mock_attrs_one.get_organization_name.return_value = 'one organization name'
        mock_attrs_one.get_keywords.return_value = ['one1', 'one2', 'one3', 'one4']

        mock_attrs_two = MagicMock()
        mock_attrs_two.get_name.return_value = 'two name'
        mock_attrs_two.get_project_name.return_value = 'two project name'
        mock_attrs_two.get_organization_name.return_value = 'two organization name'
        mock_attrs_two.get_keywords.return_value = ['two1', 'two2', 'two3', 'two4']

        mock_get_attrs.side_effect = [mock_attrs_one, mock_attrs_two]

        prov = ProvenanceUtil()
        prov_attrs = prov.get_merged_rocrate_provenance_attrs(
            rocrate=['rocrate_path_one', 'rocrate_path_two'],
            extra_keywords=['embedding']
        )

        self.assertTrue('one name|two name' == prov_attrs.get_name())
        self.assertTrue('one project name|two project name' == prov_attrs.get_project_name())
        self.assertTrue('one organization name|two organization name' == prov_attrs.get_organization_name())
        self.assertTrue('one1|two1 one2|two2 one3|two3 '
                        'one4|two4 ' in prov_attrs.get_description())
        self.assertTrue('one name' in prov_attrs.get_description())
        self.assertTrue('two name' in prov_attrs.get_description())
        self.assertTrue('embedding' in prov_attrs.get_description())

        self.assertEqual(['one1|two1', 'one2|two2',
                          'one3|two3', 'one4|two4'],
                         prov_attrs.get_keywords()[:4])
        self.assertTrue('embedding' in prov_attrs.get_keywords())
        for n in range(1, 5):
            self.assertTrue('one' + str(n) in prov_attrs.get_keywords())
            self.assertTrue('two' + str(n) in prov_attrs.get_keywords())

        self.assertEqual(15, len(prov_attrs.get_keywords()))

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_success_raise_on_error_false(self, mock_popen):
        mock_popen.return_value.communicate.return_value = (b'Success', b'')
        mock_popen.return_value.returncode = 0

        prov_util = ProvenanceUtil()
        result = prov_util._run_cmd(['fake_cmd'])
        self.assertEqual(result[0], 0)

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    @patch('cellmaps_utils.provenance.ProvenanceUtil._log_fairscape_error')
    def test_failure_raise_on_error_false(self, mock_log_error, mock_popen):
        mock_popen.return_value.communicate.return_value = (b'', b'Error')
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil()
        result = prov_util._run_cmd(['fake_cmd'])
        self.assertEqual(result[0], 1)
        mock_log_error.assert_called_once()

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_timeout(self, mock_popen):
        mock_popen.return_value.communicate.side_effect = subprocess.TimeoutExpired(cmd='fake_cmd', timeout=360)
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil(raise_on_error=True)
        with self.assertRaises(subprocess.TimeoutExpired):
            prov_util._run_cmd(['fake_cmd'])

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_register_computation_failure_raise_on_error_true(self, mock_popen):
        mock_popen.return_value.communicate.return_value = (b'', b'Error')
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil(raise_on_error=True)
        with self.assertRaises(CellMapsProvenanceError):
            prov_util.register_computation('fake_path', 'test_name')

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_register_computation_success(self, mock_popen):
        mock_popen.return_value.communicate.return_value = (b'Success', b'')
        mock_popen.return_value.returncode = 0

        prov_util = ProvenanceUtil(raise_on_error=True)
        result = prov_util.register_computation('fake_path', 'test_name')
        self.assertIn('Success', str(result))

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_register_software_failure_raise_on_error_true(self, mock_popen):
        mock_popen.return_value.communicate.return_value = (b'', b'Error')
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil(raise_on_error=True)
        with self.assertRaises(CellMapsProvenanceError):
            prov_util.register_software('fake_path', 'test_software')

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_register_software_failure_raise_on_error_false(self, mock_popen):
        mock_popen.return_value.communicate.return_value = ('out', 'Error')
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil()
        result = prov_util.register_software('fake_path', 'test_software')
        self.assertIn('out', str(result))

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_register_dataset_failure_raise_on_error_true(self, mock_popen):
        mock_popen.return_value.communicate.return_value = (b'', b'Error')
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil(raise_on_error=True)
        with self.assertRaises(CellMapsProvenanceError):
            prov_util.register_dataset('fake_path', {'name': 'Name of dataset',
                                                     'author': 'Author of dataset',
                                                     'version': 'Version of dataset',
                                                     'url': 'Url of dataset (optional)',
                                                     'date-published': 'Date dataset was published MM-DD-YYYY',
                                                     'description': 'Description of dataset',
                                                     'data-format': 'Format of data'})

    @patch('cellmaps_utils.provenance.subprocess.Popen')
    def test_register_dataset_failure_raise_on_error_false(self, mock_popen):
        mock_popen.return_value.communicate.return_value = ('out', 'Error')
        mock_popen.return_value.returncode = 1

        prov_util = ProvenanceUtil()
        result = prov_util.register_dataset('fake_path', {'name': 'Name of dataset',
                                                          'author': 'Author of dataset',
                                                          'version': 'Version of dataset',
                                                          'url': 'Url of dataset (optional)',
                                                          'date-published': 'Date dataset was published MM-DD-YYYY',
                                                          'description': 'Description of dataset',
                                                          'data-format': 'Format of data'})
        self.assertIn('out', str(result))

    @patch('cellmaps_utils.provenance.logger')
    def test_log_fairscape_error(self, mock_logger):
        mock_cmd = ['command', 'arg1', 'arg2']
        mock_exit_code = 1
        mock_err = 'Some error occurred'

        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, 'provenance_errors.json')

        try:
            prov_util = ProvenanceUtil()
            prov_util._log_fairscape_error(mock_cmd, mock_exit_code, mock_err, cwd=temp_dir)

            mock_logger.error.assert_called()

            with open(log_file, 'r') as file:
                data = json.load(file)
                expected_log_entry = {
                    "cmd": mock_cmd,
                    "exit_code": mock_exit_code,
                    "reason": 'non zero exit code : ' + mock_err.strip()
                }
                self.assertEqual(data[0], expected_log_entry)

        finally:
            os.remove(log_file)
            os.rmdir(temp_dir)

    def test_rocrate_lifecycle_where_fairscape_fails(self):
        """Test the lifecycle of RO-Crate operations in `cellmaps_utils`."""
        temp_dir = tempfile.mkdtemp()
        try:
            nonexistant_cli = os.path.join(temp_dir, 'nonexistant-cli')

            provenance_util = ProvenanceUtil(raise_on_error=False,
                                             fairscape_binary=nonexistant_cli)

            rocrate_path = os.path.join(temp_dir, "test_rocrate")
            os.mkdir(rocrate_path)
            provenance_util.register_rocrate(rocrate_path, name='Test Crate')
            self.assertFalse(os.path.isfile(os.path.join(rocrate_path,
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
                                                         source_file=i_data)

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

            rocrate_dict = provenance_util.get_rocrate_as_dict(rocrate_path)
            self.assertEqual({'@id': None, 'name': '',
                              'description': '',
                              'keywords': [''],
                              'isPartOf': [{'@type': 'Organization',
                                            'name': ''},
                                           {'@type': 'Project',
                                            'name': ''}]},
                             rocrate_dict)

            with open(os.path.join(rocrate_path, constants.PROVENANCE_ERRORS_FILE)) as f:
                data = json.load(f)
                self.assertEqual(5, len(data))
        finally:
            import time
            print(os.listdir(os.path.join(temp_dir, 'test_rocrate')))
            shutil.rmtree(temp_dir)
