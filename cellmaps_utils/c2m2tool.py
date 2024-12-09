import json
import os
import shutil
import uuid
import copy
import hashlib
from datetime import date
import re
import time
import logging
import requests
from requests import RequestException
import pandas as pd

from tqdm import tqdm
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
from cellmaps_utils import logutils
from cellmaps_utils.provenance import ProvenanceUtil

logger = logging.getLogger(__name__)


class C2M2Creator(BaseCommandLineTool):
    """
    Creates RO-Crate of CRISPR data from
    raw CRISPR data files
    """
    COMMAND = 'c2m2creator'

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
        self._provenance_utils = provenance_utils
        self._softwareid = None
        self._dataset_ids = []
        self._input = theargs.input
        self._input_data_dict = theargs.__dict__
        self._name = theargs.name

        if theargs.author is None:
            self._author = self._provenance_utils.get_login()
        else:
            self._author = theargs.author
        self._organization_name = theargs.organization_name
        self._project_name = theargs.project_name
        self._ext_cv_ref = theargs.ext_cv_ref
        self._c2m2_json = None
        self._c2m2_submissiondir = os.path.join(self._outdir, theargs.c2m2submitdir)
        self._c2m2_mapping = None
        self._skip_logging = theargs.skip_logging
        self._start_time = int(time.time())
        self._end_time = -1
        self._abbreviation = 'CM4AI'
        self._project_id_namespace = 'https://cm4ai.org'
        self._project_local_id = 'CM4AI'
        self._readable_name = 'Cell maps for Artificial Intelligence'

    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _download_file(self, downloadurl, destfilename, max_retries=3, retry_wait=10):
        # use python requests to download the file and then get its results
        local_file = os.path.join(self._outdir,
                                  destfilename)

        retry_num = 0
        download_successful = False
        while retry_num < max_retries and not download_successful:
            try:
                with requests.get(downloadurl, stream=True) as r:
                    content_size = int(r.headers.get('content-length', 0))
                    tqdm_bar = tqdm(desc='Downloading ' + os.path.basename(local_file),
                                    total=content_size,
                                    unit='B', unit_scale=True,
                                    unit_divisor=1024)
                    logger.debug('Downloading ' + str(downloadurl) +
                                 ' of size ' + str(content_size) +
                                 'b to ' + local_file)
                    try:
                        r.raise_for_status()
                        with open(local_file, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                                tqdm_bar.update(len(chunk))
                        download_successful = True
                    finally:
                        tqdm_bar.close()

                return local_file

            except RequestException as he:
                logger.debug(str(he.response.text))
                retry_num += 1
                time.sleep(retry_wait)

        if not download_successful:
            raise CellMapsError(f'{max_retries} attempts to download ' +
                                str(destfilename) + ' file from ' +
                                str(downloadurl) + ' failed')

    def _register_rocrate(self):
        """
        Registers RO-Crate
        :return:
        """
        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description='Creates C2M2 TSV files for submission',
                                                keywords=['C2M2', 'CM4AI'],
                                                guid=self._get_fairscape_id())

    def _register_tsv_file(self, tsvfilepath=None,
                           altdescription=None):
        """
        Registers TSV file as a dataset, adding to dataset generated ids

        :param tsvfilepath:
        """
        prefix = os.path.basename(tsvfilepath)
        if altdescription is not None:
            desc = altdescription
        else:
            desc = prefix + ' C2M2 TSV file'
        # describe file
        dataset_dict = {'name': prefix,
                        'author': self._author,
                        'version': '1.0',
                        'date-published': date.today().strftime(self._provenance_utils.get_default_date_format_str()),
                        'description': desc,
                        'data-format': 'TSV',
                        'keywords': ['file', 'C2M2']}

        dset_id = self._provenance_utils.register_dataset(self._outdir,
                                                          data_dict=dataset_dict,
                                                          source_file=tsvfilepath,
                                                          skip_copy=True)
        self._dataset_ids.append(dset_id)

    def _register_software(self):
        """
        Registers this tool, self._provenance must exist and have 'keywords' and
        'description' set

        :raises CellMapsProvenanceError: If fairscape call fails
        """
        software_keywords = ['C2M2', 'TSV']
        software_keywords.extend(['tools', cellmaps_utils.__name__])
        software_description = cellmaps_utils.__description__
        self._softwareid = self._provenance_utils.register_software(self._outdir,
                                                                    name=cellmaps_utils.__name__,
                                                                    description=software_description,
                                                                    author=cellmaps_utils.__author__,
                                                                    version=cellmaps_utils.__version__,
                                                                    file_format='py',
                                                                    keywords=software_keywords,
                                                                    url=cellmaps_utils.__repo_url__)

    def _register_computation(self):
        """
        Registers computation with rocrate.
        Current implementation only registers the 1st 2000 images

        """
        keywords = ['C2M2', 'computation']
        description = 'Run of ' + cellmaps_utils.__name__ + ' C2M2Creator'

        self._provenance_utils.register_computation(self._outdir,
                                                    name='C2M2Creator',
                                                    run_by=str(self._provenance_utils.get_login()),
                                                    command=str(self._input_data_dict),
                                                    description=description,
                                                    keywords=keywords,
                                                    used_software=[self._softwareid],
                                                    used_dataset=[],
                                                    generated=self._dataset_ids)

    def _parse_c2m2_json(self):
        """
        Parses c2m2 json spec to get column headers for each needed tsv
        file
        :return:
        :rtype: dict
        """
        with open(self._c2m2_json) as f:
            data = json.load(f)

        if 'resources' not in data:
            raise CellMapsError('No resources found in ' + str(self._c2m2_json))
        self._c2m2_mapping = {}
        for r in data['resources']:
            self._c2m2_mapping[r['name']] = {'path': r['path'],
                                   'fields': []}
            for field in r['schema']:
                self._c2m2_mapping[r['name']]['fields'].append(r['schema'][field])

    def _validate_data_matches_expected_cols(self, tsvfileprefix=None,
                                             data=None):
        """

        :param tsvfileprefix:
        :param data:
        :return:
        """
        expected_cols = self._extract_cols(tsvfileprefix)
        expected_col_set = set(expected_cols)
        data_col_set = set(data.keys())
        if expected_col_set != data_col_set:
            logger.error('For ' + tsvfileprefix +
                         ' C2M2_packaage.json columns: ' +
                         str(expected_col_set) +
                         ' differs from what this method generates: ' +
                         str(data_col_set))

    def _extract_cols(self, tsvname=None):
        """

        :param tsvname:
        :return:
        """
        cols = []

        # There is not an entry for collection_biofluid in C2M2_datapackage.json
        # so just built list off this page:
        # https://info.cfde.cloud/documentation/C2M2/TableInfo:-collection_biofluid.tsv
        if tsvname not in self._c2m2_mapping:
            logger.warning(tsvname + ' not in C2M2_datapackage.json')
            if tsvname == 'collection_biofluid':
                logger.warning(tsvname + ' using manually created field list since '
                                         'C2M2_datapackage.json does not have info')
                return ['collection_id_namespace', 'collection_local_id', 'biofluid']
            else:
                raise CellMapsError(tsvname + ' lacks entry in C2M2_datapackage.json')

        for fields_entry in self._c2m2_mapping[tsvname]['fields']:
            for subfield_entry in fields_entry:
                if 'name' not in subfield_entry:
                    continue
                if not isinstance(subfield_entry, dict):
                    cols.append(subfield_entry)
                else:
                    cols.append(subfield_entry['name'])
        return cols

    def _generate_id_namespace(self):
        """
        Generates id_namespace.tsv file
        :return:
        """
        data = {'id': ['https://cm4ai.org'],
                'abbreviation': [self._abbreviation],
                'name': [self._readable_name],
                'description': ['The CM4AI data generation project seeks to map the spatiotemporal '
                                'architecture of human cells and use these maps toward the grand '
                                'challenge of interpretable genotype-phenotype learning.']}
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, 'id_namespace.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _generate_project(self):
        """
        Generates project.tsv file
        :return:
        """
        # Todo Need to review the local id names, abbreviations, and descriptions

        data = {'id_namespace': [self._project_id_namespace, self._project_id_namespace,
                                 self._project_id_namespace],
                'local_id': ['Perturb-Seq', 'IFImage', 'PPI'],
                'persistent_id': ['', '', ''],
                'abbreviation': ['Perturb-Seq', 'IFImage', 'PPI'],
                'name': ['Perturb-Seq CRISPR', 'Immunoflourescent Imaging', 'Protein to Protein Interaction'],
                'description': ['CM4AI CRISPR Perturb Sequence',
                                'CM4AI Immunoflourescent imaging',
                                'CM4AI protein interaction']}

        self._validate_data_matches_expected_cols(tsvfileprefix='project',
                                                  data=data)
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, 'project.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _generate_dcc(self):
        """
        Generates dcc.tsv file
        :return:
        """
        data = {'id': ['BRIDGE2AI.CM4AI'],
                'dcc_name': ['Cell Maps for Artificial Intelligence'],
                'dcc_abbreviation': ['CM4AI'],
                'dcc_description': ['The CM4AI data generation project seeks to map the spatiotemporal '
                                    'architecture of human cells and use these maps toward the grand '
                                    'challenge of interpretable genotype-phenotype learning.'] ,
                'contact_email': ['tools@cm4ai.org'],
                'contact_name': ['Christopher Churas'],
                'dcc_url': ['https://cm4ai.org'],
                'project_id_namespace': [self._project_id_namespace],
                'project_local_id': [self._project_local_id]}
        self._validate_data_matches_expected_cols(tsvfileprefix='dcc',
                                                  data=data)
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, 'dcc.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _generate_subject(self):
        """
        Generates subject.tsv file
        :return:
        """
        data = {'id_namespace': [self._project_id_namespace, self._project_id_namespace],
                'local_id': ['MDA-MB-468', 'KOLF2.1J'],
                'project_id_namespace': [self._project_id_namespace, self._project_id_namespace],
                'project_local_id': ['CM4AI', 'CM4AI'],
                'persistent_id': ['', ''],
                'creation_time': ['', ''],
                'granularity': ['cfde_subject_granularity:4', 'cfde_subject_granularity:4'],
                'sex': ['cfde_subject_sex:1', 'cfde_subject_sex:2'],
                'ethnicity': ['cfde_subject_ethnicity:1', 'cfde_subject_ethnicity:1'],
                'age_at_enrollment': [51, 55]}
        self._validate_data_matches_expected_cols(tsvfileprefix='subject',
                                                  data=data)
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, 'subject.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _generate_collection(self):
        """

        :return:
        """
        data = {'id_namespace': [self._project_id_namespace],
                'local_id': ['Perturb-Seq'],
                'persistent_id': [''],
                'creation_time': [''],
                'abbreviation': [''],
                'name': ['Single pooled crispr screens analysis'],
                'description': ['Single pooled crispr screens analysis']
                }
        self._validate_data_matches_expected_cols(tsvfileprefix='collection',
                                                  data=data)
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, 'collection.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _generate_crispr_file_tsv(self, rocrate_dir=None,
                                  rocrate_dict=None):
        """

        :param rocrate_dir:
        :param rocrate_dict:
        :return:
        """
        # TODO in future parse rocrate for files, but for now just
        #      look for h5ad file and add entry to file.tsv
        cell_line = self._get_cell_line_from_rocrate_dict(rocrate_dict=rocrate_dict)
        h5adfile = None
        for entry in os.listdir(rocrate_dir):
            if not entry.endswith('.h5ad'):
                continue
            h5adfile = os.path.join(rocrate_dir, entry)
        if h5adfile is None:
            raise CellMapsError('No .h5ad file found in ' + rocrate_dir)

        filehashes = self._get_md5_and_sha256_hashes(filepath=h5adfile)
        data = {'id_namespace': [self._project_id_namespace],
                'local_id': [os.path.basename(h5adfile)],
                'project_id_namespace': ['https://cm4ai.org'],
                'project_local_id': ['Perturb-Seq'],
                'persistent_id': [''],
                'creation_time': [''],
                'size_in_bytes': [os.path.getsize(h5adfile)],
                'uncompressed_size_in_bytes': [''],
                'sha256': [filehashes['sha256']],
                'md5': [filehashes['md5']],
                'filename': [os.path.basename(h5adfile)],
                'format': ['format:3590'],
                'compression_format': [''],
                'data_type': [''],
                'assay_type': [''],
                'analysis_type': [''],
                'mime_type': [''],
                'bundle_collection_id_namespace': [''],
                'bundle_collection_local_id': [''],
                'dbgap_study_id': ['']}
        self._validate_data_matches_expected_cols(tsvfileprefix='file',
                                                  data=data)
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, 'file.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _get_md5_and_sha256_hashes(self, filepath=None):
        """

        :param filepath:
        :return:
        :rtype: dict
        """
        # compute hashes
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as data:
            for chunk in iter(lambda: data.read(4096), b""):
                md5.update(chunk)
                sha256.update(chunk)

        return {'md5': md5.hexdigest(),
                'sha256': sha256.hexdigest()}

    def _generate_empty_tsv(self, tsvprefix=None):
        """

        :param tsvfilename:
        :return:
        """
        tsv_cols = self._extract_cols(tsvprefix)
        logger.debug(str(tsvprefix) + '.tsv columns: ' + str(tsv_cols))
        data = {}
        for col in tsv_cols:
            data[col] = []
        df = pd.DataFrame(data=data)
        destfile = os.path.join(self._c2m2_submissiondir, tsvprefix + '.tsv')
        df.to_csv(destfile, sep='\t', index=False)
        self._register_tsv_file(tsvfilepath=destfile)

    def _write_task_start_json(self):
        """
        Writes task_start.json file with information about
        what is to be run

        """
        data = {}

        if self._input_data_dict is not None:
            data.update({'commandlineargs': self._input_data_dict})

        logutils.write_task_start_json(outdir=self._outdir,
                                       start_time=self._start_time,
                                       version=cellmaps_utils.__version__,
                                       data=data)

    def _get_cell_line_from_rocrate_dict(self, rocrate_dict=None):
        """

        :param rocrate_dict:
        :return:
        """
        if 'keywords' in rocrate_dict:
            if 'MDA-MB-468' in rocrate_dict['keywords']:
                return 'MDA-MB-468'
            if 'KOLF2.1J' in rocrate_dict['keywords']:
                return 'KOLF2.1J'

        raise CellMapsError('Neither MDA-MB-468 or KOLF2.1J cell line found '
                            'in RO-Crate keywords')

    def run(self):
        """
        Runs the process of CRISPR data loading into a RO-Crate.
        It includes generating the output directory,
        linking and registering h5ad file and registering the
        computation and software used in the process.

        :return:
        """
        exitcode=99
        try:
            if os.path.exists(self._outdir):
                raise CellMapsError(self._outdir + ' already exists')

            logger.debug('Creating directory ' + str(self._outdir))
            os.makedirs(self._outdir, mode=0o755)

            if self._skip_logging is False:
                logutils.setup_filelogger(outdir=self._outdir,
                                          handlerprefix='cellmaps_utils')

            self._write_task_start_json()
            self._register_rocrate()
            self._register_software()

            # download C2M2_datapackage.json and store in RO-Crate
            self._c2m2_json = self._download_file('https://osf.io/download/3sra4', 'C2M2_datapackage.json')

            # download citation for above file
            self._download_file('https://osf.io/3sra4/metadata/?format=datacite-json', 'C2M2_datapackage.json-datacite.json')

            # download external_CV_reference_files and store in RO-Crate
            # https://files.osf.io/v1/resources/bq6k9/providers/osfstorage/611e9cf92dab24014f25ba63/?zip=
            # uncompress external_CV_reference_files directory
            # going to just copy it because it is 9 gigabytes and download is very slow
            logger.info('Copying over self._ext_cv_ref')
            shutil.copytree(self._ext_cv_ref,
                            os.path.join(self._outdir,
                                         'external_CV_reference_files'))

            # download prepare_C2M2_submission.py file and store in RO-Crate
            self._download_file('https://osf.io/download/7qdz4',
                                'prepare_C2M2_submission.py')
            self._download_file('https://osf.io/7qdz4/metadata/?format=datacite-json',
                                'prepare_C2M2_submission.py-datacite.json')

            # edit line 44 of prepare_C2M2_submission.py if submission dir is not default name

            # create c2m2submission directory
            os.makedirs(self._c2m2_submissiondir, mode=0o755)

            # parse C2M2_package.json file
            self._parse_c2m2_json()

            # generate dcc.tsv
            self._generate_dcc()

            # generate id_namespace.tsv
            self._generate_id_namespace()

            # generate project.tsv
            self._generate_project()

            # generate subject.tsv
            self._generate_subject()

            # generate collection.tsv
            self._generate_collection()

            # generate other empty tsv files
            for tsvprefix in ['biosample', 'biosample_disease',
                              'biosample_gene', 'biosample_substance',
                              'subject_disease', 'subject_phenotype',
                              'subject_role_taxonomy', 'subject_substance',
                              'collection_anatomy', 'collection_biofluid',
                              'collection_compound', 'collection_disease',
                              'collection_gene', 'collection_phenotype',
                              'collection_protein', 'collection_substance',
                              'collection_taxonomy']:
                self._generate_empty_tsv(tsvprefix=tsvprefix)

            if self._input is not None:
                for input_rocrate in self._input:
                    rocrate_dict = self._provenance_utils.get_rocrate_as_dict(input_rocrate)

                    if rocrate_dict['name'] == 'CRISPR':
                        # TODO in future parse rocrate for files, but for now just
                        #      look for h5ad file and add entry to file.tsv
                        self._generate_crispr_file_tsv(rocrate_dir=input_rocrate,
                                                       rocrate_dict=rocrate_dict)
                    # iterate through all RO-Crates fed in and
                    # generate file (NEED TO REMOVE FROM EMPTY LIST ABOVE)

                    # generate sample (NEED TO REMOVE FROM EMPTY LIST ABOVE)

                    # generate file_describes_biosample, file_describes_subject, biosample_from_subject
                    # (NEED TO REMOVE FROM EMPTY LIST ABOVE)

                    # generate biosample_gene, biosample_disease, biosample_substance, subject_disease
                    # (NEED TO REMOVE FROM EMPTY LIST ABOVE)

                    # generate anatomy, assay_type, compound, data_type, disease, file_format, gene, ncbi_taxonomy, substance
                    # (NEED TO REMOVE FROM EMPTY LIST ABOVE)

            self._register_computation()
            exitcode = 0
            return exitcode
        finally:
            self._end_time = int(time.time())
            # write a task finish file
            logutils.write_task_finish_json(outdir=self._outdir,
                                            start_time=self._start_time,
                                            end_time=self._end_time,
                                            status=exitcode)

    @staticmethod
    def add_subparser(subparsers):
        """
        Adds a subparser for the C2M2 Creator command.

        :return:
        """
        desc = """

        Version {version}

        {cmd} Generates C2M2 data package and stores it in
        RO-Crate

        """.format(version=cellmaps_utils.__version__,
                   cmd=C2M2Creator.COMMAND)

        parser = subparsers.add_parser(C2M2Creator.COMMAND,
                                       help='Generates C2M2 data package for upload into CFDE',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument('--input', nargs='+',
                            help='One or more input RO-Crates to use as input for'
                                 'C2M2 generation')
        parser.add_argument('--name', default='C2M2Creator',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='unknown',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', default='unknown',
                            help='Name of project running this tool, '
                                 'needed for FAIRSCAPE. Usually set to '
                                 'funding source')
        parser.add_argument('--author',
                            help='Name of author running this tool. If unset,'
                                 'user account running this tool will be used')
        parser.add_argument('--c2m2submitdir', default='draft_C2M2_submission_TSVs',
                            help='Name of directory in output RO-Crate to store C2M2 TSV files. '
                                 'This should match line 44 of prepare_C2M2_submission.py')
        parser.add_argument('--ext_cv_ref', required=True,
                            help='Set to directory that is unzipped copy of external_CV_reference_files from this'
                                 ' URL: https://osf.io/bq6k9')
        parser.add_argument('--skip_logging', action='store_true',
                            help='If set, output.log, error.log '
                                 'files will not be created')
        return parser

