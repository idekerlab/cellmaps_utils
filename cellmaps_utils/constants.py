
import argparse


LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
             "%(filename)s::%(funcName)s():%(lineno)d %(message)s"
"""
Sets format of logging messages
"""


class ArgParseFormatter(argparse.ArgumentDefaultsHelpFormatter,
                        argparse.RawDescriptionHelpFormatter):
    """
    Combine two :py:class:`argparse` Formatters to get help
    and default values
    displayed when showing help

    """
    pass
