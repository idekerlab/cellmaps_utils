import json
import os
import shutil
import uuid
from datetime import date
import re
import logging
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil

logger = logging.getLogger(__name__)


class CRISPRDataLoader(BaseCommandLineTool):
    """
    Creates RO-Crate of CRISPR data from
    raw CRISPR data files
    """
    COMMAND = 'crisprconverter'

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
        self._organization_name = theargs.organization_name
        self._project_name = theargs.project_name
        self._release = theargs.release
        self._cell_line = theargs.cell_line
        self._tissue = theargs.tissue
        self._treatment = theargs.treatment
        self._author = theargs.author
        self._gene_set = theargs.gene_set
        self._h5ad = theargs.h5ad
        self._dataset = theargs.dataset
        self._skipcopy = theargs.skipcopy
        self._num_perturb_guides = theargs.num_perturb_guides
        self._num_non_target_ctrls = theargs.num_non_target_ctrls
        self._num_screen_targets = theargs.num_screen_targets
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

        keywords = [self._project_name, self._release,
                    self._cell_line, self._treatment, 'CRISPR',
                    self._tissue, self._dataset]

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
            constants.DATASET_GENE_SET: self._gene_set,
            constants.DATASET_COLLECTION_SET: self._dataset
        }
        self.save_dataset_info_to_json(self._outdir, info_dict,
                                       constants.DATASET_INFO_FILE)

        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description=description,
                                                keywords=keywords,
                                                guid=self._get_fairscape_id())
        gen_dsets = []

        gen_dsets.extend(self._link_and_register_h5ad(keywords=keywords,
                                                      description=description))
        self._register_software(keywords=keywords, description=description)
        self._register_computation(generated_dataset_ids=gen_dsets,
                                   description=description,
                                   keywords=keywords)
        self._copy_over_crispr_readme()
        return 0

    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _get_dataset_description(self):
        """
        Provides a description of the dataset based on its type (1channel or subset).

        :return: A string description of the dataset.
        :rtype: str
        """
        if self._dataset.lower() == '1channel':
            return 'FASTQs file were obtain by concatenating 3 NGS run over 7 sequencing lanes'
        elif self._dataset.lower() == 'subset':
            return 'Subset run'
        return ''

    def _link_and_register_h5ad(self, description='',
                                keywords=[]):
        """
        Processes expression file by optionally copying it to the output directory and
        registering the file in the
        RO-Crate metadata.

        :param description: A base description for the files being processed.
        :type description: str
        :param keywords: A list of keywords associated with these files for metadata purposes.
        :type keywords: list
        :return: A list of dataset identifiers for the registered expression files.
        :rtype: list
        """
        dset_ids = []

        dest_file = os.path.join(self._outdir, constants.PERTURBATION_FILE)
        if self._skipcopy is True:
            open(dest_file, 'a').close()
        else:
            self._link_or_copy(self._h5ad, dest_file)
        file_desc = description + ' file'
        file_keywords = keywords.copy()
        file_keywords.extend(['file'])
        dset_id = self._provenance_utils.register_dataset(rocrate_path=self._outdir, source_file=dest_file,
                                                          skip_copy=True,
                                                          data_dict={'name': 'Single pooled crispr screens analysis',
                                                                     'description': file_desc,
                                                                     'keywords': file_keywords,
                                                                     'data-format': 'h5ad',
                                                                     'author': self._author,
                                                                     'version': self._release,
                                                                     'date-published': date.today().strftime(
                                                                         '%Y-%m-%d')},
                                                          guid=self._get_fairscape_id())
        dset_ids.append(dset_id)

        return dset_ids

    def _link_or_copy(self, src, dest):
        """
        Attempts to hardlink src to dest and if
        that fails perform a regular copy

        :param src:
        :param dest:
        :return:
        """
        try:
            os.link(src, dest)
        except OSError as e:
            logger.warning('Falling back to copy because unable to '
                           'hardlink ' + src + ' to ' +
                           dest + ' : ' + str(e))
            shutil.copy(src, dest)

    def _create_token_replacement_map(self):
        """
        Generates a map of tokens to their respective replacement values for use in modifying the CRISPR readme file.

        :return: A dictionary where each key is a token to replace and each value is the replacement string.
        :rtype: dict
        """
        return {'@@H5AD@@': constants.PERTURBATION_FILE,
                '@@CELL_LINE@@': self._cell_line,
                '@@TREATMENT@@': self._treatment,
                '@@NUM_SCREEN_TARGETS_AND_GENE_SET@@': str(self._num_screen_targets) +
                                                       ' ' + self._gene_set,
                '@@NUM_NON_TARGET_CTRLS@@': str(self._num_non_target_ctrls),
                '@@NUM_PERTURB_GUIDES@@': str(self._num_perturb_guides)}

    def _copy_over_crispr_readme(self):
        """
        Copies over crispr_readme.txt

        """
        crispr_readme = os.path.join(os.path.dirname(__file__),
                                     'crispr_readme.txt')

        tokenmap = self._create_token_replacement_map()
        result_readme = os.path.join(self._outdir, 'readme.txt')
        with open(result_readme, 'w') as fout:
            fout.write(self._dataset + ' ' +
                       self._get_dataset_description() +
                       '\n\n')
            with open(crispr_readme, 'r') as f:
                for line in f:
                    line_to_write = self._replace_readme_tokens(line,
                                                                tokenmap=tokenmap)
                    fout.write(line_to_write)

    def _replace_readme_tokens(self, line, tokenmap=None):
        """
        Replaces tokens in a line of the CRISPR readme file with their corresponding values from the token
        replacement map.

        :param line: The current line from the readme file to process.
        :type line: str
        :param tokenmap: A map of tokens and their replacement values.
        :type tokenmap: dict
        :return: The line with tokens replaced by their respective values.
        :rtype: str
        """
        for token in tokenmap.keys():
            if token in line:
                return line.replace(token, tokenmap[token])
        return line

    def _generate_rocrate_dir_path(self):
        """
        Generates the directory path for the RO-Crate based on project name, gene set, cell line, treatment type,
        tissue, dataset type, and release version.
        """
        dir_name = self._project_name.lower() + '_'
        if self._gene_set is not None:
            dir_name += self._gene_set.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += re.sub('[^a-zA-Z0-9\w\n\.]', '_', self._tissue.lower()) + '_'
        dir_name += self._treatment.lower() + '_crispr_'
        if self._dataset.lower() != '':
            dir_name += self._dataset.lower() + '_'
        dir_name += self._release.lower()

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
                                                    name='CRISPR',
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
        Adds a subparser for the CRISPR data loader command.

        :return:
        """
        desc = """

        Version {version}

        {cmd} Loads CRISPR data into a RO-Crate by creating a 
        directory, copying over relevant and using FAIRSCAPE CLI to 
        register the data files in the directory known as an RO-Crate

        """.format(version=cellmaps_utils.__version__,
                   cmd=CRISPRDataLoader.COMMAND)

        parser = subparsers.add_parser(CRISPRDataLoader.COMMAND,
                                       help='Loads CRISPR data into a RO-Crate',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument('--skipcopy', action='store_true',
                            help='If set, --h5ad file will not be copied, '
                                 'but instead a 0 byte file will be placed in the RO-Crate as a placeholder. '
                                 'It is up to the caller to manually move/copy the files over before distribution')
        parser.add_argument('--h5ad', required=True,
                            help='Path to h5ad file')
        parser.add_argument('--author', default='Mali Lab',
                            help='Author that created this data')
        parser.add_argument('--name', default='CRISPR',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='Mali Lab',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', default='CM4AI',
                            help='Name of project running this tool, '
                                 'needed for FAIRSCAPE. Usually set to '
                                 'funding source')
        parser.add_argument('--release', required=True,
                            help='Version of release. '
                                 'For example: 0.1 alpha')
        parser.add_argument('--treatment', default='untreated',
                            choices=['paclitaxel', 'vorinostat', 'untreated'],
                            help='Treatment of sample.')
        parser.add_argument('--dataset', required=True,
                            choices=['1channel', 'subset', '4channel'],
                            help='Collection set')
        parser.add_argument('--cell_line', default='MDA-MB-468',
                            choices=['MDA-MB-468', 'KOLF2.1J'],
                            help='Name of cell line. For example MDA-MB-468')
        parser.add_argument('--gene_set', choices=['chromatin', 'metabolic'],
                            default='chromatin',
                            help='Gene set for dataset')
        parser.add_argument('--tissue', choices=['undifferentiated', 'neuron',
                                                 'cardiomyocytes', ''],
                            default='breast; mammary gland',
                            help='Tissue for dataset. Since the default --cell_line '
                                 'is MDA-MB-468, this value is set to the tissue '
                                 'for that cell line')
        parser.add_argument('--num_perturb_guides', default='6',
                            help='Number of guides per perturbation')
        parser.add_argument('--num_non_target_ctrls', default='109',
                            help='Number of non targeting controls')
        parser.add_argument('--num_screen_targets', default='108',
                            help='Number of screen targets')
        return parser

