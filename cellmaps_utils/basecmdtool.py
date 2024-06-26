# -*- coding: utf-8 -*-
import json
import os
import sys
import argparse
import logging
import cellmaps_utils
from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsError

logger = logging.getLogger(__name__)


class BaseCommandLineTool(object):
    """
    Base class for all command line tools.
    Command line tools MUST subclass this
    """

    COMMAND = 'BaseCommandLineTool'

    def __init__(self):
        """
        Constructor
        """
        pass

    def save_dataset_info_to_json(self, outdir, info_dict, file_name):
        """
        Saves project information to a JSON file.

        :param outdir: Output directory where the file will be saved
        :param info_dict: Dictionary with dataset information
        :param file_name: Name of the file to save the information.
        """

        json_str = json.dumps(info_dict, indent=4)

        json_file_path = os.path.join(outdir, file_name)

        with open(json_file_path, 'w') as json_file:
            json_file.write(json_str)

    def run(self):
        """
        Should contain logic that will be run by command line tool.
        This must be implemented by sub classes and will always raise
        an error

        :raises CellMapsError: will always raise this
        :return:
        """
        raise CellMapsError('Must be implemented by subclass')

    @staticmethod
    def add_subparser(subparsers):
        """
        Should add any argparse commandline arguments to **subparsers** passed in
        This must be implemented by sub classes and will always raise
        an error

        :param subparsers:
        :type subparsers: argparse
        :return:
        """
        raise CellMapsError('Must be implemented by subclass')


class HelloWorldCommand(BaseCommandLineTool):
    """
    Simply prints Hello World and returns 0 always
    """
    COMMAND = 'helloworld'

    def __init__(self, theargs):
        """

        :param theargs:
        """
        super().__init__()

    def run(self):
        """

        :return:
        """
        sys.stdout.write('Hello world\n')
        return 0

    def add_subparser(subparsers):
        """

        :return:
        """
        desc = """

        Version {version}

        {cmd} prints Hello world and exits
        """.format(version=cellmaps_utils.__version__,
                   cmd=HelloWorldCommand.COMMAND)

        parser = subparsers.add_parser(HelloWorldCommand.COMMAND,
                                       help='Prints Hello world and exits',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)

        return parser
