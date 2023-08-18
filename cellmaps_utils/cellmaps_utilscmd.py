#! /usr/bin/env python

import argparse
import sys
import logging
import logging.config
import traceback
import json
import warnings

import cellmaps_utils
from cellmaps_utils import logutils
from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.basecmdtool import HelloWorldCommand
from cellmaps_utils.apmstool import APMSDataLoader


logger = logging.getLogger(__name__)


def _parse_arguments(desc, args):
    """
    Parses command line arguments

    :param desc: description to display on command line
    :type desc: str
    :param args: command line arguments usually :py:func:`sys.argv[1:]`
    :type args: list
    :return: arguments parsed by :py:mod:`argparse`
    :rtype: :py:class:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=constants.ArgParseFormatter)

    subparsers = parser.add_subparsers(dest='command',
                                       help='Command to run. '
                                            'Type <command> -h for '
                                            'more help')
    subparsers.required = True

    HelloWorldCommand.add_subparser(subparsers)
    APMSDataLoader.add_subparser(subparsers)

    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'this format: https://docs.python.org/3/library/'
                             'logging.config.html#logging-config-fileformat '
                             'Setting this overrides -v parameter which uses '
                             ' default logger. (default None)')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module. Messages are '
                             'output at these python logging levels '
                             '-v = ERROR, -vv = WARNING, -vvv = INFO, '
                             '-vvvv = DEBUG, -vvvvv = NOTSET (default no '
                             'logging)')
    parser.add_argument('--version', action='version',
                        version=('%(prog)s ' +
                                 cellmaps_utils.__version__))

    return parser.parse_args(args)


def main(args):
    """
    Main entry point for program

    :param args: arguments passed to command line usually :py:func:`sys.argv[1:]`
    :type args: list

    :return: return value of :py:meth:`cellmaps_imagedownloader.runner.CellmapsImageDownloader.run`
             or ``2`` if an exception is raised
    :rtype: int
    """

    desc = """
Version {version}




    """.format(version=cellmaps_utils.__version__)
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = cellmaps_utils.__version__

    try:
        logutils.setup_cmd_logging(theargs)
        logger.debug('Command is: ' + str(theargs.command))
        if theargs.command == HelloWorldCommand.COMMAND:
            cmd = HelloWorldCommand(theargs)
        elif theargs.command == APMSDataLoader.COMMAND:
            cmd = APMSDataLoader(theargs)
        else:
            raise CellMapsError('Invalid command: ' + str(theargs.command))
        return cmd.run()

    except Exception as e:
        logger.exception('Caught exception: ' + str(e))
        sys.stderr.write('\n\nCaught Exception ' + str(e))
        traceback.print_exc()
        return 2
    finally:
        logging.shutdown()


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
