import os
import tempfile
import tarfile
import shutil
from datetime import date
import logging
import csv
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil

logger = logging.getLogger(__name__)


class TableFromROCrates(BaseCommandLineTool):
    """
    Creates table of meta data and links from
    one or more RO-Crates
    """
    COMMAND = 'rocratetable'

    ID_COL = 'FAIRSCAPE ARK ID'
    DATE_COL = 'Date'
    COMPUTATION_COL = 'Name'
    DESCRIPTION_COL = 'Description'
    KEYWORDS_COL = 'Keywords'
    DOWNLOAD_COL = 'Download RO-Crate Data Package'
    DOWNLOAD_COL_SIZE = 'Download RO-Crate Data Package Size MB'
    GENERATED_COL = 'Generated By Software'
    OUTPUT_COL = 'Output Dataset'
    RESPONSIBLE_COL = 'Responsible Lab'
    TYPE_COL = 'Type'
    CELL_LINE_COL = 'Cell Line'
    TREATMENT_COL = 'Treatment'
    TISSUE_COL = 'Tissue'
    GENESET_COL = 'Gene set'
    VERSION_COL = 'Version'

    DATA_ROCRATE = 'Data'
    MODEL_ROCRATE = 'Model'
    INTERMEDIATE_ROCRATE = 'Intermediate'
    OTHER_ROCRATE = 'Other'

    COLUMNS = [ID_COL, DATE_COL,
               VERSION_COL,
               TYPE_COL,
               CELL_LINE_COL,
               TISSUE_COL,
               TREATMENT_COL,
               GENESET_COL,
               GENERATED_COL,
               COMPUTATION_COL,
               DESCRIPTION_COL, KEYWORDS_COL,
               DOWNLOAD_COL,
               DOWNLOAD_COL_SIZE,
               GENERATED_COL,
               OUTPUT_COL,
               RESPONSIBLE_COL]

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
        self._rocrates = theargs.rocrates
        self._date = theargs.date
        self._version = theargs.release
        self._provenance_utils = provenance_utils
        self._downloadurlprefix = theargs.downloadurlprefix
        self._input_data_dict = theargs.__dict__

    def _get_rocrate_type(self, compname):
        """
        Gets type of rocrate, which can be Data, Model, or Intermediate

        :return:
        :rtype: str
        """
        if compname in ['IF images', 'AP-MS', 'CRISPR']:
            return TableFromROCrates.DATA_ROCRATE
        if compname in ['Hierarchy']:
            return TableFromROCrates.MODEL_ROCRATE
        return TableFromROCrates.INTERMEDIATE_ROCRATE

    def _get_cell_line(self, keywords):
        """
        Looks for cell line in keywords

        :param keywords:
        :type keywords: list
        :return:
        :rtype: str
        """
        if 'MDA-MB-468' in keywords:
            return 'MDA-MB-468'
        if 'KOLF2.1J' in keywords:
            return 'KOLF2.1J'
        return 'Unknown'

    def _get_treatment(self, keywords):
        """
        Gets treatment from keywords

        :param keywords:
        :return:
        """
        treatments = []
        if 'untreated' in keywords:
            treatments.append('untreated')
        if 'vorinostat' in keywords:
            treatments.append('vorinostat')
        if 'paclitaxel' in keywords:
            treatments.append('paclitaxel')
        return ','.join(treatments)

    def _get_tissue(self, keywords):
        """
        Gets tissue from keywords

        :param keywords:
        :return:
        """
        if 'undifferentiated' in keywords:
            return 'undifferentiated'
        if 'neuron' in keywords:
            return 'neuron'
        if 'cardiomyocytes' in keywords:
            return 'cardiomyocytes'
        return ''

    def _get_geneset(self, keywords):
        """
        Gets treatment from keywords

        :param keywords:
        :return:
        """
        genesets = []

        if 'chromatin' in keywords:
            genesets.append('chromatin')
        if 'metabolic' in keywords:
            genesets.append('metabolic')
        if len(genesets) == 0:
            return 'Unknown'
        return ','.join(genesets)

    def run(self):
        """
        Runs the process of creation a metadata table from one or more RO-Crates. This method iterates through each
        RO-Crate, collects metadata and provenance information, and writes it into a tab-separated values (TSV) file.

        :return:
        """
        if os.path.exists(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        logger.debug('Creating directory ' + str(self._outdir))
        os.makedirs(self._outdir, mode=0o755)

        table_file = os.path.join(self._outdir, 'data.tsv')
        with open(table_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, delimiter='\t',
                                    fieldnames=TableFromROCrates.COLUMNS)
            writer.writeheader()
            for rocrate in self._rocrates:
                rocrate_dict = self._get_rocrate_as_dict(rocrate)
                urlfile = os.path.basename(rocrate)
                if not rocrate.endswith('.tar.gz'):
                    urlfile += '.tar.gz'

                prov_attrs = self._provenance_utils.get_rocrate_provenance_attributes(rocrate=rocrate_dict)

                gen_col_value = self._get_software_url(rocrate_dict=rocrate_dict)
                if gen_col_value == 'cellmaps_utils':
                    gen_col_value = '- ' + prov_attrs.get_organization_name() + ' -'

                output_url = self._get_output_dataset_url(rocrate_dict=rocrate_dict)

                comp_name = self._get_computation_name(rocrate_dict=rocrate_dict)
                if comp_name is None:
                    comp_name = prov_attrs.get_name()

                logger.debug(rocrate + ': ' + 'Keywords: ' + str(prov_attrs.get_keywords()))
                row = {TableFromROCrates.ID_COL: self._provenance_utils.get_id_of_rocrate(rocrate=rocrate_dict),
                       TableFromROCrates.DATE_COL: self._date,
                       TableFromROCrates.VERSION_COL: self._version,
                       TableFromROCrates.TYPE_COL: self._get_rocrate_type(comp_name),
                       TableFromROCrates.CELL_LINE_COL: self._get_cell_line(prov_attrs.get_keywords()),
                       TableFromROCrates.TISSUE_COL: self._get_tissue(prov_attrs.get_keywords()),
                       TableFromROCrates.TREATMENT_COL: self._get_treatment(prov_attrs.get_keywords()),
                       TableFromROCrates.GENESET_COL: self._get_geneset(prov_attrs.get_keywords()),
                       TableFromROCrates.COMPUTATION_COL: comp_name,
                       TableFromROCrates.DESCRIPTION_COL: prov_attrs.get_description(),
                       TableFromROCrates.KEYWORDS_COL: ','.join(prov_attrs.get_keywords()),
                       TableFromROCrates.DOWNLOAD_COL: self._get_rocrate_download_link(urlfile),
                       TableFromROCrates.DOWNLOAD_COL_SIZE: self._get_rocrate_size(rocrate),
                       TableFromROCrates.GENERATED_COL: gen_col_value,
                       TableFromROCrates.OUTPUT_COL: output_url,
                       TableFromROCrates.RESPONSIBLE_COL: prov_attrs.get_organization_name()}
                writer.writerow(row)

        return 0

    def _get_rocrate_size(self, rocrate_path):
        """
         Determines the size of the RO-Crate, either directly or by inspecting its tar.gz archive.

        :param rocrate_path: The file path to the RO-Crate or its tar.gz archive.
        :return:
        """
        if os.path.isfile(rocrate_path):
            return str(max(round(os.path.getsize(rocrate_path)/1048576.0), 1))
        targz_appended = rocrate_path + '.tar.gz'
        if os.path.isfile(targz_appended):
            return self._get_rocrate_size(rocrate_path + '.tar.gz')
        return '?'

    def _get_rocrate_download_link(self, urlfile):
        """
        Constructs a download link for the RO-Crate.

        :param urlfile: The base name of the RO-Crate file for which to construct the download link.
        :return: The full URL to download the RO-Crate
        """
        return self._downloadurlprefix + urlfile

    def _get_software_url(self, rocrate_dict=None):
        """
        Retrieves the URL of the software used to generate the RO-Crate

        :param rocrate_dict: The RO-Crate metadata as a dictionary.
        :return: The URL of the software or its name if generated by cellmaps_utils.
        """
        for entry in self._get_next_software_from_rocrate_dict(rocrate_dict=rocrate_dict):
            if entry['name'] == 'cellmaps_utils':
                return entry['name']
            # this creates html <a href fragment
            # return '<a href="' + entry['url'] + '" target="_blank">' + entry['name'] + '</a>'
            return entry['url']

    def _get_next_software_from_rocrate_dict(self, rocrate_dict=None):
        """
        Generator that gets next software from **rocrate** dict passed
        in

        :param rocrate_dict:
        :type rocrate_dict: dict
        :return: next software section of RO-CRATE as dictionary
        :type: dict
        """
        if not '@graph' in rocrate_dict:
            raise CellMapsError('No @graph, but found: ' + str(rocrate_dict.keys()))
        for graph_entry in rocrate_dict['@graph']:
            if 'metadataType' not in graph_entry:
                continue
            if 'EVI#Software' in graph_entry['metadataType']:
                yield graph_entry

    def _get_next_computation_from_rocrate_dict(self, rocrate_dict=None):
        """
        Generator that gets next software from **rocrate** dict passed
        in

        :param rocrate_dict:
        :type rocrate_dict: dict
        :return: next software section of RO-CRATE as dictionary
        :type: dict
        """
        # Todo refactor this and _get_next_software_from_rocrate_dict because
        #      they basically do the same thing
        if not '@graph' in rocrate_dict:
            raise CellMapsError('No @graph, but found: ' + str(rocrate_dict.keys()))
        for graph_entry in rocrate_dict['@graph']:
            if 'metadataType' not in graph_entry:
                continue
            if 'EVI#Computation' in graph_entry['metadataType']:
                yield graph_entry

    def _get_computation_name(self, rocrate_dict=None):
        """
        Extracts the computation name from the RO-Crate metadata

        :param rocrate_dict: The RO-Crate metadata as a dictionary.
        :return: The name of the computation, or None.
        """
        for entry in self._get_next_computation_from_rocrate_dict(rocrate_dict=rocrate_dict):
            if ' computation' in entry['name']:
                return None
            return entry['name']

    def _get_next_output_dataset_url(self, rocrate_dict=None,
                                     name='Output Dataset'):
        """
        Generator that gets url from next Dataset
        whose name is **name**

        :param rocrate_dict:
        :return:
        """
        if not '@graph' in rocrate_dict:
            raise CellMapsError('No @graph, but found: ' + str(rocrate_dict.keys()))
        for graph_entry in rocrate_dict['@graph']:
            if 'name' not in graph_entry:
                continue
            if graph_entry['name'] == name:
                if 'url' in graph_entry:
                    yield graph_entry['url']

    def _get_output_dataset_url(self, rocrate_dict=None):
        """
        Retrieves the URL of the output dataset from the RO-Crate.

        :param rocrate_dict: The RO-Crate as a dictionary.
        :return: The URL of the output dataset or an empty string if not found.
        """
        for entry in self._get_next_output_dataset_url(rocrate_dict=rocrate_dict):
            if entry is None:
                return ''
            return entry

    def _get_rocrate_as_dict(self, rocrate=None):
        """
        Gets ro-crate-metadata.json as a dict
        from
        :param rocrate: Path to directory, ro-crate meta data file, tar file, or tar.gz file
        :type rocrate: str
        :return:
        """
        if os.path.isdir(rocrate):
            return self._provenance_utils.get_rocrate_as_dict(rocrate_path=rocrate)
        if not os.path.isfile(rocrate):
            raise CellMapsError('Invalid rocrate: ' + str(rocrate))
        if rocrate.endswith('.tar') or rocrate.endswith('.tar.gz') or rocrate.endswith('.tgz'):
            return self._get_rocrate_as_dict_from_tarball(rocrate=rocrate)
        return self._provenance_utils.get_rocrate_as_dict(rocrate_path=rocrate)

    def _get_rocrate_as_dict_from_tarball(self, rocrate=None):
        """
        Extracts the RO-Crate metadata from a tarball (tar.gz) and returns it as a dictionary.

        :param rocrate: Path to the tarball containing the RO-Crate.
        :return: The RO-Crate as a dictionary.
        """
        with tarfile.open(rocrate) as tar:
            for ti in tar:
                split_path = ti.name.split('/')
                if len(split_path) != 2:
                    continue
                if split_path[1] == 'ro-crate-metadata.json':
                    temp_dir = tempfile.mkdtemp()
                    try:
                        tar.extract(ti.name, path=temp_dir)
                        return self._provenance_utils.get_rocrate_as_dict(rocrate_path=os.path.join(temp_dir,
                                                                                             ti.name))
                    finally:
                        shutil.rmtree(temp_dir)

    @staticmethod
    def add_subparser(subparsers):
        """
        Adds the command-line subparser for the TableFromROCrates tool

        :return:
        """
        desc = """

        Version {version}

        {cmd} Creates meta data Table from one or more RO-Crates
        """.format(version=cellmaps_utils.__version__,
                   cmd=TableFromROCrates.COMMAND)

        parser = subparsers.add_parser(TableFromROCrates.COMMAND,
                                       help='Creates metadata table from RO-Crates',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory metadata tables will be created')
        parser.add_argument('--rocrates', nargs='+',
                            help='Path to RO-Crates used for table generation. ')
        parser.add_argument('--date', default=date.today().strftime('%Y-%m-%d'),
                            help='Date to list in table for RO-Crates')
        parser.add_argument('--release', default='0.1 alpha',
                            help='Version of release')
        parser.add_argument('--downloadurlprefix', default='https://g-9b3b6e.9ad93.a567.data.globus.org/Data/cm4ai_0.1alpha/')

        return parser

