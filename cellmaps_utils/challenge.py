
import os
import shutil
import uuid
import re
import logging
import pandas as pd
import random
import time
import string
import json
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil

logger = logging.getLogger(__name__)


REPL_ONE_TSV = 'repl1.tsv'
REPL_TWO_TSV = 'repl2.tsv'
REPL_MAPPING = 'repl1_repl2_id_mapping.json'
REPL_ONE_TWO_COMBINED = 'repl1_repl2_combined.tsv'
NEW_ID_COLNAME = 'xxx'


def get_dataframe(inputfile=None):
    """
    Loads TSV as dataframe

    :param inputfile:
    :type inputfile: str
    :return: Loaded dataframe
    :rtype: :py:class:`pandas.DataFrame`
    """
    return pd.read_csv(inputfile, sep='\t')


def get_set_of_all_values_of_column_from_dataframes(dataframes=[], col_name=None):
    """
    Iterates across all dataframes and pulls values from column specified by **col_name**

    :param dataframes: data frames
    :type dataframes: list
    :param col_name: Column where values will be obtained
    :type col_name: str
    :return: unique set of values from **col_name** column across all data frames
    :rtype: set
    """
    if dataframes is None:
        raise CellMapsError('dataframes cannot be None')

    df_list = dataframes
    if not isinstance(df_list, list):
        df_list = [dataframes]

    if col_name is None:
        raise CellMapsError('Column name must be specified')
    col_values = set()
    for df in df_list:
        col_values.update(df[col_name].unique())
    return col_values


def generate_mapping(col_vals=None, num_chars=9,
                     mapping_col_name=None,
                     input_repl_one=None,
                     input_repl_two=None):
    """
    Uses random string generator of capitalized characters and numbers
    to create a mapping of values
    in **col_vals** to another string of length **num_chars**

    Output mapping looks like:

    ```json

       { 'mapped_column_name': 'foo',
         'forward': { 'a': 'ASDFEFDDD', 'b': 'GGGHIJKOK'},
         'reverse': {'ASDFEFDDD': 'a', 'GGGHIJKOK': 'b'}
       }

    ```

    :param col_vals: Values to encode
    :type col_vals: set
    :param num_chars: length of random string
    :type num_chars: int
    :param mapping_col_name: Name of column the mapping was made for
    :type mapping_col_name: str
    :return: the mapping as a dict
    :rtype: dict
    """
    forward_mapping = {}
    new_id_set = set()
    reverse_mapping = {}
    new_rando_id = None
    for cval in col_vals:
        while new_rando_id is None or new_rando_id in new_id_set:
            new_rando_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(num_chars))
        new_id_set.add(new_rando_id)
        forward_mapping[cval] = new_rando_id
        reverse_mapping[new_rando_id] = cval
    return {'mapped_column_name': mapping_col_name,
            REPL_ONE_TSV: input_repl_one,
            REPL_TWO_TSV: input_repl_two,
            'forward': forward_mapping,
            'reverse': reverse_mapping}


def write_id_mapping_file(outdir, id_mapping=None):
    """
    Writes out mapping file as json to file with **REPL_MAPPING** as name

    See generate_mapping function for expected format of **id_mapping**

    :param outdir:
    :param id_mapping:
    :type id_mapping: dict
    :return:
    """
    with open(os.path.join(outdir, REPL_MAPPING), 'w') as f:
        json.dump(id_mapping, f, indent=2)


