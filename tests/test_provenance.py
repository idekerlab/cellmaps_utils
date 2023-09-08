#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `cellmaps_utils.cellmaps_io` package."""

import os
import sys
import shutil
import tempfile
import json
from datetime import date
import unittest
from unittest.mock import patch

from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_utils.exceptions import CellMapsProvenanceError


class TestProvenanceUtil(unittest.TestCase):
    """Tests for `cellmaps_utils` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_run_cmd_timeout(self):
        temp_dir = tempfile.mkdtemp()
        try:
            py_file = os.path.join(temp_dir, 'sleep.py')
            with open(py_file, 'w') as f:
                f.write('import time\r\n')
                f.write('time.sleep(60)\r\n')
            p = ProvenanceUtil()
            p._run_cmd([sys.executable, py_file], timeout=1)
        except CellMapsProvenanceError as ce:
            self.assertTrue('Process timed out' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_keywords(self):
        prov = ProvenanceUtil()
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
        prov = ProvenanceUtil()
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

    def test_get_rocrate_as_dict_invalid_rocrate_metadata(self):
        prov = ProvenanceUtil()
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
            self.assertTrue(os.path.isfile(crate_file))
            self.assertTrue(os.path.getsize(crate_file) > 0)
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
            prov = ProvenanceUtil()
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
            prov = ProvenanceUtil()
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
            self.assertTrue(len(c_id) > 0)
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
            self.assertTrue(len(c_id) > 0)
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
            self.assertTrue(len(s_id) > 0)
        finally:
            shutil.rmtree(temp_dir)

    def test_register_software_invalid_rocrate(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
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
            self.assertTrue(len(d_id) > 0)

        except CellMapsProvenanceError as ce:
            self.assertEqual('', str(ce))
            self.assertTrue('Error adding dataset' in str(ce))
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
            self.assertTrue(len(d_id) > 0)

        except CellMapsProvenanceError as ce:
            self.assertEqual('', str(ce))
            self.assertTrue('Error adding dataset' in str(ce))
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
            self.assertTrue(len(d_id) > 0)

        except CellMapsProvenanceError as ce:
            self.assertEqual('', str(ce))
            self.assertTrue('Error adding dataset' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_rocrate_as_dict(self):

        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='foo', guid='12345',
                                  description='some 10 character desc')
            crate_dict = prov.get_rocrate_as_dict(temp_dir)
            self.assertEqual({'@id', '@context', '@type',
                              'name', 'isPartOf', '@graph', 'description', 'keywords'},

                             set(crate_dict.keys()))
            self.assertEqual('foo', crate_dict['name'])
            self.assertEqual('12345', crate_dict['@id'])
            self.assertEqual('some 10 character desc', crate_dict['description'])

        finally:
            shutil.rmtree(temp_dir)

    def test_get_id_of_rocrate(self):

        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='foo', guid='12345', description='some 10 character desc')
            self.assertEqual('12345', prov.get_id_of_rocrate(temp_dir))

            # verify passing dict works as well
            crate_dict = prov.get_rocrate_as_dict(temp_dir)
            self.assertEqual('12345', prov.get_id_of_rocrate(crate_dict))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_name_project_org_of_rocrate(self):

        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(temp_dir, name='foo', guid='12345',
                                  project_name='proj', organization_name='org',
                                  description='10 character desc sdfsdf')
            self.assertEqual(('foo', 'proj', 'org'),
                             prov.get_name_project_org_of_rocrate(temp_dir))

            # verify passing dict works as well
            crate_dict = prov.get_rocrate_as_dict(temp_dir)
            self.assertEqual(('foo', 'proj', 'org'),
                             prov.get_name_project_org_of_rocrate(crate_dict))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_merged_rocrate_provenance_attrs_none_for_rocrate(self):
        prov = ProvenanceUtil()
        try:
            prov.get_merged_rocrate_provenance_attrs()
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertEqual('rocrate is None', str(ce))

    def test_get_merged_rocrate_provenance_attrs_none_for_rocrate_invalidtype(self):
        prov = ProvenanceUtil()
        try:
            prov.get_merged_rocrate_provenance_attrs(rocrate=int(5))
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertTrue('rocrate must be type str, list or dict' in str(ce))

    def test_get_merged_rocrate_provenance_attrs_none_for_rocrate_norocrates_in_list(self):
        prov = ProvenanceUtil()
        try:
            prov.get_merged_rocrate_provenance_attrs(rocrate=[])
            self.fail('Expected Exception')
        except CellMapsProvenanceError as ce:
            self.assertEqual('No rocrates in list', str(ce))

    def test_get_merged_rocrate_provenance_attrs_single_crate_nooverrides(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(rocrate_path=temp_dir,
                                  name='some name',
                                  project_name='some project name',
                                  description='some description name',
                                  organization_name='some organization name',
                                  keywords=['keyword1'])
            prov_attrs = prov.get_merged_rocrate_provenance_attrs(rocrate=temp_dir)
            self.assertEqual('some name', prov_attrs.get_name())
            self.assertEqual('some project name', prov_attrs.get_project_name())
            self.assertEqual('some organization name', prov_attrs.get_organization_name())
            self.assertTrue('keyword1' in prov_attrs.get_description())
            self.assertTrue('some name' in prov_attrs.get_description())
            self.assertTrue(['keyword1', 'some name'], prov_attrs.get_keywords())

        finally:
            shutil.rmtree(temp_dir)

    def test_get_merged_rocrate_provenance_attrs_single_crate_with_overrides(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(rocrate_path=temp_dir,
                                  name='some name',
                                  project_name='some project name',
                                  description='some description name',
                                  organization_name='some organization name',
                                  keywords=['keyword1'])
            prov_attrs = prov.get_merged_rocrate_provenance_attrs(rocrate=temp_dir,
                                                                  override_name='new name',
                                                                  override_organization_name='new org',
                                                                  override_project_name='new proj')
            self.assertEqual('new name', prov_attrs.get_name())
            self.assertEqual('new proj', prov_attrs.get_project_name())
            self.assertEqual('new org', prov_attrs.get_organization_name())
            self.assertEqual('keyword1 some name', prov_attrs.get_description())
            self.assertEqual(['keyword1', 'some name'], prov_attrs.get_keywords())

        finally:
            shutil.rmtree(temp_dir)

    def test_get_merged_rocrate_provenance_attrs_single_crate_four_extrakeywords(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            prov.register_rocrate(rocrate_path=temp_dir,
                                  name='some name',
                                  project_name='some project name',
                                  description='some description name',
                                  organization_name='some organization name',
                                  keywords=['keyword1', 'keyword2', 'keyword3', 'keyword4'])
            prov_attrs = prov.get_merged_rocrate_provenance_attrs(rocrate=temp_dir,
                                                                  extra_keywords=['embedding'])
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

        finally:
            shutil.rmtree(temp_dir)

    def test_get_merged_rocrate_provenance_attrs_two_crates(self):
        temp_dir = tempfile.mkdtemp()
        try:
            prov = ProvenanceUtil()
            crate_list = []
            for name in ['one', 'two']:
                crate = os.path.join(temp_dir, name)
                crate_list.append(crate)
                os.makedirs(crate, mode=0o755)
                prov.register_rocrate(rocrate_path=crate,
                                      name=name + ' name',
                                      project_name=name + ' project name',
                                      description=name + ' description name',
                                      organization_name=name + ' organization name',
                                      keywords=[name + '1',
                                                name + '2',
                                                name + '3',
                                                name + '4'])
            prov_attrs = prov.get_merged_rocrate_provenance_attrs(rocrate=crate_list,
                                                                  extra_keywords=['embedding'])
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

        finally:
            shutil.rmtree(temp_dir)




