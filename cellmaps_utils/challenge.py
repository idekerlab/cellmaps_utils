
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
import numpy as np
import cellmaps_utils
import ndex2
from ndex2.cx2 import RawCX2NetworkFactory, CX2NetworkXFactory

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
    Writes out a pandas dataframe in tab separated
    format with a header and no index

    :param df: data to write
    :type df: :py:class:`pandas.DataFrame`
    :param outfile: destination file path
    :type outfile: str
    """
    df.to_csv(outfile, index=False, sep='\t', header=True)


def get_col_repl_map(prefix=None, columns=None, idcol='xxx'):
    """
    Given a list of strings in **columns** create a
    dict where the key is the value from **columns**
    and the value is the **prefix** prepended to the value
    from the **columns**

    :param prefix:
    :type prefix: str
    :param columns:
    :type columns: list
    :return: column name => prefix + column name unless column name
             matches **idcol** in which case do not add prefix
    :rtype: dict
    """
    if prefix is None:
        raise CellMapsError('prefix is None')
    if columns is None:
        raise CellMapsError('columns is None')
    if idcol is None:
        raise CellMapsError('idcol is None')

    cmap = {}
    for c in columns:
        if c == idcol:
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


def merge_uniprot_gene_mapping(file1, file2, mapped_column, col_name='PG.Genes'):
    df1 = pd.read_table(file1)
    df2 = pd.read_table(file2)
    df1_filtered = df1[[mapped_column, col_name]]
    df2_filtered = df2[[mapped_column, col_name]]

    merged_df = pd.concat([df1_filtered, df2_filtered], ignore_index=True)

    uniprot_gene_dict = {}
    gene_uniprot_dict = {}
    for _, row in merged_df.iterrows():
        uniprot_ids = row[mapped_column].split(";")
        gene_names = row[col_name].split(";")

        for uniprot_id, gene_name in zip(uniprot_ids, gene_names):
            uniprot_gene_dict[uniprot_id] = gene_name
            gene_uniprot_dict[gene_name] = uniprot_id

    return uniprot_gene_dict, gene_uniprot_dict


def get_network(uuid_of_net):
    client = ndex2.client.Ndex2()
    factory = RawCX2NetworkFactory()
    client_resp = client.get_network_as_cx2_stream(uuid_of_net)
    net = factory.get_cx2network(json.loads(client_resp.content))
    return net


def get_system_to_gene_count(gene_to_system_mapping):
    """
    Given a dict of gene => [ node ids ]
    this function returns a new dict
    where key is node id aka system and value is count of genes
    in that system: node id => count of genes

    :param gene_to_system_mapping: gene => [ node ids ]
    :type gene_to_system_mapping: dict
    :return: node id => count of genes
    :rtype: dict
    """
    system_to_gene_count = {}
    for gene, systems in gene_to_system_mapping.items():
        for system in set(systems):
            if system in system_to_gene_count:
                system_to_gene_count[system] += 1
            else:
                system_to_gene_count[system] = 1
    return system_to_gene_count


def get_genes_and_uniprots(forward_dict, uniprot_gene_dict):
    uniprots = None
    if uniprot_gene_dict is None:
        genes = list(forward_dict.keys())
    else:
        uniprots = list(forward_dict.keys())
        genes = []
        for uniprot in uniprots:
            gene = uniprot_gene_dict.get(uniprot, None)
            if gene:
                genes.append(gene)
    return genes, uniprots


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


class SolutionGenerator(BaseCommandLineTool):
    """
    Creates solution from a challenge dataset
    """
    COMMAND = 'solutiongenerator'

    SOURCE = 'source'
    COL_NAME = 'col_name'
    PREFIX = 'prefix'
    MINSIZE = 'minsize'
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
        self._input = theargs.input
        self._id_mapping_file = os.path.join(self._input, theargs.id_mapping_file)
        self._standards = theargs.standards
        self._provenance_utils = provenance_utils
        self._softwareid = None
        self._input_data_dict = theargs.__dict__

    def _get_uniprot_gene_dicts(self):
        """

        :return:
        """
        with open(self._id_mapping_file, "r") as file:
            data = json.load(file)

        repl1 = data.get("repl1.tsv", None)
        repl2 = data.get("repl2.tsv", None)
        uniprot_gene_dict = None
        gene_uniprot_dict = {}
        if repl1 and repl2:
            mapped_column = data.get("mapped_column_name", "PG.ProteinAccessions")  # "PG.ProteinAccessions"
            dir_path = os.path.dirname(self._id_mapping_file)
            uniprot_gene_dict, gene_uniprot_dict = merge_uniprot_gene_mapping(os.path.join(dir_path, repl1),
                                                                              os.path.join(dir_path, repl2),
                                                                              mapped_column)
        return uniprot_gene_dict, gene_uniprot_dict, data.get('forward', {})

    def _get_gene_to_system_mapping_from_network(self, genes_column=None, net=None, minsize=4, genes=None,
                                                 uniprots=None, gene_uniprot_dict=None, prefix=None):
        """

        :return:
        """
        nodes_to_remove = []
        gene_to_system_mapping = {}
        for node_id, node_obj in net.get_nodes().items():
            if genes_column not in node_obj['v']:
                nodes_to_remove.append(node_id)
                continue
            gene_names = node_obj['v'].get(genes_column, [])
            if isinstance(gene_names, str):
                gene_names = gene_names.split(',')
            if len(gene_names) < minsize:
                nodes_to_remove.append(node_id)
                continue

            if not all(gene in genes for gene in gene_names):
                nodes_to_remove.append(node_id)
            else:
                for gene in gene_names:
                    if gene in genes:
                        if uniprots:
                            gene_to_system_mapping.setdefault(gene_uniprot_dict[gene], []).append(prefix + str(node_id))
                        else:
                            gene_to_system_mapping.setdefault(gene, []).append(prefix + str(node_id))
        return gene_to_system_mapping

    def _get_gene_to_system_mapping(self, genes=None, uniprots=None, gene_uniprot_dict=None,
                                    source=None,
                                   prefix=None):
        gene_to_system_mapping = {}

        df = pd.read_csv(source)
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)

        for system in df.columns:
            for gene in df[system].dropna().values:
                if gene in genes:
                    if uniprots:
                        gene_to_system_mapping.setdefault(gene_uniprot_dict[gene], []).append(prefix + str(system))
                    else:
                        gene_to_system_mapping.setdefault(gene, []).append(prefix + (system))

        return gene_to_system_mapping

    def _generate_solution_for_standard(self, uniprot_gene_dict=None, gene_uniprot_dict=None,
                                        forward_dict=None, source=None, genes_column=None,
                                        minsize=4, prefix=''):
        """

        :return:
        """
        genes, uniprots = get_genes_and_uniprots(forward_dict, uniprot_gene_dict)

        if os.path.isfile(source):
            gene_to_system_mapping = self._get_gene_to_system_mapping(uniprots=uniprots, genes=genes,
                                                                      gene_uniprot_dict=gene_uniprot_dict,
                                                                      source=source, prefix=prefix)
        else:
            gene_to_system_mapping = self._get_gene_to_system_mapping_from_network(genes_column=genes_column,
                                                                                   minsize=minsize,
                                                                                   genes=genes,
                                                                                   gene_uniprot_dict=gene_uniprot_dict,
                                                                                   prefix=prefix,
                                                                                   net=get_network(source),
                                                                                   uniprots=uniprots)

        system_to_gene_count = get_system_to_gene_count(gene_to_system_mapping)

        systems_too_small = set()
        for system, cnt in system_to_gene_count.items():
            if cnt < minsize:
                systems_too_small.add(system)

        self._write_solution(outfile=os.path.join(self._outdir, prefix + '_solution.csv'),
                             systems_too_small=systems_too_small, forward_dict=forward_dict,
                             gene_to_system_mapping=gene_to_system_mapping)

        self._remove_too_small_systems(systems_too_small=systems_too_small,
                                       system_to_gene_count=system_to_gene_count)

        # Convert the values to a list
        gene_counts = list(system_to_gene_count.values())
        # Calculate mean and variance
        mean_gene_count = np.mean(gene_counts)
        variance_gene_count = np.var(gene_counts)

        with open(os.path.join(self._outdir, prefix + '_readme.txt'), 'w') as f:
            f.write(f"Mean number of genes per system: {mean_gene_count}\n")
            f.write(f"Variance of number of genes per system: {variance_gene_count}\n")

        with open(os.path.join(self._outdir, prefix + '_systemsizes.json'), 'w') as f:
            json.dump(system_to_gene_count, f)

    def _remove_too_small_systems(self, systems_too_small=None,
                                  system_to_gene_count=None):
        """

        :param systems_to_small:
        :param system_to_gene_count:
        :return:
        """
        # remove the too small systems for stats
        for system in systems_too_small:
            del system_to_gene_count[system]

    def _write_solution(self, outfile=None, gene_to_system_mapping=None,
                        forward_dict=None,
                        systems_too_small=set()):
        """

        :return:
        """
        cntr = 1
        with open(outfile, 'w') as f:
            f.write("id,xxx,solution,Usage\n")
            for gene, systems in gene_to_system_mapping.items():
                for system in set(systems):
                    if system in systems_too_small:
                        continue
                    f.write(f"{cntr},{forward_dict[gene]},{system},Public\n")
                    cntr += 1

    def _get_combined_solution(self):
        """
        Looks in output directory for all _solution.csv files and
        creates a new solution file concating the entries and resetting
        id column values to start from 1 and go to N
        :return:
        """
        dframes = []
        for entry in os.listdir(self._outdir):
            fp = os.path.join(self._outdir, entry)
            if not os.path.isfile(fp):
                continue
            if not entry.endswith('_solution.csv'):
                continue
            dframes.append(pd.read_csv(fp))
        df = pd.concat(dframes, ignore_index=True)
        df['id'] = df.index
        return df

    def _write_combined_solution(self, df):
        """
        Writes **df** as a CSV file
        :param df:
        :type df: :py:class:`pandas.DataFrame`
        """
        df.to_csv(os.path.join(self._outdir, 'combined_sol.csv'),
                  index=False, header=True)

    def run(self):
        """


        :return:
        """
        self._generate_rocrate_dir_path()
        if os.path.exists(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        logger.debug('Creating directory ' + str(self._outdir))
        os.makedirs(self._outdir, mode=0o755)


        self._provenance_utils.register_rocrate(self._outdir,
                                                name=os.path.basename(self._input) + ' solution',
                                                organization_name='NEED TO SET THIS',
                                                project_name='NEED TO SET THIS',
                                                description='NEED TO SET THIS',
                                                keywords=['solution'],
                                                guid=self._get_fairscape_id())

        uniprot_gene_dict, gene_uniprot_dict, forward_dict = self._get_uniprot_gene_dicts()

        for entry in self._get_standards_as_dicts():
            #uniprot_gene_dict = None, gene_uniprot_dict = None,
            #forward_dict = None, source = None, genes_column = None,
            #minsize = 4, prefix = ''
            self._generate_solution_for_standard(uniprot_gene_dict=uniprot_gene_dict,
                                                 gene_uniprot_dict=gene_uniprot_dict,
                                                 forward_dict=forward_dict,
                                                 source=entry[SolutionGenerator.SOURCE],
                                                 minsize=entry[SolutionGenerator.MINSIZE],
                                                 prefix=entry[SolutionGenerator.PREFIX],
                                                 genes_column=entry[SolutionGenerator.COL_NAME])

        df = self._get_combined_solution()

        self._write_combined_solution(df)

        gen_dsets = []



        # self._register_software(keywords=keywords, description=description)
        # self._register_computation(generated_dataset_ids=gen_dsets,
        #                          description=description,
        #                           keywords=keywords)
        return 0

    def _get_standards_as_dicts(self):
        """

        :return:
        """
        for entry in self._standards:
            curstandard = re.split('\s*,\s*', entry)
            if len(curstandard) == 3:
                yield {SolutionGenerator.SOURCE: curstandard[0],
                       SolutionGenerator.PREFIX: curstandard[1],
                       SolutionGenerator.MINSIZE: int(curstandard[2]),
                       SolutionGenerator.COL_NAME: None}
            elif len(curstandard) == 4:
                yield {SolutionGenerator.SOURCE: curstandard[0],
                       SolutionGenerator.COL_NAME: curstandard[1],
                       SolutionGenerator.PREFIX: curstandard[2],
                       SolutionGenerator.MINSIZE: int(curstandard[3])}
            else:
                raise CellMapsError('Expected 4 values got: ' +
                                    str(curstandard))

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
        input_rocrate = self._provenance_utils.get_rocrate_as_dict(self._input)
        dir_name = os.path.basename(self._input) + '_solution'
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
                                                    name=SolutionGenerator.COMMAND,
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

        {cmd} Given an RO-Crate with a Challenge dataset, this
        tool creates a solution RO-Crate using standards passed
        in via --standard flag

        Each --standard should have the following fields delimited by a
        comma: <NDEx UUID | CSV file>,<COLUMN NAME>,<PREFIX>,<MINSIZE OF CLUSTER>

         <NDEx UUID | CSV file>: Either UUID of network on NDEx https://www.ndexbio.org or a path to CSV file
         <COLUMN NAME>: Name of column in network where genes reside
         <PREFIX>: Name to prefix on solution
         <MINSIZE OF CLUSTER>: Minimum number of genes needed in cluster to be included



        """.format(version=cellmaps_utils.__version__,
                   cmd=SolutionGenerator.COMMAND)

        parser = subparsers.add_parser(SolutionGenerator.COMMAND,
                                       help='Generates solution for challenge dataset',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument("--input", type=str,
                            help="Path to Challenge RO-Crate")
        parser.add_argument('--id_mapping_file', default='repl1_repl2_id_mapping.json',
                            help='Name of json file containing id mapping')
        parser.add_argument('--standards', nargs='*',
                            help=('Standards to use which is a comma delimited list'
                                  'of <NDEx UUID>,<COLUMN NAME>,<PREFIX>,<MINSIZE OF CLUSTER> or'
                                  '   <CSV FILE>,<PREFIX>,<MINSIZE OF CLUSTER>'))
        return parser

