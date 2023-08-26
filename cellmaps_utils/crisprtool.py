import os
import sys
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
        self._treatment = theargs.treatment
        self._author = theargs.author
        self._gene_set = theargs.gene_set
        self._feature = theargs.feature
        self._expression = theargs.expression
        self._guiderna = theargs.guiderna
        self._dataset = theargs.dataset
        self._skipcopy = theargs.skipcopy
        self._provenance_utils = provenance_utils
        self._softwareid = None
        self._input_data_dict = theargs.__dict__

    def run(self):
        """

        :return:
        """
        self._generate_rocrate_dir_path()
        if os.path.exists(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        logger.debug('Creating directory ' + str(self._outdir))
        os.makedirs(self._outdir, mode=0o755)

        keywords = [self._project_name, self._release,
                    self._cell_line, self._treatment, 'CRISPR', self._dataset]

        if self._gene_set is not None:
            keywords.append(self._gene_set)

        description = ' '.join(keywords)

        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description=description,
                                                keywords=keywords)
        gen_dsets = []

        gen_dsets.extend(self._copy_and_register_guiderna(keywords=keywords,
                                                          description=description))
        gen_dsets.extend(self._copy_and_register_expression(keywords=keywords,
                                                            description=description))
        self._register_software(keywords=keywords, description=description)
        self._register_computation(generated_dataset_ids=gen_dsets,
                                   description=description,
                                   keywords=keywords)
        self._copy_over_crispr_readme()
        return 0

    def _get_dataset_description(self):
        """

        :return:
        """
        if self._dataset == '1channel':
            return 'FASTQs file were obtain by concatenating 3 NGS run over 7 sequencing lanes'
        elif self._dataset == 'Subset':
            return 'Subset run'

    def _copy_and_register_guiderna(self, description='',
                                    keywords=[]):
        """

        :return:
        """
        dset_ids = []
        for guiderna in self._guiderna:
            orig_filename = os.path.basename(guiderna)
            offset = 0
            if '_CRISPR' in orig_filename:
                offset = orig_filename.index('_CRISPR')
            dest_file = os.path.join(self._outdir, self._cell_line + '_' +
                                     self._treatment + '_'
                                     + orig_filename[offset:])
            if self._skipcopy is True:
                open(dest_file, 'a').close()
            else:
                shutil.copy(guiderna, dest_file)
            file_desc = description + ' file'
            file_keywords = keywords.copy()
            file_keywords.extend(['file'])
            dset_id = self._provenance_utils.register_dataset(rocrate_path=self._outdir, source_file=dest_file,
                                                              skip_copy=True,
                                                              data_dict={'name': 'Guide RNA sequences file',
                                                                         'description': file_desc,
                                                                         'keywords': file_keywords,
                                                                         'data-format': 'fastq',
                                                                         'author': self._author,
                                                                         'version': self._release,
                                                                         'date-published': date.today().strftime(
                                                                             '%Y-%m-%d')})
            dset_ids.append(dset_id)

        return dset_ids

    def _copy_and_register_expression(self, description='',
                                      keywords=[]):
        """

        :return:
        """
        dset_ids = []
        for expression in self._expression:
            orig_filename = os.path.basename(expression)
            offset = 0
            if '_scRNA' in orig_filename:
                offset = orig_filename.index('_scRNA')
            dest_file = os.path.join(self._outdir, self._cell_line + '_' +
                                     self._treatment + '_'
                                     + orig_filename[offset:])
            if self._skipcopy is True:
                open(dest_file, 'a').close()
            else:
                shutil.copy(expression, dest_file)
            file_desc = description + ' file'
            file_keywords = keywords.copy()
            file_keywords.extend(['file'])
            dset_id = self._provenance_utils.register_dataset(rocrate_path=self._outdir, source_file=dest_file,
                                                              skip_copy=True,
                                                              data_dict={'name': 'Single-cell RNA expression file',
                                                                         'description': file_desc,
                                                                         'keywords': file_keywords,
                                                                         'data-format': 'fastq',
                                                                         'author': self._author,
                                                                         'version': self._release,
                                                                         'date-published': date.today().strftime(
                                                                             '%Y-%m-%d')})
            dset_ids.append(dset_id)

        return dset_ids

    def _create_token_replacement_map(self):
        """

        :return:
        """
        prefix = self._cell_line + '_' + self._treatment
        return {'@@PREFIX@@': prefix,
                '@@FEATURE_REF_UNDERLINE@@': '-' * (len(prefix) + 23),
                '@@CRISPR_UNDERLINE@@': '-' * (len(prefix) + 18),
                '@@SCRNA_UNDERLINE@@': '-' * (len(prefix) + 19)}

    def _copy_over_crispr_readme(self):
        """
        Copies over crispr_readme.txt

        """
        crispr_readme = os.path.join(os.path.dirname(__file__), 'crispr_readme.txt')
        if not os.path.isfile(crispr_readme):
            return

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

        :param line:
        :return:
        """
        for token in tokenmap.keys():
            if token in line:
                return line.replace(token, tokenmap[token])
        return line

    def _generate_rocrate_dir_path(self):
        """

        :return:
        """
        dir_name = self._project_name.lower() + '_'
        if self._gene_set is not None:
            dir_name += self._gene_set.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += self._treatment.lower() + '_crispr_'
        dir_name += self._release.lower()

        dir_name = dir_name.replace(' ', '_')
        self._outdir = os.path.join(self._outdir, dir_name)

    def _register_computation(self, generated_dataset_ids=[],
                              description='',
                              keywords=[]):
        """
        # Todo: added in used dataset, software and what is being generated
        :return:
        """
        logger.debug('Getting id of input rocrate')
        comp_keywords = keywords.copy()
        comp_keywords.extend(['computation'])
        description = description + ' run of ' + cellmaps_utils.__name__
        self._provenance_utils.register_computation(self._outdir,
                                                    name=cellmaps_utils.__name__ + ' computation',
                                                    run_by=str(self._provenance_utils.get_login()),
                                                    command=str(self._input_data_dict),
                                                    description=description,
                                                    keywords=comp_keywords,
                                                    used_software=[self._softwareid],
                                                    generated=generated_dataset_ids)

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
                                                                    url=cellmaps_utils.__repo_url__)

    def add_subparser(subparsers):
        """

        :return:
        """
        desc = """

        Version {version}

        {cmd} Loads CRISPR data into a RO-Crate
        """.format(version=cellmaps_utils.__version__,
                   cmd=CRISPRDataLoader.COMMAND)

        parser = subparsers.add_parser(CRISPRDataLoader.COMMAND,
                                       help='Loads CRISPR data into a RO-Crate',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument('--feature', required=True,
                            help='ChroCRISPRi-feature-ref-10x.csv file')
        parser.add_argument('--guiderna', required=True, nargs='+',
                            help='One or more FASTQ files containing sequence of the guide '
                                 'RUNA linked to cell barcode. It is assumed these files'
                                 'have _CRISPRi in name and after has S#_L###_R#_###.fastq.gz')
        parser.add_argument('--expression', required=True, nargs='+',
                            help='One or more FASTQ files containing single-cell RNA '
                                 'expression data. It is assumed these files have _scRNAseq '
                                 'in name and after has S#_L###_R#_###.fastq.gz')
        parser.add_argument('--skipcopy', action='store_true',
                            help='If set, --guiderna and --expression files will not be copied, '
                                 'but instead 0 byte files will be placed in the RO-Crate as placeholders. '
                                 'It is up to the caller to manually move the files over before distribution')
        parser.add_argument('--author', default='Mali Lab',
                            help='Author that created this data')
        parser.add_argument('--name', default='CRISPR',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='Mali Lab',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', required=True,
                            help='Name of project running this tool, needed for '
                                 'FAIRSCAPE. Usually set to funding source')
        parser.add_argument('--release', required=True,
                            help='Version of release. For example: 0.1 alpha')
        parser.add_argument('--treatment', default='untreated',
                            choices=['paclitaxel', 'vorinostat', 'untreated'],
                            help='Treatment of sample.')
        parser.add_argument('--dataset', required=True, choices=['1channel', 'Subset'],
                            help='Collection set')
        parser.add_argument('--cell_line', default='MDA-MB-468',
                            help='Name of cell line. For example MDA-MB-468')
        parser.add_argument('--gene_set', choices=['chromatin', 'metabolic'],
                            default='chromatin',
                            help='Gene set for dataset')
        return parser

