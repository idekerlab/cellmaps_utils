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
        self._author = theargs.author
        self._gene_set = theargs.gene_set
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
                    self._cell_line, self._treatment, 'AP-MS edgelist']

        if self._gene_set is not None:
            keywords.append(self._gene_set)

        description = ' '.join(keywords)

        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description=description,
                                                keywords=keywords,
                                                guid=self._get_fairscape_id())
        gen_dsets = []

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

    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _copy_over_apms_readme(self):
        """
        Copies over apms_readme.txt

        """
        apms_readme = os.path.join(os.path.dirname(__file__), 'apms_readme.txt')
        shutil.copy(apms_readme, os.path.join(self._outdir, 'readme.txt'))

    def _generate_rocrate_dir_path(self):
        """

        :return:
        """
        dir_name = self._project_name.lower() + '_'
        if self._gene_set is not None:
            dir_name += self._gene_set.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += self._treatment.lower() + '_apms_'
        dir_name += self._release.lower()

        dir_name = dir_name.replace(' ', '_')
        self._outdir = os.path.join(self._outdir, dir_name)

    def _merge_and_save_apms_data(self):
        """

        :return:
        """
        df_list = []
        for input in self._inputs:
            df_list.append(pd.read_csv(input, sep='\t'))

        df = pd.concat(df_list)

        apms_path = os.path.join(self._outdir, 'apms.tsv')
        df.to_csv(apms_path, sep='\t', index=False)
        return apms_path

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
        return parser

