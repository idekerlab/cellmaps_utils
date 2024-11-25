import json
import os
import shutil
import uuid
from datetime import date
import re
import time
import logging
import requests
from requests import RequestException

from tqdm import tqdm
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
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
        self._input_data_dict = theargs.__dict__
        self._name = theargs.name
        self._organization_name = theargs.organization_name
        self._project_name = theargs.project_name
        self._ext_cv_ref = theargs.ext_cv_ref
        self._c2m2_json = None
        self._c2m2_submissiondir = os.path.join(self._outdir, theargs.c2m2submitdir)

    def download_file(self, downloadurl, destfilename, max_retries=3, retry_wait=10):
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

    def run(self):
        """
        Runs the process of CRISPR data loading into a RO-Crate.
        It includes generating the output directory,
        linking and registering h5ad file and registering the
        computation and software used in the process.

        :return:
        """
        if os.path.exists(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        logger.debug('Creating directory ' + str(self._outdir))
        os.makedirs(self._outdir, mode=0o755)

        # download C2M2_datapackage.json and store in RO-Crate
        self._c2m2_json = self.download_file('https://osf.io/download/3sra4', 'C2M2_datapackage.json')

        # download citation for above file
        self.download_file('https://osf.io/3sra4/metadata/?format=datacite-json', 'C2M2_datapackage.json-datacite.json')

        # download external_CV_reference_files and store in RO-Crate
        # https://files.osf.io/v1/resources/bq6k9/providers/osfstorage/611e9cf92dab24014f25ba63/?zip=
        # uncompress external_CV_reference_files directory
        # going to just copy it cause it is too hard to cleanly download
        logger.info('Copying over self._ext_cv_ref')
        shutil.copytree(self._ext_cv_ref, os.path.join(self._outdir, 'external_CV_reference_files'))

        # download prepare_C2M2_submission.py file and store in RO-Crate
        self.download_file('https://osf.io/download/7qdz4',
                           'prepare_C2M2_submission.py')
        self.download_file('https://osf.io/7qdz4/metadata/?format=datacite-json',
                           'prepare_C2M2_submission.py-datacite.json')

        # edit line 44 of prepare_C2M2_submission.py if submission dir is not default name

        # create c2m2submission directory
        os.makedirs(self._c2m2_submissiondir, mode=0o755)

        # generate file

        # generate sample

        # generate subject

        # generate file_describes_biosample, file_describes_subject, biosample_from_subject

        # generate biosample_gene, biosample_disease, biosample_substance, subject_disease

        # generate anatomy, assay_type, compound, data_type, disease, file_format, gene, ncbi_taxonomy, substance

        return 0


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
        parser.add_argument('--name', default='C2M2Creator',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='unknown',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', default='unknown',
                            help='Name of project running this tool, '
                                 'needed for FAIRSCAPE. Usually set to '
                                 'funding source')
        parser.add_argument('--c2m2submitdir', default='draft_C2M2_submission_TSVs',
                            help='Name of directory in output RO-Crate to store C2M2 TSV files. '
                                 'This should match line 44 of prepare_C2M2_submission.py')
        parser.add_argument('--ext_cv_ref', required=True,
                            help='Set to directory that is unzipped copy of external_CV_reference_files from this'
                                 ' URL: https://osf.io/bq6k9')

        return parser