def set_id_col_and_rename_othercols(df=None, id_mapping=None, col_name=None,
                                    id_col_name=NEW_ID_COLNAME,
                                    cols_to_remove=['PG.ProteinGroups',
                                                    'PG.ProteinAccessions',
                                                    'PG.Genes',
                                                    'PG.UniProtIds',
                                                    'PG.ProteinNames']):
    """
    Updates DataFrame **df** so it has format of:

    ```bash
       <NEW_ID_COLNAME> 1 2 3 ... N
    ```

    :param df:
    :param id_mapping: Used
    :type id_mapping: dict
    :param col_name: Column to swap values via **id_mapping**
    :type col_name: str
    :param cols_to_remove: columns to remove
    :type cols_to_remove: list
    :param id_col_name: New name for id column
    :type id_col_name: str
    :return:
    :rtype: :py:class:`Pandas.DataFrame`
    """
    # swap values in column with new ids
    df[id_col_name] = df[col_name].replace(to_replace=id_mapping['forward'])
    for c in cols_to_remove:
        if c in df:
            df.drop(c, axis=1, inplace=True)
    col_list = df.columns.tolist()
    col_list.insert(0, col_list.pop(col_list.index(id_col_name)))

    df = df.reindex(columns=col_list)
    col_mapping = {id_col_name: id_col_name}
    cntr = 1
    for c in col_list[1:]:
        col_mapping[c] = str(cntr)
        cntr += 1
    df.rename(mapper=col_mapping, axis=1, inplace=True)

    return df


def write_tsv_file(df=None, outfile=None):
    """

    :param df:
    :param outfile:
    :return:
    """
    df.to_csv(outfile, index=False, sep='\t', header=True)


def get_col_repl_map(prefix=None, columns=None):
    """

    :param prefix:
    :param columns:
    :return:
    """
    cmap = {}
    for c in columns:
        if c == 'xxx':
            cmap[c] = c
        else:
            cmap[c] = prefix + str(c)
    return cmap

def merge_replicate_dataframes(repl1_df=None, repl2_df=None, idcol='xxx'):
    """
    Merges two replicate dataframes by outer join

    :param repl1:
    :param repl2:
    :param idcol:
    :return:
    """
    repl1_df.rename(mapper=get_col_repl_map('repl1_',
                                            columns=repl1_df.columns.tolist()),
                    inplace=True, axis=1)

    repl2_df.rename(mapper=get_col_repl_map('repl2_',
                                            columns=repl2_df.columns.tolist()),
                    inplace=True, axis=1)
    return pd.merge(repl1_df,repl2_df, on=idcol, how='outer')


