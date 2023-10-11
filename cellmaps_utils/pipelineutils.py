import os
import time
import logging
from cellmaps_utils import logutils
from cellmaps_utils.provenance import ProvenanceUtil
from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsError


logger = logging.getLogger(__name__)


class ToolRunner(object):
    """
    Base class for Cell Maps Tools
    """
    def __init__(self,
                 outdir=None,
                 skip_logging=True,
                 input_data_dict=None,
                 provenance_utils=None):
        """
        Constructor

        :param skip_logging: If ``True`` skip logging, if ``None`` or ``False`` do NOT skip logging
        :type skip_logging: bool
        :param provenance:
        :type provenance: dict
        :param input_data_dict:
        :type input_data_dict: dict
        :param provenance_utils: Wrapper for `fairscape-cli <https://pypi.org/project/fairscape-cli>`__
                                 which is used for
                                 `RO-Crate <https://www.researchobject.org/ro-crate>`__ creation and population
        :type provenance_utils: :py:class:`~cellmaps_utils.provenance.ProvenanceUtil`
        """
        if outdir is None:
            raise CellMapsError('outdir is None')
        self._outdir = os.path.abspath(outdir)
        self._start_time = int(time.time())
        self._end_time = -1

        if skip_logging is None:
            self._skip_logging = False
        else:
            self._skip_logging = skip_logging

        self._input_data_dict = input_data_dict
        self._provenance_utils = provenance_utils

    def _create_output_directory(self):
        """
        Creates output directory if it does not already exist

        :raises CellmapsDownloaderError: If output directory is None or if directory already exists
        """
        if os.path.isdir(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        os.makedirs(self._outdir, mode=0o755)
        for cur_color in constants.COLORS:
            cdir = os.path.join(self._outdir, cur_color)
            if not os.path.isdir(cdir):
                logger.debug('Creating directory: ' + cdir)
                os.makedirs(cdir,
                            mode=0o755)

    def _initialize_logging(self, handlerprefix='cellmaps'):
        """

        :param handlerprefix:
        :return:
        """
        if self._skip_logging is False:
            logutils.setup_filelogger(outdir=self._outdir,
                                      handlerprefix=handlerprefix)

    def _write_task_start_json(self, version='NA',
                               input_data_dict=None,
                               data=None):
        """
        Writes task_start.json file with information about
        what is to be run

        :param version: Version of tool
                        (should be __version__ from __init__.py of tool)
        :type version: str
        :param input_data_dict:
        :type input_data_dict: dict
        :param data:
        :type data: dict
        :return:
        """
        if input_data_dict is not None:
            data.update({'commandlineargs': input_data_dict})

        logutils.write_task_start_json(outdir=self._outdir,
                                       start_time=self._start_time,
                                       version=version,
                                       data=data)

    def _write_task_finish_json(self, exitcode):
        """

        :return:
        """
        self._end_time = int(time.time())
        # write a task finish file
        logutils.write_task_finish_json(outdir=self._outdir,
                                        start_time=self._start_time,
                                        end_time=self._end_time,
                                        status=exitcode)

    def run(self):
        """
        Subclasses must implement this
        :raises NotImplementedError: Always raised
        """
        raise NotImplementedError('Subclasses must implement')
