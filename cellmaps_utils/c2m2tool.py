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


        return parser

