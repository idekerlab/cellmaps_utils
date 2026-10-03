"""Tests for SEC-MS conversion using real files and local RO-Crate metadata."""

import argparse
from contextlib import redirect_stderr
from datetime import date
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

import cellmaps_utils
from cellmaps_utils import constants, secmstool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_utils.secmstool import SECMSDataConverter


class TestSECMSDataConverter(unittest.TestCase):

    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tempdir)
        self.args = argparse.Namespace(
            outdir=str(self.tempdir / 'output'),
            inputs=['first.tsv,1', 'second.tsv,2'],
            name='Test SEC-MS', organization_name='Test Lab',
            project_name='Test Project', release='1.0 Alpha',
            cell_line='Test Line', treatment='untreated',
            tissue='breast; mammary gland', author='Test Author')
        self.provenance = ProvenanceUtil(raise_on_error=True)
        self.converter = SECMSDataConverter(
            self.args, provenance_utils=self.provenance)

    def _create_inputs(self):
        contents = [
            b'PG.ProteinGroups\tIntensity\r\nP12345\t1.25\r\n',
            b'PG.ProteinGroups\tIntensity\nQ67890\tNA\n']
        paths = [self.tempdir / 'first.tsv', self.tempdir / 'second.tsv']
        for path, content in zip(paths, contents):
            path.write_bytes(content)
        self.args.inputs[:] = [str(path) + ',' + str(index)
                               for index, path in enumerate(paths, start=1)]
        return paths

    def _create_rocrate(self):
        Path(self.converter._outdir).mkdir()
        self.provenance.register_rocrate(
            self.converter._outdir, name=self.args.name,
            organization_name=self.args.organization_name,
            project_name=self.args.project_name)

    def _read_rocrate(self):
        return self.provenance.get_rocrate_as_dict(self.converter._outdir)

    def _run_converter(self):
        # Keep the test runner's global logging configuration intact.
        with patch('cellmaps_utils.secmstool.logutils.setup_filelogger'):
            return self.converter.run()

    def _read_task_json(self, suffix):
        filename = (constants.TASK_FILE_PREFIX + str(self.converter._start_time)
                    + suffix)
        return json.loads((Path(self.converter._outdir) / filename).read_text())

    def _assert_finish_status(self, status):
        task = self._read_task_json(constants.TASK_FINISH_FILE_SUFFIX)
        self.assertEqual(task['status'], str(status))
        self.assertGreaterEqual(task['end_time'], self.converter._start_time)
        self.assertGreaterEqual(task['elapsed_time'], 0)

    @staticmethod
    def _create_parser():
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command', required=True)
        SECMSDataConverter.add_subparser(subparsers)
        return parser

    def test_initialization(self):
        before = int(time.time())
        converter = SECMSDataConverter(self.args, provenance_utils=self.provenance)
        self.assertGreaterEqual(converter._start_time, before)
        self.assertLessEqual(converter._start_time, int(time.time()))
        self.assertEqual(converter._outdir, os.path.abspath(self.args.outdir))
        for attribute in ('inputs', 'name', 'organization_name', 'project_name',
                          'release', 'cell_line', 'treatment', 'tissue', 'author'):
            with self.subTest(attribute=attribute):
                self.assertEqual(getattr(converter, '_' + attribute),
                                 getattr(self.args, attribute))
        self.assertIs(converter._provenance_utils, self.provenance)
        self.assertIs(converter._input_data_dict, vars(self.args))
        self.assertIsNone(converter._softwareid)

    def test_add_subparser_defaults(self):
        args = self._create_parser().parse_args([
            'secmsconverter', 'output', '--inputs', 'first.tsv,1', 'second.tsv,2',
            '--release', '1.0'])
        self.assertEqual(vars(args), dict(
            command=SECMSDataConverter.COMMAND, outdir='output',
            inputs=['first.tsv,1', 'second.tsv,2'], release='1.0',
            author='Krogan Lab', name='SEC-MS', organization_name='Krogan Lab',
            project_name='CM4AI', treatment='untreated', cell_line='MDA-MB-468',
            tissue='breast; mammary gland'))

    def test_add_subparser_custom_metadata(self):
        args = self._create_parser().parse_args([
            'secmsconverter', 'output', '--inputs', 'input.tsv,3',
            '--release', '2.0', '--author', 'Author', '--name', 'Run',
            '--organization_name', 'Lab', '--project_name', 'Project',
            '--treatment', 'paclitaxel', '--cell_line', 'KOLF2.1J',
            '--tissue', 'neuron'])
        self.assertEqual(vars(args), dict(
            command=SECMSDataConverter.COMMAND, outdir='output',
            inputs=['input.tsv,3'], release='2.0', author='Author', name='Run',
            organization_name='Lab', project_name='Project',
            treatment='paclitaxel', cell_line='KOLF2.1J', tissue='neuron'))

    def test_add_subparser_rejects_missing_or_invalid_arguments(self):
        valid = ['secmsconverter', 'output', '--inputs', 'input.tsv,1',
                 '--release', '1.0']
        cases = [
            ['secmsconverter', 'output', '--release', '1.0'],
            ['secmsconverter', 'output', '--inputs', 'input.tsv,1'],
            ['secmsconverter', 'output', '--inputs', '--release', '1.0'],
            valid + ['--treatment', 'invalid'],
            valid + ['--tissue', 'invalid']]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    self._create_parser().parse_args(arguments)
                self.assertEqual(error.exception.code, 2)

    def test_get_input_tuples_preserves_order_and_replicate_labels(self):
        self.converter._inputs = ['path with spaces.tsv,02', 'second.tsv,rep-A']
        self.assertEqual(self.converter._get_input_tuples(),
                         [('path with spaces.tsv', '02'), ('second.tsv', 'rep-A')])

    def test_get_input_tuples_empty(self):
        self.converter._inputs = []
        self.assertEqual(self.converter._get_input_tuples(), [])

    def test_get_input_tuples_rejects_wrong_number_of_elements(self):
        for value in ('first.tsv', 'first.tsv,1,extra', ''):
            with self.subTest(value=value):
                self.converter._inputs = [value]
                with self.assertRaisesRegex(CellMapsError, 'Expecting 2 elements'):
                    self.converter._get_input_tuples()

    def test_generate_rocrate_dir_path(self):
        self.converter._generate_rocrate_dir_path()
        self.assertEqual(self.converter._outdir, os.path.join(
            self.args.outdir, 'test_project_test_line_untreated_secms_1.0_alpha'))

    def test_get_fairscape_id_is_unique(self):
        first = self.converter._get_fairscape_id()
        second = self.converter._get_fairscape_id()
        self.assertNotEqual(first, second)
        for guid in (first, second):
            identifier, basename = guid.split(':')
            self.assertEqual(str(uuid.UUID(identifier)), identifier)
            self.assertEqual(basename, 'output')

    def test_save_secms_data_copies_files_and_registers_metadata(self):
        paths = self._create_inputs()
        self._create_rocrate()
        keywords = ['CM4AI', 'SEC-MS fractions']
        datasets = self.converter._save_secms_data(
            keywords=keywords, input_tuples=self.converter._get_input_tuples())
        entries = self._read_rocrate()['@graph']
        self.assertEqual(len(entries), 2)
        self.assertEqual(datasets, [entry['@id'] for entry in entries])
        for index, (source, entry) in enumerate(zip(paths, entries), start=1):
            destination = Path(self.converter._outdir) / ('secms_' + str(index) + '.tsv')
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertTrue(entry['@type'].endswith('#Dataset'))
            self.assertEqual(entry['name'], ' SEC-MS file')
            self.assertEqual(entry['description'],
                             'SEC-MS file replicate ' + str(index) +
                             ' copied from ' + source.name)
            self.assertEqual(entry['keywords'], keywords + ['file', 'Replicate ' + str(index)])
            self.assertEqual(entry['format'], 'tsv')
            self.assertEqual(entry['author'], self.args.author)
            self.assertEqual(entry['version'], self.args.release)
            self.assertEqual(entry['datePublished'], date.today().isoformat())
        self.assertEqual(keywords, ['CM4AI', 'SEC-MS fractions'])

    def test_save_secms_data_empty(self):
        self._create_rocrate()
        self.assertEqual(self.converter._save_secms_data(input_tuples=[]), [])
        self.assertEqual(self._read_rocrate()['@graph'], [])

    def test_save_secms_data_missing_file(self):
        self._create_rocrate()
        with self.assertRaises(FileNotFoundError):
            self.converter._save_secms_data(
                input_tuples=[(str(self.tempdir / 'missing.tsv'), '1')])
        self.assertEqual(self._read_rocrate()['@graph'], [])

    def test_copy_over_secms_readme(self):
        Path(self.converter._outdir).mkdir()
        self.converter._copy_over_secms_readme()
        source = Path(secmstool.__file__).parent / 'secms_readme.txt'
        destination = Path(self.converter._outdir) / 'readme.txt'
        self.assertEqual(destination.read_bytes(), source.read_bytes())

    def test_register_software(self):
        self._create_rocrate()
        keywords = ['SEC-MS']
        self.converter._register_software(description='Description', keywords=keywords)
        entries = self._read_rocrate()['@graph']
        self.assertEqual(len(entries), 1)
        software = entries[0]
        self.assertEqual(software['@id'], self.converter._softwareid)
        self.assertTrue(software['@type'].endswith('#Software'))
        self.assertEqual(software['name'], cellmaps_utils.__name__)
        self.assertEqual(software['description'], 'Description ' + cellmaps_utils.__description__)
        self.assertEqual(software['author'], cellmaps_utils.__author__)
        self.assertEqual(software['version'], cellmaps_utils.__version__)
        self.assertEqual(software['format'], 'py')
        self.assertEqual(software['url'], cellmaps_utils.__repo_url__)
        self.assertEqual(software['keywords'], ['SEC-MS', 'tools', cellmaps_utils.__name__])
        self.assertEqual(keywords, ['SEC-MS'])

    def test_register_computation(self):
        self._create_inputs()
        self._create_rocrate()
        datasets = self.converter._save_secms_data(
            input_tuples=self.converter._get_input_tuples())
        original_datasets = datasets.copy()
        self.converter._register_software()
        keywords = ['SEC-MS']
        self.converter._register_computation(
            generated_dataset_ids=datasets, description='Description', keywords=keywords)
        computation = self._read_rocrate()['@graph'][-1]
        self.assertTrue(computation['@type'].endswith('#Computation'))
        self.assertEqual(computation['name'], 'SEC-MS')
        self.assertEqual(computation['runBy'], self.provenance.get_login())
        self.assertEqual(computation['command'], str(vars(self.args)))
        self.assertEqual(computation['description'], 'Description run of ' + cellmaps_utils.__name__)
        self.assertEqual(computation['keywords'], ['SEC-MS', 'computation'])
        self.assertEqual(computation['usedSoftware'], [self.converter._softwareid])
        self.assertEqual(computation['generated'], datasets)
        self.assertEqual(keywords, ['SEC-MS'])
        self.assertEqual(datasets, original_datasets)

    def test_run(self):
        paths = self._create_inputs()
        self.assertEqual(self._run_converter(), 0)
        outdir = Path(self.converter._outdir)
        for index, source in enumerate(paths, start=1):
            self.assertEqual((outdir / ('secms_' + str(index) + '.tsv')).read_bytes(),
                             source.read_bytes())
        self.assertEqual((outdir / 'readme.txt').read_bytes(),
                         (Path(secmstool.__file__).parent / 'secms_readme.txt').read_bytes())
        self.assertEqual(json.loads((outdir / constants.DATASET_INFO_FILE).read_text()), {
            constants.DATASET_NAME: self.args.name,
            constants.DATASET_ORGANIZATION_NAME: self.args.organization_name,
            constants.DATASET_PROJECT_NAME: self.args.project_name,
            constants.DATASET_RELEASE: self.args.release,
            constants.DATASET_CELL_LINE: self.args.cell_line,
            constants.DATASET_TREATMENT: self.args.treatment,
            constants.DATASET_TISSUE: self.args.tissue,
            constants.DATASET_AUTHOR: self.args.author,
            constants.DATASET_REPLICATES: '1,2'})
        keywords = ['Test Project', '1.0 Alpha', 'Test Line', 'untreated',
                    'breast; mammary gland', 'SEC-MS fractions']
        crate = self._read_rocrate()
        self.assertEqual(crate['name'], self.args.name)
        self.assertEqual(crate['description'], ' '.join(keywords))
        self.assertEqual(crate['keywords'], keywords)
        self.assertEqual([entry['name'] for entry in crate['isPartOf']],
                         [self.args.organization_name, self.args.project_name])
        self.assertEqual(len(crate['@graph']), 4)
        first, second, software, computation = crate['@graph']
        self.assertEqual(computation['generated'], [first['@id'], second['@id']])
        self.assertEqual(software['@id'], self.converter._softwareid)
        self.assertEqual(computation['usedSoftware'], [software['@id']])
        task_start = self._read_task_json(constants.TASK_START_FILE_SUFFIX)
        self.assertEqual(task_start['start_time'], self.converter._start_time)
        self.assertEqual(task_start['outdir'], str(outdir))
        self.assertEqual(task_start['commandlineargs'], vars(self.args))
        self.assertEqual(task_start['version'], cellmaps_utils.__version__)
        self._assert_finish_status(0)

    def test_run_existing_output_directory(self):
        outdir = Path(self.args.outdir) / 'test_project_test_line_untreated_secms_1.0_alpha'
        outdir.mkdir(parents=True)
        sentinel = outdir / 'existing.txt'
        sentinel.write_text('preserve this file')
        with self.assertRaisesRegex(CellMapsError, ' already exists'):
            self._run_converter()
        self.assertEqual(sentinel.read_text(), 'preserve this file')
        self.assertFalse((outdir / 'ro-crate-metadata.json').exists())
        self.assertEqual(list(outdir.glob('*' + constants.TASK_START_FILE_SUFFIX)), [])
        self._assert_finish_status(99)

    def test_run_invalid_input_records_failure(self):
        self.converter._inputs = ['invalid.tsv']
        with self.assertRaisesRegex(CellMapsError, 'Expecting 2 elements'):
            self._run_converter()
        self.assertFalse((Path(self.converter._outdir) / 'ro-crate-metadata.json').exists())
        self._assert_finish_status(99)

    def test_run_missing_input_records_failure(self):
        self.converter._inputs = [str(self.tempdir / 'missing.tsv') + ',1']
        with self.assertRaises(FileNotFoundError):
            self._run_converter()
        self.assertEqual(self._read_rocrate()['@graph'], [])
        self._assert_finish_status(99)

    def test_run_provenance_failure_records_failure(self):
        self._create_inputs()
        with patch.object(self.provenance, 'register_dataset',
                          side_effect=CellMapsError('Registration failed')):
            with self.assertRaisesRegex(CellMapsError, 'Registration failed'):
                self._run_converter()
        self.assertEqual(self._read_rocrate()['@graph'], [])
        self.assertFalse((Path(self.converter._outdir) / 'readme.txt').exists())
        self._assert_finish_status(99)


if __name__ == '__main__':
    unittest.main()
