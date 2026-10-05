import json
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
                                   baitcolname='Bait',
                                   tissue='breast; mammory gland',
                                   input_format='legacy',
                                   drug=None,
                                   drug_effect_input=None,
                                   drug_effect_rows='all',
                                   exclude_baits=['MDA'],
                                   filter='any_pass',
                                   no_unfiltered=False)
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

    def test_generate_rocrate_dir_path_with_set_name(self):
        self.mock_args.set_name = 'set1'
        self.loader = APMSDataLoader(self.mock_args)
        self.loader._generate_rocrate_dir_path()
        expected_dir_name = os.path.join('/fakepath',
                                         'test_project_test_set_test_line_test_treatment_set1_apms_1.0').lower().replace(' ',
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
                                       tissue='breast; mammory gland',
                                       input_format='legacy',
                                       drug=None,
                                       drug_effect_input=None,
                                       drug_effect_rows='all',
                                       exclude_baits=['MDA'],
                                       filter='any_pass',
                                       no_unfiltered=False)
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

class TestAPMSDataLoaderZmadexSaint(unittest.TestCase):
    """
    Tests the Zmadex/SAINT input format added for the 2025_04_04
    Krogan release
    """

    SAINT_FILE = os.path.join(os.path.dirname(__file__), 'data',
                              'zmadex_saint_example.csv')
    MSSTATS_FILE = os.path.join(os.path.dirname(__file__), 'data',
                                'msstats_drug_effect_example.tsv')

    def _get_args(self, outdir='/fakepath', drug='VRST',
                  treatment='vorinostat', drug_effect_input=None,
                  drug_effect_rows='all', thefilter='any_pass',
                  no_unfiltered=False, inputs=None,
                  input_format='zmadex_saint', gene_set='chromatin'):
        if inputs is None:
            inputs = [TestAPMSDataLoaderZmadexSaint.SAINT_FILE]
        args = MagicMock(outdir=outdir,
                         inputs=inputs,
                         organization_name='Test Org',
                         project_name='Test Project',
                         release='1.0',
                         cell_line='Test Line',
                         treatment=treatment,
                         author='Test Author',
                         gene_set=gene_set,
                         set_name=None,
                         baitcolname='Bait',
                         tissue='breast; mammary gland',
                         input_format=input_format,
                         drug=drug,
                         drug_effect_input=drug_effect_input,
                         drug_effect_rows=drug_effect_rows,
                         exclude_baits=['MDA'],
                         no_unfiltered=no_unfiltered)
        # name and filter collide with MagicMock/builtins so set them after
        args.name = 'Test Name'
        args.filter = thefilter
        return args

    def _get_loader(self, **kwargs):
        loader = APMSDataLoader(self._get_args(**kwargs))
        loader._name = 'Test Name'
        return loader

    def _build_arm(self, **kwargs):
        """
        Runs the load/select/filter chain without touching the filesystem
        """
        loader = self._get_loader(**kwargs)
        saint_df = loader._load_zmadex_saint()
        arm_df = loader._select_drug_arm(saint_df)
        return loader, arm_df, loader._apply_filter(arm_df)

    def test_column_renaming(self):
        loader = self._get_loader()
        df = loader._load_zmadex_saint()
        for renamed in APMSDataLoader.ZMADEX_SAINT_COL_MAP.values():
            self.assertIn(renamed, df.columns)
        for original in APMSDataLoader.ZMADEX_SAINT_COL_MAP.keys():
            self.assertNotIn(original, df.columns)
        # label must survive as ReferenceLabel
        self.assertIn('ReferenceLabel', df.columns)
        self.assertEqual(18, loader._qc['zmadex_saint_input_rows'])

    def test_missing_required_column_raises(self):
        temp_dir = tempfile.mkdtemp()
        try:
            bad = os.path.join(temp_dir, 'bad.csv')
            df = pd.read_csv(TestAPMSDataLoaderZmadexSaint.SAINT_FILE,
                             dtype=str, na_filter=False)
            df.drop(columns=['passZ']).to_csv(bad, index=False)
            loader = self._get_loader(inputs=[bad])
            loader._load_zmadex_saint()
            self.fail('Expected CellMapsError')
        except CellMapsError as ce:
            self.assertTrue('passZ' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_apms_schema_identical_across_treatments(self):
        """
        The point of keeping drug effect in its own file. Both arms, with
        and without a drug effect input, must yield the same header
        """
        _, vrst_arm, vrst_filt = self._build_arm(drug='VRST')
        _, dmso_arm, dmso_filt = self._build_arm(drug='DMSO',
                                                 treatment='untreated')
        self.assertEqual(APMSDataLoader.APMS_COLS, list(vrst_arm.columns))
        self.assertEqual(APMSDataLoader.APMS_COLS, list(dmso_arm.columns))
        self.assertEqual(list(vrst_filt.columns), list(dmso_filt.columns))
        self.assertEqual(14, len(APMSDataLoader.APMS_COLS))

    def test_no_drug_effect_column_in_apms_tables(self):
        _, arm_df, filtered_df = self._build_arm()
        for df in [arm_df, filtered_df]:
            for colname in df.columns:
                self.assertFalse(colname.startswith('DrugEffect'),
                                 colname + ' leaked into an AP-MS table')
        self.assertNotIn(APMSDataLoader.DRUG_COL, arm_df.columns)

    def test_select_drug_arm_splits_disjoint(self):
        _, vrst_arm, _ = self._build_arm(drug='VRST')
        _, dmso_arm, _ = self._build_arm(drug='DMSO', treatment='untreated')
        self.assertEqual(9, len(vrst_arm))
        self.assertEqual(9, len(dmso_arm))
        # same keys in both arms, different measurements
        vrst_keys = set(map(tuple, vrst_arm[APMSDataLoader.KEY_COLS].values))
        dmso_keys = set(map(tuple, dmso_arm[APMSDataLoader.KEY_COLS].values))
        self.assertEqual(vrst_keys, dmso_keys)
        self.assertNotEqual(list(vrst_arm['Zmadex']), list(dmso_arm['Zmadex']))

    def test_select_drug_arm_unknown_drug_raises(self):
        try:
            self._build_arm(drug='NOTADRUG')
            self.fail('Expected CellMapsError')
        except CellMapsError as ce:
            self.assertTrue('NOTADRUG' in str(ce))

    def test_bait_in_two_batches_stays_distinct(self):
        """
        HDAC2 appears in SET1 and SET5, so Bait + Prey alone is not a key
        """
        _, arm_df, _ = self._build_arm()
        hdac2 = arm_df[arm_df['Bait'] == 'HDAC2']
        self.assertEqual({'SET1', 'SET5'}, set(hdac2['Batch']))
        # P00001 is under HDAC2 in both batches
        dupes = hdac2[hdac2['Prey'] == 'P00001']
        self.assertEqual(2, len(dupes))
        self.assertEqual(0, int(arm_df.duplicated(APMSDataLoader.KEY_COLS).sum()))
        # but duplicated on the two column key it would collide
        self.assertEqual(1, int(arm_df.duplicated(['Bait', 'Prey']).sum()))

    def test_duplicate_keys_raise(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dupe = os.path.join(temp_dir, 'dupe.csv')
            df = pd.read_csv(TestAPMSDataLoaderZmadexSaint.SAINT_FILE,
                             dtype=str, na_filter=False)
            pd.concat([df, df.head(2)]).to_csv(dupe, index=False)
            loader = self._get_loader(inputs=[dupe])
            loader._select_drug_arm(loader._load_zmadex_saint())
            self.fail('Expected CellMapsError')
        except CellMapsError as ce:
            self.assertTrue('duplicate' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def test_blank_scores_survive_as_empty_strings(self):
        _, arm_df, filtered_df = self._build_arm()
        blank = arm_df[arm_df['Prey'] == 'P00002']
        self.assertEqual(1, len(blank))
        for colname in ['Zmadex', 'BaitControlLog2FC', 'SAINTBFDRIntensity',
                        'SAINTBFDRSpectralCount', 'PassSAINTIntensity',
                        'PassSAINTSpectralCount']:
            self.assertEqual('', blank.iloc[0][colname],
                             colname + ' should be an empty string')
        # a real zero must not be confused with a blank
        hdac2 = arm_df[(arm_df['Bait'] == 'HDAC2') &
                       (arm_df['Prey'] == 'Q92769')]
        self.assertEqual('0', hdac2.iloc[0]['SAINTBFDRIntensity'])

    def test_blank_pass_flags_excluded_without_raising(self):
        _, arm_df, filtered_df = self._build_arm(thefilter='any_pass')
        self.assertIn('P00002', list(arm_df['Prey']))
        self.assertNotIn('P00002', list(filtered_df['Prey']))

    def test_filter_modes(self):
        expected = {'any_pass': 5, 'passz': 4, 'saint_intensity': 4,
                    'saint_spc': 5, 'none': 9}
        for mode, count in expected.items():
            _, arm_df, filtered_df = self._build_arm(thefilter=mode)
            self.assertEqual(count, len(filtered_df),
                             'filter ' + mode + ' gave ' + str(len(filtered_df)))
        # none must be a true no-op
        _, arm_df, filtered_df = self._build_arm(thefilter='none')
        self.assertEqual(len(arm_df), len(filtered_df))

    def test_msstats_rename_and_projection(self):
        loader = self._get_loader(
            drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
        df = loader._load_msstats()
        self.assertEqual(APMSDataLoader.DRUG_EFFECT_COLS, list(df.columns))
        self.assertEqual(13, len(df.columns))
        for dropped in ['PositiveCondition', 'NegativeCondition', 'BaitUniprot',
                        'Gene', 'GeneInteraction', 'UniprotInteraction',
                        'PositiveComplete', 'NegativeComplete',
                        'MissingPercentage', 'ImputationPercentage']:
            self.assertNotIn(dropped, df.columns)

    def test_msstats_excludes_control_bait(self):
        loader = self._get_loader(
            drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
        df = loader._load_msstats()
        self.assertNotIn('MDA', list(df['Bait']))
        self.assertEqual(12, loader._qc['msstats_input_rows'])
        self.assertEqual(2, loader._qc['msstats_rows_excluded_by_bait']['MDA'])
        self.assertEqual(10, loader._qc['msstats_rows_after_bait_exclusion'])

    def test_msstats_without_control_bait_still_succeeds(self):
        temp_dir = tempfile.mkdtemp()
        try:
            nomda = os.path.join(temp_dir, 'nomda.tsv')
            df = pd.read_csv(TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE,
                             sep='\t', dtype=str, na_filter=False)
            df[df['Bait'] != 'MDA'].to_csv(nomda, sep='\t', index=False)
            loader = self._get_loader(drug_effect_input=nomda)
            result = loader._load_msstats()
            self.assertEqual(10, len(result))
            self.assertEqual(0, loader._qc['msstats_rows_excluded_by_bait']['MDA'])
        finally:
            shutil.rmtree(temp_dir)

    def test_protein_groups_never_exploded(self):
        loader = self._get_loader(
            drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
        df = loader._load_msstats()
        self.assertEqual(1, loader._qc['msstats_protein_group_rows'])
        # row count must be unchanged by the rename/projection
        self.assertEqual(10, len(df))
        groups = df[df['Prey'].str.contains(';')]
        self.assertEqual(1, len(groups))
        self.assertEqual('P00006;P00007', groups.iloc[0]['Prey'])
        # neither accession may appear on its own
        self.assertNotIn('P00006', list(df['Prey']))
        self.assertNotIn('P00007', list(df['Prey']))

    def test_drug_effect_rows_variants(self):
        expected = {'all': 10, 'saint_universe': 8, 'apms_keys': 5}
        for mode, count in expected.items():
            loader, arm_df, filtered_df = self._build_arm(
                drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE,
                drug_effect_rows=mode)
            drug_df = loader._restrict_drug_effect(loader._load_msstats(),
                                                   arm_df, filtered_df)
            self.assertEqual(count, len(drug_df),
                             'drug_effect_rows ' + mode)
            self.assertEqual(count, loader._qc['drug_effect_rows_written'])
            # every variant must still cover all of apms.tsv
            loader._check_drug_effect_coverage(filtered_df, drug_df)
            self.assertEqual(loader._qc['apms_keys'],
                             loader._qc['apms_keys_with_drug_effect'],
                             'drug_effect_rows ' + mode + ' lost coverage')
            self.assertEqual(0, loader._qc['apms_keys_without_drug_effect'])

    def test_unmatched_msstats_row_kept_under_all_dropped_otherwise(self):
        """
        P99999 is quantified by MSstats but is not in the SAINT prey universe
        """
        for mode, present in [('all', True), ('saint_universe', False),
                              ('apms_keys', False)]:
            loader, arm_df, filtered_df = self._build_arm(
                drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE,
                drug_effect_rows=mode)
            drug_df = loader._restrict_drug_effect(loader._load_msstats(),
                                                   arm_df, filtered_df)
            self.assertEqual(present, 'P99999' in list(drug_df['Prey']),
                             'drug_effect_rows ' + mode)

    def test_apms_keys_matches_saint_universe_when_filter_none(self):
        """
        With no filter the arm is the SAINT universe, so the two restrictions
        must agree. Documented behaviour, not a bug
        """
        frames = {}
        for mode in ['saint_universe', 'apms_keys']:
            loader, arm_df, filtered_df = self._build_arm(
                drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE,
                drug_effect_rows=mode, thefilter='none')
            frames[mode] = loader._restrict_drug_effect(loader._load_msstats(),
                                                        arm_df, filtered_df)
        pd.testing.assert_frame_equal(frames['saint_universe'],
                                      frames['apms_keys'])

    def test_drug_effect_joins_one_to_one(self):
        loader, arm_df, filtered_df = self._build_arm(
            drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
        drug_df = loader._restrict_drug_effect(loader._load_msstats(),
                                               arm_df, filtered_df)
        merged = filtered_df.merge(drug_df, on=APMSDataLoader.KEY_COLS,
                                   how='left')
        self.assertEqual(len(filtered_df), len(merged))
        self.assertEqual(0, merged['DrugEffect'].isna().sum())

    def test_gene_set_check_warns_only(self):
        loader, arm_df, _ = self._build_arm()
        loader._check_gene_set(arm_df)
        # PIM1 is the only bait off the published chromatin list, SMARCA4
        # must be resolved through its BRG1 alias
        self.assertEqual(['PIM1'], loader._qc['baits_not_in_gene_set'])
        self.assertEqual(3, loader._qc['bait_count'])

    def test_validate_args_rejects_bad_combinations(self):
        cases = [
            (dict(input_format='legacy',
                  drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE),
             'only supported'),
            (dict(inputs=['a.csv', 'b.csv']), 'exactly one'),
            (dict(drug=None), '--drug is required'),
            (dict(drug_effect_rows='apms_keys'), 'nothing to act on'),
            (dict(input_format='bogus'), '--input_format'),
            (dict(thefilter='bogus'), '--filter'),
            (dict(drug_effect_rows='bogus',
                  drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE),
             '--drug_effect_rows'),
        ]
        for kwargs, expected in cases:
            try:
                self._get_loader(**kwargs)._validate_args()
                self.fail('Expected CellMapsError for ' + str(kwargs))
            except CellMapsError as ce:
                self.assertTrue(expected in str(ce),
                                str(kwargs) + ' gave: ' + str(ce))

    def test_validate_args_accepts_good_combinations(self):
        self._get_loader()._validate_args()
        self._get_loader(
            drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE
        )._validate_args()
        self._get_loader(drug='DMSO', treatment='untreated')._validate_args()

    def test_empty_filter_result_raises(self):
        temp_dir = tempfile.mkdtemp()
        try:
            nopass = os.path.join(temp_dir, 'nopass.csv')
            df = pd.read_csv(TestAPMSDataLoaderZmadexSaint.SAINT_FILE,
                             dtype=str, na_filter=False)
            for colname in ['passZ', 'passSAINTintensity', 'passSAINTspc']:
                df[colname] = 'FALSE'
            df.to_csv(nopass, index=False)
            loader = self._get_loader(outdir=temp_dir, inputs=[nopass])
            loader._outdir = temp_dir
            loader._run_zmadex_saint()
            self.fail('Expected CellMapsError')
        except CellMapsError as ce:
            self.assertTrue('no rows' in str(ce))
        finally:
            shutil.rmtree(temp_dir)

    def _run_full(self, temp_dir, **kwargs):
        out_dir = os.path.join(temp_dir, 'run')
        loader = self._get_loader(outdir=out_dir, **kwargs)
        loader._provenance_utils = MagicMock()
        loader._provenance_utils.get_login = MagicMock(return_value='smith')
        loader._provenance_utils.register_dataset = MagicMock(return_value='dsid')
        self.assertEqual(0, loader.run())
        return loader

    def test_run_untreated_arm(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._run_full(temp_dir, drug='DMSO',
                                    treatment='untreated')
            apms = os.path.join(loader._outdir, constants.APMS_TSV_FILE)
            unfiltered = os.path.join(loader._outdir,
                                      constants.APMS_UNFILTERED_TSV_FILE)
            drug_effect = os.path.join(loader._outdir,
                                       constants.APMS_DRUG_EFFECT_TSV_FILE)
            self.assertTrue(os.path.exists(apms))
            self.assertTrue(os.path.exists(unfiltered))
            self.assertFalse(os.path.exists(drug_effect),
                             'untreated crate must have no drug effect file')
            self.assertTrue(os.path.exists(os.path.join(loader._outdir,
                                                        constants.APMS_QC_FILE)))
            apms_df = pd.read_csv(apms, sep='\t', dtype=str, na_filter=False)
            unfil_df = pd.read_csv(unfiltered, sep='\t', dtype=str,
                                   na_filter=False)
            self.assertEqual(APMSDataLoader.APMS_COLS, list(apms_df.columns))
            self.assertEqual(list(apms_df.columns), list(unfil_df.columns))
            self.assertEqual(5, len(apms_df))
            self.assertEqual(9, len(unfil_df))
            # two datasets registered, apms + unfiltered, plus the qc file
            self.assertEqual(3,
                             loader._provenance_utils.register_dataset.call_count)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_vorinostat_arm(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._run_full(
                temp_dir, drug='VRST', treatment='vorinostat',
                drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
            drug_effect = os.path.join(loader._outdir,
                                       constants.APMS_DRUG_EFFECT_TSV_FILE)
            self.assertTrue(os.path.exists(drug_effect))
            drug_df = pd.read_csv(drug_effect, sep='\t', dtype=str,
                                  na_filter=False)
            self.assertEqual(APMSDataLoader.DRUG_EFFECT_COLS,
                             list(drug_df.columns))
            self.assertEqual(10, len(drug_df))
            apms_df = pd.read_csv(os.path.join(loader._outdir,
                                               constants.APMS_TSV_FILE),
                                  sep='\t', dtype=str, na_filter=False)
            self.assertEqual(APMSDataLoader.APMS_COLS, list(apms_df.columns))
            # apms + unfiltered + drug effect + qc
            self.assertEqual(4,
                             loader._provenance_utils.register_dataset.call_count)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_no_unfiltered(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._run_full(temp_dir, no_unfiltered=True)
            self.assertFalse(os.path.exists(
                os.path.join(loader._outdir,
                             constants.APMS_UNFILTERED_TSV_FILE)))
            self.assertTrue(os.path.exists(
                os.path.join(loader._outdir, constants.APMS_TSV_FILE)))
            self.assertEqual(2,
                             loader._provenance_utils.register_dataset.call_count)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_qc_contents(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._run_full(
                temp_dir, drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
            with open(os.path.join(loader._outdir,
                                   constants.APMS_QC_FILE), 'r') as f:
                qc = json.load(f)
            for key in ['zmadex_saint_input_rows', 'msstats_input_rows',
                        'msstats_rows_excluded_by_bait',
                        'msstats_rows_after_bait_exclusion',
                        'msstats_protein_group_rows', 'drug_arm',
                        'apms_rows_before_filter', 'apms_rows_after_filter',
                        'filter', 'drug_effect_rows',
                        'drug_effect_rows_written', 'apms_keys',
                        'apms_keys_with_drug_effect',
                        'apms_keys_without_drug_effect',
                        'apms_duplicate_keys', 'bait_count',
                        'baits_not_in_gene_set', 'drug_effect_categories',
                        'apms_rows_with_blank_scores', 'PassZ_true',
                        'PassSAINTIntensity_true',
                        'PassSAINTSpectralCount_true']:
                self.assertIn(key, qc)
            self.assertEqual(18, qc['zmadex_saint_input_rows'])
            self.assertEqual(9, qc['apms_rows_before_filter'])
            self.assertEqual(5, qc['apms_rows_after_filter'])
            self.assertEqual(0, qc['apms_duplicate_keys'])
            self.assertEqual(1, qc['msstats_protein_group_rows'])
            self.assertEqual(['PIM1'], qc['baits_not_in_gene_set'])
            self.assertEqual(qc['apms_keys'], qc['apms_keys_with_drug_effect'])
        finally:
            shutil.rmtree(temp_dir)

    def test_run_readme_is_generated_not_copied(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._run_full(
                temp_dir, drug_effect_input=TestAPMSDataLoaderZmadexSaint.MSSTATS_FILE)
            with open(os.path.join(loader._outdir, 'readme.txt'), 'r') as f:
                readme = f.read()
            self.assertNotIn(APMSDataLoader.SUMMARY_MARKER, readme)
            self.assertIn(constants.APMS_DRUG_EFFECT_TSV_FILE, readme)
            self.assertIn('--filter any_pass', readme)
            self.assertIn('ReferenceLabel', readme)
            # legacy columns may be named as absent, but must not be
            # documented here as column labels
            self.assertNotIn('SaintScore.x:', readme)
            self.assertNotIn('logOddsScore:', readme)
            self.assertIn('does not carry the legacy SAINT columns', readme)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_readme_untreated_explains_missing_drug_effect(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._run_full(temp_dir, drug='DMSO',
                                    treatment='untreated')
            with open(os.path.join(loader._outdir, 'readme.txt'), 'r') as f:
                readme = f.read()
            self.assertIn('has no ' + constants.APMS_DRUG_EFFECT_TSV_FILE +
                          ' by design', readme)
        finally:
            shutil.rmtree(temp_dir)

    def test_legacy_readme_still_used_for_legacy_format(self):
        temp_dir = tempfile.mkdtemp()
        try:
            loader = self._get_loader(input_format='legacy', drug=None)
            loader._outdir = temp_dir
            loader._copy_over_apms_readme()
            with open(os.path.join(temp_dir, 'readme.txt'), 'r') as f:
                readme = f.read()
            self.assertIn('SaintScore.x', readme)
            self.assertNotIn('ReferenceLabel', readme)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