class TwoReplCoelutionChallengeGenerator(BaseCommandLineTool):
    """
    Creates coelution challenge dataset suitable for Kaggle from
    raw CM4AI datasets
    """
    COMMAND = 'tworeplchallenge'

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
        self._name = theargs.name
        self._seed = theargs.seed
        self._repl1_tsv = theargs.repl1_tsv
        self._repl2_tsv = theargs.repl2_tsv
        self._mapping_col_name = theargs.mapping_col_name
        self._organization_name = theargs.organization_name
        self._project_name = theargs.project_name
        self._cell_line = theargs.cell_line
        self._tissue = theargs.tissue
        self._treatment = theargs.treatment
        self._author = theargs.author
        self._provenance_utils = provenance_utils
        self._softwareid = None
        self._input_data_dict = theargs.__dict__

    def run(self):
        """
        Runs the process of CRISPR data loading into a RO-Crate.
        It includes generating the output directory,
        linking and registering h5ad file and registering the
        computation and software used in the process.

        :return:
        """
        self._generate_rocrate_dir_path()
        if os.path.exists(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        logger.debug('Creating directory ' + str(self._outdir))
        os.makedirs(self._outdir, mode=0o755)

        keywords = [self._project_name,
                    self._cell_line, self._treatment,
                    self._tissue]


        description = ' '.join(keywords)

        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description=description,
                                                keywords=keywords,
                                                guid=self._get_fairscape_id())



        gen_dsets = []
        shutil.copy(self._repl1_tsv, self._outdir)
        shutil.copy(self._repl2_tsv, self._outdir)

        raw_repl1 = get_dataframe(self._repl1_tsv)
        raw_repl2 = get_dataframe(self._repl2_tsv)

        id_mapping = self._generate_mapping(raw_repl1, raw_repl2)

        write_id_mapping_file(self._outdir, id_mapping=id_mapping)

        repl1 = set_id_col_and_rename_othercols(raw_repl1,
                                                col_name=self._mapping_col_name,
                                                id_mapping=id_mapping)
        repl2 = set_id_col_and_rename_othercols(raw_repl2,
                                                col_name=self._mapping_col_name,
                                                id_mapping=id_mapping)
        merged_df = merge_replicate_dataframes(repl1_df=repl1, repl2_df=repl2)
        write_tsv_file(merged_df,
                       os.path.join(self._outdir, REPL_ONE_TWO_COMBINED))
        self._register_software(keywords=keywords, description=description)
        self._register_computation(generated_dataset_ids=gen_dsets,
                                   description=description,
                                   keywords=keywords)
        return 0

    def _generate_mapping(self, raw_repl1, raw_repl2):
        """

        :param raw_repl1:
        :param raw_repl2:
        :return:
        """
        col_values = get_set_of_all_values_of_column_from_dataframes([raw_repl1, raw_repl2],
                                                                     col_name=self._mapping_col_name)

        return generate_mapping(col_vals=col_values,
                                mapping_col_name=self._mapping_col_name,
                                input_repl_one=self._repl1_tsv,
                                input_repl_two=self._repl2_tsv)



    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _generate_rocrate_dir_path(self):
        """
        Generates the directory path for the RO-Crate based on project name, gene set, cell line, treatment type,
        tissue, dataset type, and release version.
        """
        dir_name = self._project_name.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += re.sub(r'[^a-zA-Z0-9\w\n\.]', '_', self._tissue.lower()) + '_'
        dir_name += self._treatment.lower()
        dir_name = dir_name.replace(' ', '_')
        self._outdir = os.path.join(self._outdir, dir_name)

    def _register_computation(self, generated_dataset_ids=[],
                              description='',
                              keywords=[]):
        """
        Registers the computation.
        # Todo: added in used dataset, software and what is being generated
        :return:
        """
        logger.debug('Getting id of input rocrate')
        comp_keywords = keywords.copy()
        comp_keywords.extend(['computation'])
        description = description + ' run of ' + cellmaps_utils.__name__
        self._provenance_utils.register_computation(self._outdir,
                                                    name=TwoReplCoelutionChallengeGenerator.COMMAND,
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
        Adds a subparser for the coleution challenge creator.

        :return:
        """
        desc = """

        Version {version}

        {cmd} Given raw coelution data, creates an RO-Crate
        with a challenge dataset containing obfuscated TSV
        file along

        """.format(version=cellmaps_utils.__version__,
                   cmd=TwoReplCoelutionChallengeGenerator.COMMAND)

        parser = subparsers.add_parser(TwoReplCoelutionChallengeGenerator.COMMAND,
                                       help='Generates coleution challenge dataset',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument('--repl1_tsv',
                            required=True,
                            help='File used to generated ' + REPL_ONE_TSV)
        parser.add_argument('--repl2_tsv',
                            required=True,
                            help='File used to generate ' + REPL_TWO_TSV)
        parser.add_argument('--mapping_col_name',
                            default='PG.ProteinAccessions',
                            help='Column to use for mapping')
        parser.add_argument('--seed',
                            default=round(time.time()),
                            help='Random seed. If unset uses current time of invocation')
        parser.add_argument('--author', default='Ideker Lab',
                            help='Author that created this data')
        parser.add_argument('--name', default='tworeplcoleution',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='Ideker Lab',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', default='tworeplcoelution_challenge',
                            help='Name of project running this tool, '
                                 'needed for FAIRSCAPE. Usually set to '
                                 'funding source')
        parser.add_argument('--treatment', default='untreated',
                            choices=['paclitaxel', 'vorinostat', 'untreated'],
                            help='Treatment of sample.')
        parser.add_argument('--cell_line', default='KOLF2.1J',
                            choices=['MDA-MB-468', 'KOLF2.1J'],
                            help='Name of cell line. For example MDA-MB-468')
        parser.add_argument('--tissue', choices=['undifferentiated', 'neuron',
                                                 'cardiomyocytes', 'breast; mammary gland'],
                            default='undifferentiated',
                            help='Tissue for dataset. Since the default --cell_line '
                                 'is MDA-MB-468, this value is set to the tissue '
                                 'for that cell line')
        return parser

