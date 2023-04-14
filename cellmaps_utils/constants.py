
import argparse

class ArgParseFormatter(argparse.ArgumentDefaultsHelpFormatter,
                        argparse.RawDescriptionHelpFormatter):
    """
    Combine two :py:class:`argparse` Formatters to get help
    and default values
    displayed when showing help

    """
    pass


LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
             "%(filename)s::%(funcName)s():%(lineno)d %(message)s"
"""
Sets format of logging messages
"""

TASK_FILE_PREFIX = 'task_'
"""
Prefix for task file
"""

TASK_START_FILE_SUFFIX = '_start.json'
"""
Suffix for task start file
"""

TASK_FINISH_FILE_SUFFIX = '_finish.json'
"""
Suffix for task finish file
"""

OUTPUT_LOG_FILE = 'output.log'
"""
Output log file name
"""

ERROR_LOG_FILE = 'error.log'
"""
Error log file name
"""

