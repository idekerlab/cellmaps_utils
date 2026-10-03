"""Convert Spectronaut SEC-MS protein-group exports into a release RO-Crate."""


from datetime import date
import logging
import time
import os
import shutil
import uuid

import cellmaps_utils
from cellmaps_utils import constants
from cellmaps_utils import logutils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.provenance import ProvenanceUtil


logger = logging.getLogger(__name__)


class SECMSDataConverter(BaseCommandLineTool):
    """Stream wide SEC-MS matrices and preserve replicate-level provenance."""

    COMMAND = 'secmsconverter'


    def __init__(self, theargs,
                 provenance_utils=ProvenanceUtil()):
        super().__init__()
        self._start_time = int(time.time())
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
        self._provenance_utils = provenance_utils
        self._softwareid = None
        self._input_data_dict = theargs.__dict__


    @staticmethod
    def add_subparser(subparsers):
        parser = subparsers.add_parser(
            SECMSDataConverter.COMMAND,
            help='Convert Spectronaut SEC-MS exports into a RO-Crate',
            formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir', help='Directory where RO-Crate will be made')
        parser.add_argument('--inputs', nargs='+', required=True,
                            help='<tsv file>,replicate #')
        parser.add_argument('--author', default='Krogan Lab',
                            help='Author that created this data')
        parser.add_argument('--name', default='SEC-MS',
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
        parser.add_argument('--tissue', choices=['undifferentiated', 'neuron',
                                                 'cardiomyocytes', ''],
                            default='breast; mammary gland',
                            help='Tissue for dataset. Since the default --cell_line '
                                 'is MDA-MB-468, this value is set to the tissue '
                                 'for that cell line')
        return parser

    def run(self):

        exitcode = 99
        try:
            self._generate_rocrate_dir_path()
            if os.path.exists(self._outdir):
                raise CellMapsError(self._outdir + ' already exists')

            logger.debug('Creating directory ' + str(self._outdir))
            os.makedirs(self._outdir, mode=0o755)

            logutils.setup_filelogger(outdir=self._outdir,
                                      handlerprefix='cellmaps_utils')
            logutils.write_task_start_json(outdir=self._outdir,
                                           start_time=self._start_time,
                                           data={'commandlineargs': self._input_data_dict},
                                           version=cellmaps_utils.__version__)
            keywords = [self._project_name, self._release,
                        self._cell_line, self._treatment, self._tissue,
                        'SEC-MS fractions']

            description = ' '.join(keywords)

            input_tuples = self._get_input_tuples()
            replist = list()
            for input_tuple in input_tuples:
                replist.append(input_tuple[1])

            info_dict = {
                constants.DATASET_NAME: self._name,
                constants.DATASET_ORGANIZATION_NAME: self._organization_name,
                constants.DATASET_PROJECT_NAME: self._project_name,
                constants.DATASET_RELEASE: self._release,
                constants.DATASET_CELL_LINE: self._cell_line,
                constants.DATASET_TREATMENT: self._treatment,
                constants.DATASET_TISSUE: self._tissue,
                constants.DATASET_AUTHOR: self._author,
                constants.DATASET_REPLICATES: ','.join(replist)
            }

            self.save_dataset_info_to_json(self._outdir, info_dict, constants.DATASET_INFO_FILE)

            self._provenance_utils.register_rocrate(self._outdir,
                                                    name=self._name,
                                                    organization_name=self._organization_name,
                                                    project_name=self._project_name,
                                                    description=description,
                                                    keywords=keywords,
                                                    guid=self._get_fairscape_id())
            gen_dsets = list()
            gen_dsets.extend(self._save_secms_data(keywords=keywords,
                                                   input_tuples=input_tuples))

            self._register_software(keywords=keywords, description=description)
            self._register_computation(generated_dataset_ids=gen_dsets,
                                       description=description,
                                       keywords=keywords)
            self._copy_over_secms_readme()
            exitcode = 0
            return exitcode
        finally:
            logutils.write_task_finish_json(outdir=self._outdir,
                                            start_time=self._start_time,
                                            status=exitcode)

    def _get_input_tuples(self):
        """
        Gets a list of tuples of the inputs in format of
        (filename, replicate)
        :return:
        """
        input_tuples = []
        for input in self._inputs:
            input_tuple = input.split(',')
            if len(input_tuple) != 2:
                raise CellMapsError('Expecting 2 elements in input <file>,<replicate>')
            input_tuples.append((input_tuple[0], input_tuple[1]))
        return input_tuples

    def _save_secms_data(self, keywords=[], input_tuples=None):
        """
        Copy input files over naming them as denoted via
        self._inputs variable which should be in format
        of <tsvfile>,<replicate #>

        secms_<replicate #>.tsv
        :return:
        """
        dsets = []
        for input_tuple in input_tuples:
            file_path = os.path.join(self._outdir, 'secms_' + str(input_tuple[1]) + '.tsv')
            logger.debug(f'Copying file {file_path}')
            shutil.copy(input_tuple[0], file_path)
            file_desc = 'SEC-MS file replicate ' + str(input_tuple[1] + ' copied from ' + str(os.path.basename(input_tuple[0])))
            file_keywords = keywords.copy()
            file_keywords.extend(['file', 'Replicate ' + str(input_tuple[1])])
            dset_id = self._provenance_utils.register_dataset(rocrate_path=self._outdir, source_file=file_path,
                                                          skip_copy=True,
                                                          data_dict={'name': ' SEC-MS file',
                                                                     'description': file_desc,
                                                                     'keywords': file_keywords,
                                                                     'data-format': 'tsv',
                                                                     'author': self._author,
                                                                     'version': self._release,
                                                                     'date-published': date.today().strftime(
                                                                         '%Y-%m-%d')},
                                                          guid=self._get_fairscape_id())
            dsets.append(dset_id)

        return dsets

    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _copy_over_secms_readme(self):
        """
        Copies over apms_readme.txt

        """
        secms_readme = os.path.join(os.path.dirname(__file__), 'secms_readme.txt')
        shutil.copy(secms_readme, os.path.join(self._outdir, 'readme.txt'))

    def _generate_rocrate_dir_path(self):
        """
        Generates a directory path for the RO-Crate based on provided metadata like project name,
        cell line, treatment, and release version.
        """
        dir_name = self._project_name.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += self._treatment.lower()
        dir_name += '_secms_'
        dir_name += self._release.lower()
        dir_name = dir_name.replace(' ', '_')
        self._outdir = os.path.join(self._outdir, dir_name)

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
                                                    name='SEC-MS',
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

