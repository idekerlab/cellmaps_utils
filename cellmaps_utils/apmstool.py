import json
import os
import sys
import uuid
import shutil
from datetime import date
import logging
import pandas as pd
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil

logger = logging.getLogger(__name__)


class APMSDataLoader(BaseCommandLineTool):
    """
    Creates RO-Crate of AP-MS data from
    raw AP-MS tables
    """
    COMMAND = 'apmsconverter'

    BAIT_COL_NAME = 'Bait'

    LEGACY_FORMAT = 'legacy'
    """
    Value for ``--input_format`` denoting the original SAINT tables
    """

    ZMADEX_SAINT_FORMAT = 'zmadex_saint'
    """
    Value for ``--input_format`` denoting the Zmadex/SAINT tables
    introduced with the 2025_04_04 Krogan release
    """

    INPUT_FORMATS = [LEGACY_FORMAT, ZMADEX_SAINT_FORMAT]

    DRUG_COL = 'drug'
    """
    Name of column in Zmadex/SAINT input used to split treatment arms.
    The column is consumed by the split and never written out
    """

    ZMADEX_SAINT_COL_MAP = {'baitGene': 'Bait',
                            'preyProtein': 'Prey',
                            'preyGene': 'PreyGene',
                            'batch': 'Batch',
                            'meanZmadex': 'Zmadex',
                            'meanLog2FC': 'BaitControlLog2FC',
                            'obsCount': 'ObservedCount',
                            'missingCount': 'MissingCount',
                            'SAINT.BFDR.intensity': 'SAINTBFDRIntensity',
                            'SAINT.BFDR.spc': 'SAINTBFDRSpectralCount',
                            'passZ': 'PassZ',
                            'passSAINTintensity': 'PassSAINTIntensity',
                            'passSAINTspc': 'PassSAINTSpectralCount',
                            'label': 'ReferenceLabel'}
    """
    Zmadex/SAINT source column to normalized AP-MS column
    """

    APMS_COLS = ['Bait', 'Prey', 'PreyGene', 'Batch',
                 'Zmadex', 'BaitControlLog2FC',
                 'ObservedCount', 'MissingCount',
                 'SAINTBFDRIntensity', 'SAINTBFDRSpectralCount',
                 'PassZ', 'PassSAINTIntensity', 'PassSAINTSpectralCount',
                 'ReferenceLabel']
    """
    Column order of apms.tsv and apms_unfiltered.tsv. Identical for every
    treatment so downstream consumers need no per-crate branching
    """

    MSSTATS_COL_MAP = {'Batch': 'Batch',
                       'Bait': 'Bait',
                       'Protein': 'Prey',
                       'log2FC': 'DrugEffectLog2FC',
                       'SE': 'DrugEffectSE',
                       'Tvalue': 'DrugEffectTValue',
                       'DF': 'DrugEffectDF',
                       'pvalue': 'DrugEffectPValue',
                       'adj.pvalue': 'DrugEffectAdjustedPValue',
                       'Significant': 'DrugEffectSignificant',
                       'Effect': 'DrugEffect',
                       'issue': 'DrugEffectIssue',
                       'Label': 'DrugEffectComparison'}
    """
    MSstats source column to normalized drug effect column
    """

    DRUG_EFFECT_COLS = ['Batch', 'Bait', 'Prey',
                        'DrugEffectLog2FC', 'DrugEffectSE',
                        'DrugEffectTValue', 'DrugEffectDF',
                        'DrugEffectPValue', 'DrugEffectAdjustedPValue',
                        'DrugEffectSignificant', 'DrugEffect',
                        'DrugEffectIssue', 'DrugEffectComparison']
    """
    Column order of apms_drug_effect.tsv
    """

    KEY_COLS = ['Batch', 'Bait', 'Prey']
    """
    Join key. All three are needed, HDAC2 and USP7 appear in two batches
    so Bait + Prey alone is not unique
    """

    PASS_COLS = ['PassZ', 'PassSAINTIntensity', 'PassSAINTSpectralCount']

    FILTER_ANY_PASS = 'any_pass'
    FILTER_NONE = 'none'

    FILTER_MODES = {FILTER_ANY_PASS: PASS_COLS,
                    'passz': ['PassZ'],
                    'saint_intensity': ['PassSAINTIntensity'],
                    'saint_spc': ['PassSAINTSpectralCount'],
                    FILTER_NONE: []}
    """
    ``--filter`` value to the columns that must hold ``TRUE``
    """

    DRUG_EFFECT_ROWS_ALL = 'all'
    DRUG_EFFECT_ROWS_SAINT_UNIVERSE = 'saint_universe'
    DRUG_EFFECT_ROWS_APMS_KEYS = 'apms_keys'

    DRUG_EFFECT_ROWS_CHOICES = [DRUG_EFFECT_ROWS_ALL,
                                DRUG_EFFECT_ROWS_SAINT_UNIVERSE,
                                DRUG_EFFECT_ROWS_APMS_KEYS]

    TRUE_VAL = 'TRUE'

    KNOWN_DRUGS = ['DMSO', 'VRST']

    DRUG_TO_TREATMENT = {'DMSO': 'untreated',
                         'VRST': 'vorinostat'}

    KNOWN_DRUG_EFFECTS = ['up', 'down', 'insig',
                          'gained', 'lost', 'unidentified']

    GENE_SET_ALIASES = {'SMARCA4': 'BRG1',
                        'MORF4L1': 'MRG15',
                        'NSD1': 'KMT3B'}
    """
    Baits published under a legacy alias in the CM4AI gene set tables.
    Resolved before the gene set check so they are not reported missing
    """

    CHROMATIN_GENE_SET = set("""
        PARP1 BAP1 USP7 NEDD4 BRCA1 BARD1 BRE1A CBL MSL1 PHF6 TAF1 UHRF1 UHRF2 KAT2A KAT3A KAT3B
        KAT6A KAT6B HDAC1 HDAC2 HDAC3 HDAC4 HDAC5 HDAC6 HDAC7 HDAC8 HDAC9 HDAC10 HDAC11 SIRT2
        KDM3B KDM4C KDM5A KDM5B KDM5C KDM6A KDM6B TET1 TET2 TET3 ATM ATR AURKB AURKA CSNK2A1
        HASPIN JAK2 MSK1 MSK2 PRKCA PRKCB PRKCD BAZ1B PRKAA1 PRKAA2 PRKAB1 PRKAB2 PRKAG1 PRKAG2
        PRKAG3 DNMT1 DNMT3A DNMT3B KMT1D KMT1F KMT2A KMT2C KMT2D KMT2E KMT2H KMT3B PRMT1 EYA1
        EYA3 PPP1CA PPP1CB PPP1CC PPP4C BPTF BRD4 BRD7 BRPF1 CHD4 ING1 TRIM24 YWHAZ YWHAE YWHAQ
        YWHAB YWHAH YWHAG BRG1 CBX2 CBX3 MRG15 53BP1 BRD3 CHD1 MBTD1 PDP1 RAG2
        """.split())
    """
    CM4AI Year 1 chromatin modifier genes, see
    https://cm4ai.org/product-documentation/#year-1-chromatin-modifier-genes-proteins
    """

    METABOLIC_GENE_SET = set("""
        FOLR1 MTHFR MTR MTHFD1 MAT1A MAT2A MAT2B AHCY SHMT1 RFK FLAD1 TKFC ACAD9 ACADM ACADS
        ACADSB ACADVL ACAT1 ACOT7 ACOX3 ACSS2 ACSS3 GMPS LDHA LDHB LDHD ACLY ALDH5A1 DLAT DLD
        GLUD1 GLUD2 IDH1 IDH3A IDH3B IDH3G MDH2 OGDH PDHA1 PDHA2 PDHB SDHA G6PD GAPDH NADK
        NDUFS4 NDUFAB1 NMNAT2 NNT PGD PGM1 PHGDH PYGL SRC KIT ITPKA AKT1 BRAF CDK4 DAPK3 FYN
        PIK3CA PIK3C2A NUAK1 STK4 MAPK1 MTOR PIP5K1C RIPK1 RPS6KA3 KRAS TGFBR2 WEE1 PPA2 AHCYL2
        CYP27A1 DIO3 GSTM1 HEXA NAGS NCOA1 PANK2 PARP4 PARP6 PLCD4 PLCG1 SLC2A1 UGDH UGT8 UBE3C
        CYP24A1 GCLM GYG2 PDE4A PLPP7 AMDHD2 ABHD6
        """.split())
    """
    CM4AI Year 2 metabolic enzyme genes, see
    https://cm4ai.org/product-documentation/#year-2-metabolic-enzyme-genes-proteins
    """

    GENE_SETS = {'chromatin': CHROMATIN_GENE_SET,
                 'metabolic': METABOLIC_GENE_SET}

    SUMMARY_MARKER = '@@DATASET_SUMMARY@@'
    """
    Placeholder in apms_zmadex_saint_readme.txt replaced with a
    description of what this particular RO-Crate holds
    """

    def __init__(self, theargs,
                 provenance_utils=ProvenanceUtil()):
        """
        Constructor

        :param theargs: Command line arguments that at minimum need
                        to have the following attributes:
        :type theargs: :py:class:`~python.argparse.Namespace`
        """
        super().__init__()
        self._outdir = os.path.abspath(theargs.outdir)
        self._inputs = theargs.inputs
        self._name = theargs.name
        self._organization_name = theargs.organization_name
        self._project_name = theargs.project_name
        self._release = theargs.release
        self._cell_line = theargs.cell_line
        self._treatment = theargs.treatment
        self._tissue = theargs.tissue
        self._author = theargs.author
        self._gene_set = theargs.gene_set
        self._baitcolname = theargs.baitcolname
        self._set_name = theargs.set_name
        self._input_format = getattr(theargs, 'input_format',
                                     APMSDataLoader.LEGACY_FORMAT)
        self._drug = getattr(theargs, 'drug', None)
        self._drug_effect_input = getattr(theargs, 'drug_effect_input', None)
        self._drug_effect_rows = getattr(theargs, 'drug_effect_rows',
                                         APMSDataLoader.DRUG_EFFECT_ROWS_ALL)
        self._exclude_baits = getattr(theargs, 'exclude_baits', ['MDA'])
        self._filter = getattr(theargs, 'filter',
                               APMSDataLoader.FILTER_ANY_PASS)
        self._no_unfiltered = getattr(theargs, 'no_unfiltered', False)
        self._provenance_utils = provenance_utils
        self._softwareid = None
        self._input_data_dict = theargs.__dict__
        self._qc = {}

    def run(self):
        """
        Run method to create RO-Crate from AP-MS data tables. This process involves merging input tables,
        registering the dataset and related software in the RO-Crate.

        :return:
        """
        self._validate_args()
        self._generate_rocrate_dir_path()
        if os.path.exists(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        logger.debug('Creating directory ' + str(self._outdir))
        os.makedirs(self._outdir, mode=0o755)

        keywords = [self._project_name, self._release,
                    self._cell_line, self._treatment, self._tissue,
                    'AP-MS edgelist']

        if self._gene_set is not None:
            keywords.append(self._gene_set)

        description = ' '.join(keywords)

        info_dict = {
            constants.DATASET_NAME: self._name,
            constants.DATASET_ORGANIZATION_NAME: self._organization_name,
            constants.DATASET_PROJECT_NAME: self._project_name,
            constants.DATASET_RELEASE: self._release,
            constants.DATASET_CELL_LINE: self._cell_line,
            constants.DATASET_TREATMENT: self._treatment,
            constants.DATASET_TISSUE: self._tissue,
            constants.DATASET_AUTHOR: self._author,
            constants.DATASET_GENE_SET: self._gene_set
        }

        self.save_dataset_info_to_json(self._outdir, info_dict, constants.DATASET_INFO_FILE)

        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description=description,
                                                keywords=keywords,
                                                guid=self._get_fairscape_id())
        gen_dsets = []

        if self._input_format == APMSDataLoader.ZMADEX_SAINT_FORMAT:
            gen_dsets.extend(self._run_zmadex_saint(description=description,
                                                    keywords=keywords))
        else:
            file_path = self._merge_and_save_apms_data()
            file_desc = description + ' AP-MS file'
            file_keywords = keywords.copy()
            file_keywords.extend(['file'])
            dset_id = self._provenance_utils.register_dataset(rocrate_path=self._outdir, source_file=file_path,
                                                              skip_copy=True,
                                                              data_dict={'name': ' AP-MS file',
                                                                         'description': file_desc,
                                                                         'keywords': file_keywords,
                                                                         'data-format': 'tsv',
                                                                         'author': self._author,
                                                                         'version': self._release,
                                                                         'date-published': date.today().strftime('%Y-%m-%d')},
                                                              guid=self._get_fairscape_id())
            gen_dsets.append(dset_id)
        self._register_software(keywords=keywords, description=description)
        self._register_computation(generated_dataset_ids=gen_dsets,
                                   description=description,
                                   keywords=keywords)
        self._copy_over_apms_readme()
        return 0

    def _validate_args(self):
        """
        Checks the combination of command line flags makes sense before
        any directory is created

        :raises CellMapsError: if the flags are contradictory
        """
        if self._input_format not in APMSDataLoader.INPUT_FORMATS:
            raise CellMapsError('--input_format must be one of ' +
                                str(APMSDataLoader.INPUT_FORMATS) +
                                ' received: ' + str(self._input_format))

        if self._input_format == APMSDataLoader.LEGACY_FORMAT:
            if self._drug_effect_input is not None:
                raise CellMapsError('--drug_effect_input is only supported '
                                    'with --input_format ' +
                                    APMSDataLoader.ZMADEX_SAINT_FORMAT)
            return

        if self._inputs is None or len(self._inputs) != 1:
            raise CellMapsError('--input_format ' +
                                APMSDataLoader.ZMADEX_SAINT_FORMAT +
                                ' expects exactly one --inputs file, received: ' +
                                str(self._inputs))

        if self._drug is None:
            raise CellMapsError('--drug is required with --input_format ' +
                                APMSDataLoader.ZMADEX_SAINT_FORMAT)

        if self._filter not in APMSDataLoader.FILTER_MODES:
            raise CellMapsError('--filter must be one of ' +
                                str(list(APMSDataLoader.FILTER_MODES.keys())) +
                                ' received: ' + str(self._filter))

        if self._drug_effect_rows not in APMSDataLoader.DRUG_EFFECT_ROWS_CHOICES:
            raise CellMapsError('--drug_effect_rows must be one of ' +
                                str(APMSDataLoader.DRUG_EFFECT_ROWS_CHOICES) +
                                ' received: ' + str(self._drug_effect_rows))

        if self._drug_effect_input is None:
            if self._drug_effect_rows != APMSDataLoader.DRUG_EFFECT_ROWS_ALL:
                raise CellMapsError('--drug_effect_rows has nothing to act on '
                                    'without --drug_effect_input')
        elif self._drug == 'DMSO':
            logger.warning('--drug_effect_input was passed with --drug DMSO. '
                           'The MSstats contrast is vorinostat versus DMSO, so '
                           'it normally belongs with the treated arm only')

        expected_treatment = APMSDataLoader.DRUG_TO_TREATMENT.get(self._drug)
        if expected_treatment is not None and expected_treatment != self._treatment:
            logger.warning('--drug ' + str(self._drug) + ' is usually paired '
                           'with --treatment ' + expected_treatment +
                           ' but --treatment is ' + str(self._treatment))

    def _run_zmadex_saint(self, description='', keywords=None):
        """
        Writes and registers every file of a Zmadex/SAINT RO-Crate.

        The two inputs are never merged. The AP-MS tables are built from the
        Zmadex/SAINT file and the drug effect table from the MSstats file,
        the only thing passing between them is a key set used by the
        ``--drug_effect_rows`` restriction.

        :return: ids of registered datasets
        :rtype: list
        """
        keywords = [] if keywords is None else keywords
        gen_dsets = []

        saint_df = self._load_zmadex_saint()
        arm_df = self._select_drug_arm(saint_df)
        filtered_df = self._apply_filter(arm_df)

        if len(filtered_df) == 0:
            raise CellMapsError('Filter ' + str(self._filter) + ' left no rows '
                                'for --drug ' + str(self._drug) +
                                '. Refusing to write an empty ' +
                                constants.APMS_TSV_FILE)

        gen_dsets.append(self._write_and_register(filtered_df,
                                                  constants.APMS_TSV_FILE,
                                                  name='AP-MS file',
                                                  desc=description + ' AP-MS file',
                                                  keywords=keywords))

        if not self._no_unfiltered:
            gen_dsets.append(self._write_and_register(arm_df,
                                                      constants.APMS_UNFILTERED_TSV_FILE,
                                                      name='AP-MS unfiltered file',
                                                      desc=description +
                                                           ' complete pre-filter AP-MS matrix, '
                                                           'same schema as ' +
                                                           constants.APMS_TSV_FILE,
                                                      keywords=keywords))

        if self._drug_effect_input is not None:
            drug_df = self._load_msstats()
            drug_df = self._restrict_drug_effect(drug_df, arm_df, filtered_df)
            self._check_drug_effect_coverage(filtered_df, drug_df)
            gen_dsets.append(self._write_and_register(drug_df,
                                                      constants.APMS_DRUG_EFFECT_TSV_FILE,
                                                      name='AP-MS drug effect file',
                                                      desc=description +
                                                           ' MSstats vorinostat versus DMSO '
                                                           'contrast keyed on Batch, Bait and '
                                                           'Prey. Not an interaction table',
                                                      keywords=keywords))

        self._check_gene_set(arm_df)
        gen_dsets.append(self._write_qc(description=description,
                                        keywords=keywords))
        return gen_dsets

    def _read_table(self, input_file):
        """
        Reads **input_file** keeping every value as text so the floats in
        the source round trip unchanged and blanks stay blank

        :return: contents of file
        :rtype: :py:class:`pandas.DataFrame`
        """
        thesep = ',' if input_file.endswith('.csv') else '\t'
        return pd.read_csv(input_file, sep=thesep, dtype=str, na_filter=False)

    def _load_zmadex_saint(self):
        """
        Loads the Zmadex/SAINT file and renames its columns to the
        normalized AP-MS schema

        :raises CellMapsError: if a required column is missing
        :rtype: :py:class:`pandas.DataFrame`
        """
        df = self._read_table(self._inputs[0])
        required = list(APMSDataLoader.ZMADEX_SAINT_COL_MAP.keys())
        required.append(APMSDataLoader.DRUG_COL)
        missing = [x for x in required if x not in df.columns]
        if len(missing) > 0:
            raise CellMapsError('Zmadex/SAINT input ' + str(self._inputs[0]) +
                                ' is missing required column(s): ' + str(missing))
        self._qc['zmadex_saint_input_file'] = os.path.basename(self._inputs[0])
        self._qc['zmadex_saint_input_rows'] = len(df)
        return df.rename(columns=APMSDataLoader.ZMADEX_SAINT_COL_MAP)

    def _select_drug_arm(self, df):
        """
        Selects the rows matching ``--drug`` and drops the drug column,
        leaving the schema identical for every treatment

        :raises CellMapsError: if the drug is absent or the key is not unique
        :rtype: :py:class:`pandas.DataFrame`
        """
        found_drugs = sorted(df[APMSDataLoader.DRUG_COL].unique())
        self._qc['drugs_in_input'] = found_drugs
        unexpected = [x for x in found_drugs
                      if x not in APMSDataLoader.KNOWN_DRUGS]
        if len(unexpected) > 0:
            logger.warning('Unexpected value(s) in ' +
                           APMSDataLoader.DRUG_COL + ' column: ' +
                           str(unexpected))
        if self._drug not in found_drugs:
            raise CellMapsError('--drug ' + str(self._drug) + ' not found in ' +
                                APMSDataLoader.DRUG_COL + ' column. Found: ' +
                                str(found_drugs))

        arm_df = df[df[APMSDataLoader.DRUG_COL] == self._drug]
        arm_df = arm_df[APMSDataLoader.APMS_COLS].reset_index(drop=True)

        dupes = int(arm_df.duplicated(APMSDataLoader.KEY_COLS).sum())
        if dupes > 0:
            raise CellMapsError(str(dupes) + ' duplicate ' +
                                str(APMSDataLoader.KEY_COLS) + ' row(s) found '
                                'for --drug ' + str(self._drug))
        self._qc['drug_arm'] = self._drug
        self._qc['apms_rows_before_filter'] = len(arm_df)
        self._qc['apms_duplicate_keys'] = dupes
        for colname in APMSDataLoader.PASS_COLS:
            self._qc[colname + '_true'] = int((arm_df[colname] ==
                                               APMSDataLoader.TRUE_VAL).sum())
        self._qc['apms_rows_with_blank_scores'] = int((arm_df['Zmadex'] == '').sum())
        return arm_df

    def _apply_filter(self, df):
        """
        Keeps rows holding ``TRUE`` in any column the ``--filter`` mode names.

        Blanks need no special handling, an empty string is simply not
        ``TRUE``, which is why the frame is read with ``dtype=str`` and
        ``na_filter=False``

        :rtype: :py:class:`pandas.DataFrame`
        """
        cols = APMSDataLoader.FILTER_MODES[self._filter]
        self._qc['filter'] = self._filter
        if len(cols) == 0:
            self._qc['apms_rows_after_filter'] = len(df)
            return df
        filtered_df = df[(df[cols] == APMSDataLoader.TRUE_VAL).any(axis=1)]
        filtered_df = filtered_df.reset_index(drop=True)
        self._qc['apms_rows_after_filter'] = len(filtered_df)
        logger.info('Filter ' + str(self._filter) + ' kept ' +
                    str(len(filtered_df)) + ' of ' + str(len(df)) + ' rows')
        return filtered_df

    def _load_msstats(self):
        """
        Loads the MSstats file, drops the excluded baits and renames the
        columns to the normalized drug effect schema.

        Protein groups are counted and written through unchanged. Exploding
        them gains 0.55% more keys while creating tens of thousands of
        ambiguous ones, and every key that survives the AP-MS filter is
        already covered without it

        :raises CellMapsError: if a required column is missing
        :rtype: :py:class:`pandas.DataFrame`
        """
        df = self._read_table(self._drug_effect_input)
        missing = [x for x in APMSDataLoader.MSSTATS_COL_MAP
                   if x not in df.columns]
        if len(missing) > 0:
            raise CellMapsError('MSstats input ' + str(self._drug_effect_input) +
                                ' is missing required column(s): ' + str(missing))
        self._qc['msstats_input_file'] = os.path.basename(self._drug_effect_input)
        self._qc['msstats_input_rows'] = len(df)

        excluded = {}
        for bait in self._exclude_baits:
            excluded[bait] = int((df['Bait'] == bait).sum())
            df = df[df['Bait'] != bait]
        self._qc['msstats_rows_excluded_by_bait'] = excluded
        self._qc['msstats_rows_after_bait_exclusion'] = len(df)

        self._qc['msstats_protein_group_rows'] = int(df['Protein'].str.contains(';').sum())

        unexpected = [x for x in sorted(df['Effect'].unique())
                      if x not in APMSDataLoader.KNOWN_DRUG_EFFECTS]
        if len(unexpected) > 0:
            logger.warning('Unexpected value(s) in Effect column: ' +
                           str(unexpected))

        df = df.rename(columns=APMSDataLoader.MSSTATS_COL_MAP)
        df = df[APMSDataLoader.DRUG_EFFECT_COLS].reset_index(drop=True)
        self._qc['drug_effect_categories'] = {str(k): int(v) for k, v in
                                              df['DrugEffect'].value_counts().items()}
        return df

    def _restrict_drug_effect(self, drug_df, arm_df, filtered_df):
        """
        Applies ``--drug_effect_rows``. This is a key membership test, it
        selects rows and never adds a column or changes row multiplicity.

        ``all`` is a no-op and is the only mode computable from the MSstats
        file alone. ``apms_keys`` gives the same result as
        ``saint_universe`` when ``--filter none`` is in effect, since the
        unfiltered arm is the SAINT universe for that arm

        :rtype: :py:class:`pandas.DataFrame`
        """
        self._qc['drug_effect_rows'] = self._drug_effect_rows
        before = len(drug_df)
        self._qc['drug_effect_rows_before_restriction'] = before

        if self._drug_effect_rows == APMSDataLoader.DRUG_EFFECT_ROWS_SAINT_UNIVERSE:
            target_df = arm_df
        elif self._drug_effect_rows == APMSDataLoader.DRUG_EFFECT_ROWS_APMS_KEYS:
            target_df = filtered_df
        else:
            self._qc['drug_effect_rows_dropped_by_restriction'] = 0
            self._qc['drug_effect_rows_written'] = before
            return drug_df

        drug_keys = pd.MultiIndex.from_frame(drug_df[APMSDataLoader.KEY_COLS])
        target_keys = pd.MultiIndex.from_frame(target_df[APMSDataLoader.KEY_COLS])
        drug_df = drug_df[drug_keys.isin(target_keys)].reset_index(drop=True)

        self._qc['drug_effect_rows_dropped_by_restriction'] = before - len(drug_df)
        self._qc['drug_effect_rows_written'] = len(drug_df)
        logger.info('--drug_effect_rows ' + str(self._drug_effect_rows) +
                    ' kept ' + str(len(drug_df)) + ' of ' + str(before) + ' rows')
        return drug_df

    def _check_drug_effect_coverage(self, filtered_df, drug_df):
        """
        The only place the join between the two inputs survives. It reports
        how much of apms.tsv the drug effect table covers and writes nothing

        """
        apms_keys = pd.MultiIndex.from_frame(filtered_df[APMSDataLoader.KEY_COLS])
        drug_keys = pd.MultiIndex.from_frame(drug_df[APMSDataLoader.KEY_COLS])
        covered = int(apms_keys.isin(drug_keys).sum())
        total = len(apms_keys)
        self._qc['apms_keys'] = total
        self._qc['apms_keys_with_drug_effect'] = covered
        self._qc['apms_keys_without_drug_effect'] = total - covered
        if covered < total:
            logger.warning(str(total - covered) + ' of ' + str(total) +
                           ' rows in ' + constants.APMS_TSV_FILE +
                           ' have no match in ' +
                           constants.APMS_DRUG_EFFECT_TSV_FILE +
                           '. The two inputs may have drifted out of sync')

    def _check_gene_set(self, arm_df):
        """
        Compares the baits against the published CM4AI gene set, resolving
        legacy aliases first. Reference material, never a release gate, so
        this only warns

        """
        baits = sorted(arm_df['Bait'].unique())
        self._qc['bait_count'] = len(baits)
        gene_set = APMSDataLoader.GENE_SETS.get(self._gene_set)
        if gene_set is None:
            return
        unlisted = [x for x in baits
                    if APMSDataLoader.GENE_SET_ALIASES.get(x, x) not in gene_set]
        self._qc['baits_not_in_gene_set'] = unlisted
        if len(unlisted) > 0:
            logger.warning(str(len(unlisted)) + ' bait(s) are not on the '
                           'published ' + str(self._gene_set) + ' gene set: ' +
                           str(unlisted))

    def _write_and_register(self, df, filename, name='', desc='', keywords=None):
        """
        Writes **df** into the RO-Crate and registers it as a dataset

        :return: id of registered dataset
        :rtype: str
        """
        keywords = [] if keywords is None else keywords
        file_path = os.path.join(self._outdir, filename)
        df.to_csv(file_path, sep='\t', index=False)
        logger.info('Wrote ' + str(len(df)) + ' rows to ' + file_path)
        file_keywords = keywords.copy()
        file_keywords.extend(['file'])
        return self._provenance_utils.register_dataset(rocrate_path=self._outdir,
                                                       source_file=file_path,
                                                       skip_copy=True,
                                                       data_dict={'name': name,
                                                                  'description': desc,
                                                                  'keywords': file_keywords,
                                                                  'data-format': 'tsv',
                                                                  'author': self._author,
                                                                  'version': self._release,
                                                                  'date-published': date.today().strftime('%Y-%m-%d')},
                                                       guid=self._get_fairscape_id())

    def _write_qc(self, description='', keywords=None):
        """
        Writes the QC/summary statistics file and registers it

        :return: id of registered dataset
        :rtype: str
        """
        keywords = [] if keywords is None else keywords
        qc_path = os.path.join(self._outdir, constants.APMS_QC_FILE)
        with open(qc_path, 'w') as f:
            json.dump(self._qc, f, indent=2, sort_keys=True)
        logger.info('AP-MS summary: ' + json.dumps(self._qc, sort_keys=True))
        file_keywords = keywords.copy()
        file_keywords.extend(['file'])
        qc_desc = description + ' AP-MS summary statistics'
        return self._provenance_utils.register_dataset(rocrate_path=self._outdir,
                                                       source_file=qc_path,
                                                       skip_copy=True,
                                                       data_dict={'name': 'AP-MS QC file',
                                                                  'description': qc_desc,
                                                                  'keywords': file_keywords,
                                                                  'data-format': 'json',
                                                                  'author': self._author,
                                                                  'version': self._release,
                                                                  'date-published': date.today().strftime('%Y-%m-%d')},
                                                       guid=self._get_fairscape_id())

    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _get_dataset_summary(self):
        """
        Builds the description of what this RO-Crate actually holds, so the
        readme reports the filter and row set that were used rather than a
        hard coded guess

        :rtype: str
        """
        lines = ['Contents of this RO-Crate',
                 '-------------------------',
                 '',
                 'Treatment: ' + str(self._treatment) +
                 ' (drug arm ' + str(self._drug) + ')',
                 '',
                 constants.APMS_TSV_FILE + ': ' +
                 str(self._qc.get('apms_rows_after_filter', 'unknown')) +
                 ' rows, filtered with --filter ' + str(self._filter) +
                 ' from ' + str(self._qc.get('apms_rows_before_filter', 'unknown')) +
                 ' rows.']
        if self._no_unfiltered:
            lines.append('')
            lines.append('This RO-Crate does not include ' +
                         constants.APMS_UNFILTERED_TSV_FILE + '.')
        else:
            lines.append('')
            lines.append(constants.APMS_UNFILTERED_TSV_FILE + ': ' +
                         str(self._qc.get('apms_rows_before_filter', 'unknown')) +
                         ' rows, the complete pre-filter matrix with the '
                         'identical schema. Nothing is dropped from it.')

        lines.append('')
        if self._drug_effect_input is None:
            lines.append('This RO-Crate has no ' +
                         constants.APMS_DRUG_EFFECT_TSV_FILE + ' by design. The '
                         'MSstats contrast is vorinostat versus DMSO, so it is '
                         'published with the vorinostat RO-Crate only.')
        else:
            lines.append(constants.APMS_DRUG_EFFECT_TSV_FILE + ': ' +
                         str(self._qc.get('drug_effect_rows_written', 'unknown')) +
                         ' rows, selected with --drug_effect_rows ' +
                         str(self._drug_effect_rows) + '.')
            if self._drug_effect_rows == APMSDataLoader.DRUG_EFFECT_ROWS_ALL:
                lines.append('')
                lines.append('This is the complete MSstats output minus the '
                             'excluded bait(s) ' + str(self._exclude_baits) +
                             '. It therefore holds many more rows than ' +
                             constants.APMS_TSV_FILE + ', including preys that '
                             'are not in the AP-MS tables at all.')
            lines.append('')
            lines.append('Of the ' + str(self._qc.get('apms_keys', 'unknown')) +
                         ' rows in ' + constants.APMS_TSV_FILE + ', ' +
                         str(self._qc.get('apms_keys_with_drug_effect', 'unknown')) +
                         ' have a drug effect record.')
        return '\n'.join(lines)

    def _copy_over_apms_readme(self):
        """
        Copies over the readme matching the input format. A reader of a given
        RO-Crate should see only the columns that RO-Crate holds

        """
        if self._input_format == APMSDataLoader.ZMADEX_SAINT_FORMAT:
            src = os.path.join(os.path.dirname(__file__),
                               'apms_zmadex_saint_readme.txt')
            with open(src, 'r') as f:
                readme = f.read()
            readme = readme.replace(APMSDataLoader.SUMMARY_MARKER,
                                    self._get_dataset_summary())
            with open(os.path.join(self._outdir, 'readme.txt'), 'w') as f:
                f.write(readme)
            return
        apms_readme = os.path.join(os.path.dirname(__file__), 'apms_readme.txt')
        shutil.copy(apms_readme, os.path.join(self._outdir, 'readme.txt'))

    def _generate_rocrate_dir_path(self):
        """
        Generates a directory path for the RO-Crate based on provided metadata like project name, gene set,
        cell line, treatment, and release version.
        """
        dir_name = self._project_name.lower() + '_'
        if self._gene_set is not None:
            dir_name += self._gene_set.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += self._treatment.lower()
        if self._set_name is not None:
            dir_name += '_' + self._set_name
        dir_name += '_apms_'
        dir_name += self._release.lower()
        dir_name = dir_name.replace(' ', '_')
        self._outdir = os.path.join(self._outdir, dir_name)

    def _merge_and_save_apms_data(self):
        """
        Merges AP-MS data from input files into a single DataFrame and saves the combined data to a TSV file within
        the RO-Crate directory.

        :return: The file path to the saved AP-MS data TSV file.
        """
        df_list = []
        for input in self._inputs:
            thesep = '\t'
            if input.endswith('.csv'):
                thesep = ','
            cur_df = pd.read_csv(input, sep=thesep, na_filter=False)
            if self._baitcolname != 'Bait':
                if self._baitcolname in cur_df.columns:
                    cur_df.rename({self._baitcolname: 'Bait'}, axis=1, inplace=True)
            # Handles case where HDAC2 in initial cm4ai dataset
            # had several columns lacking .x suffix
            # we are fixing this by checking for those columns and if
            # found just renaming them in place
            for colname in ['PreyGene', 'NumReplicates', 'AvgP',
                            'MaxP', 'TopoAvgP', 'TopoMaxP',
                            'SaintScore', 'FoldChange', 'BFDR',
                            'boosted_by']:
                if colname in cur_df.columns:
                    if colname + '.x' in cur_df.columns:
                        cur_df.drop(columns=colname + '.x', inplace=True)
                    cur_df.rename({colname: colname + '.x'}, axis=1, inplace=True)

            df_list.append(cur_df)

        df = pd.concat(df_list)

        apms_path = os.path.join(self._outdir, constants.APMS_TSV_FILE)

        df.to_csv(apms_path, sep='\t', index=False)
        return apms_path

    def _register_computation(self, generated_dataset_ids=[],
                              description='',
                              keywords=[]):
        """
        Registers the computation process in the RO-Crate
        # Todo: added in used dataset, software and what is being generated
        :return:
        """
        logger.debug('Getting id of input rocrate')
        comp_keywords = keywords.copy()
        comp_keywords.extend(['computation'])
        description = description + ' run of ' + cellmaps_utils.__name__
        self._provenance_utils.register_computation(self._outdir,
                                                    name='AP-MS',
                                                    run_by=str(self._provenance_utils.get_login()),
                                                    command=str(self._input_data_dict),
                                                    description=description,
                                                    keywords=comp_keywords,
                                                    used_software=[self._softwareid],
                                                    generated=generated_dataset_ids,
                                                    guid=self._get_fairscape_id())

    def _register_software(self, description='',
                           keywords=[]):
        """
        Registers this tool

        :raises CellMapsImageEmbeddingError: If fairscape call fails
        """
        software_keywords = keywords.copy()
        software_keywords.extend(['tools', cellmaps_utils.__name__])
        software_description = description + ' ' + \
                               cellmaps_utils.__description__
        self._softwareid = self._provenance_utils.register_software(self._outdir,
                                                                    name=cellmaps_utils.__name__,
                                                                    description=software_description,
                                                                    author=cellmaps_utils.__author__,
                                                                    version=cellmaps_utils.__version__,
                                                                    file_format='py',
                                                                    keywords=software_keywords,
                                                                    url=cellmaps_utils.__repo_url__,
                                                                    guid=self._get_fairscape_id())

    def add_subparser(subparsers):
        """
        Adds a command-line subparser for the APMSDataLoader tool.

        :return:
        """
        desc = """

        Version {version}

        {cmd} Loads AP-MS data into a RO-Crate
        """.format(version=cellmaps_utils.__version__,
                   cmd=APMSDataLoader.COMMAND)

        parser = subparsers.add_parser(APMSDataLoader.COMMAND,
                                       help='Loads AP-MS data into a RO-Crate',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument('--inputs', required=True, nargs="+",
                            help='One or more table files with the following '
                                 'fields: [Bait, Prey] and for filtering also '
                                 'containing [BFDR.x, logOddsScore')
        parser.add_argument('--input_format',
                            choices=APMSDataLoader.INPUT_FORMATS,
                            default=APMSDataLoader.LEGACY_FORMAT,
                            help='Format of --inputs. "' +
                                 APMSDataLoader.LEGACY_FORMAT + '" merges the '
                                 'original SAINT tables unchanged. "' +
                                 APMSDataLoader.ZMADEX_SAINT_FORMAT + '" expects '
                                 'exactly one Zmadex/SAINT table and requires --drug')
        parser.add_argument('--drug', choices=APMSDataLoader.KNOWN_DRUGS,
                            help='Treatment arm to select from the drug column '
                                 'of a Zmadex/SAINT input. Required with '
                                 '--input_format ' +
                                 APMSDataLoader.ZMADEX_SAINT_FORMAT)
        parser.add_argument('--drug_effect_input',
                            help='MSstats drug effect table. Written to ' +
                                 constants.APMS_DRUG_EFFECT_TSV_FILE + ' as its '
                                 'own file so ' + constants.APMS_TSV_FILE +
                                 ' keeps the same schema in every RO-Crate. The '
                                 'contrast is vorinostat versus DMSO, so pass '
                                 'this on the treated run only')
        parser.add_argument('--drug_effect_rows',
                            choices=APMSDataLoader.DRUG_EFFECT_ROWS_CHOICES,
                            default=APMSDataLoader.DRUG_EFFECT_ROWS_ALL,
                            help='Which MSstats rows to publish. "all" is the '
                                 'complete table minus --exclude_baits, '
                                 '"saint_universe" keeps rows whose key is in '
                                 'the drug arm, "apms_keys" keeps rows whose key '
                                 'is in the written ' + constants.APMS_TSV_FILE)
        parser.add_argument('--exclude_baits', nargs='+', default=['MDA'],
                            help='Bait(s) to drop from --drug_effect_input. The '
                                 'default is the parental cell line control')
        parser.add_argument('--filter',
                            choices=list(APMSDataLoader.FILTER_MODES.keys()),
                            default=APMSDataLoader.FILTER_ANY_PASS,
                            help='Rows to keep in ' + constants.APMS_TSV_FILE +
                                 '. "none" writes the complete matrix. Applies '
                                 'to the AP-MS tables only, never to ' +
                                 constants.APMS_DRUG_EFFECT_TSV_FILE)
        parser.add_argument('--no_unfiltered', action='store_true',
                            help='Do not write ' +
                                 constants.APMS_UNFILTERED_TSV_FILE)
        parser.add_argument('--author', default='Krogan Lab',
                            help='Author that created this data')
        parser.add_argument('--name', default='AP-MS',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='Krogan Lab',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', default='CM4AI',
                            help='Name of project running this tool, needed for '
                                 'FAIRSCAPE. Usually set to funding source')
        parser.add_argument('--release', required=True,
                            help='Version of release. For example: 0.1 alpha')
        parser.add_argument('--treatment', default='untreated',
                            choices=['paclitaxel', 'vorinostat', 'untreated'],
                            help='Treatment of sample.')
        parser.add_argument('--cell_line', default='MDA-MB-468',
                            help='Name of cell line. For example MDA-MB-468')
        parser.add_argument('--gene_set', choices=['chromatin', 'metabolic'],
                            default='chromatin',
                            help='Gene set for dataset')
        parser.add_argument('--set_name',
                            help='If set, adds value to RO-Crate folder name before _apms_<version>. '
                                 'Example values set1')
        parser.add_argument('--tissue', choices=['undifferentiated', 'neuron',
                                                 'cardiomyocytes', ''],
                            default='breast; mammary gland',
                            help='Tissue for dataset. Since the default --cell_line '
                                 'is MDA-MB-468, this value is set to the tissue '
                                 'for that cell line')
        parser.add_argument('--baitcolname', default='Bait',
                            help='Name of bait column in input file(s)')

        return parser
