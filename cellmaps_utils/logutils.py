
import os
import time
import json
import getpass
import platform
import logging
import argparse
from cellmaps_utils import constants


logger = logging.getLogger(__name__)


def setup_cmd_logging(args):
    """
    Sets up logging based on parsed command line arguments.
    If **args.logconf** is set use that configuration otherwise look
    at **args.verbose** and set logging for this module

    This function assumes the following:

    * **args.logconf** exists and is ``None`` or set to :py:class:`str`
      containing path to logconf file

    * **args.verbose** exists and is set to :py:class:`int` to one of
      these values:

      * ``0`` = no logging
      * ``1`` = critical
      * ``2`` = error
      * ``3`` = warning
      * ``4`` = info
      * ``5`` = debug

    :param args: parsed command line arguments from argparse
    :type args: :py:class:`argparse.Namespace`
    :raises AttributeError: If args is ``None`` or
                            if **args.logconf** is None or missing or
                            if **args.verbose** is None or missing
    """

    if args.logconf is None:
        level = (50 - (10 * args.verbose))
        logging.basicConfig(format=constants.LOG_FORMAT,
                            level=level)
        logger.setLevel(level)
        return

    # logconf was set use that file
    logging.config.fileConfig(args.logconf,
                              disable_existing_loggers=False)


def write_task_start_json(outdir=None, start_time=None,
                          data=None,
                          version=None):
    """
    Writes **task_##_ start.json** file with information about
    what is to be run. The **##** in name is value of **start_time**

    .. code-block::

        from cellmaps_utils import cellmaps_io
        import time

        cellmaps_io.write_task_start_json(outdir='./mydir', start_time=int(time.time()),
                                          data={'someparam': 'some value'},
                                          version='1.0.0')

    :param outdir: directory to write file
    :type outdir: str
    :param start_time: time in seconds since epoch
                       If ``-1`` or ``None`` then value will
                       be set to current time
    :type start_time: int
    :param data: additional data to persist in
    :type data: dict
    :param version: Version of software
    :type version: str
    """
    login = ''
    try:
        login = getpass.getuser()
    except Exception as e:
        logger.error('Unable to get login for user: ' + str(e))

    if start_time is None or start_time == -1:
        start_time = int(time.time())

    task = {'start_time': start_time,
            'version': str(version),
            'pid': str(os.getpid()),
            'outdir': outdir,
            'login': login,
            'cwd': str(os.getcwd()),
            'platform': str(platform.platform()),
            'python': str(platform.python_version()),
            'system': str(platform.system()),
            'uname': str(platform.uname())
            }
    if data is not None:
        task.update(data)

    with open(os.path.join(outdir,
                           'task_' + str(start_time) +
                           '_start.json'), 'w') as f:
        json.dump(task, f, indent=2)


def write_task_finish_json(outdir=None, start_time=None,
                           end_time=None, status=None):
        """
        Writes **task_##_finish.json** file in **outdir** directory
        where **##** is the **start_time** value

        .. code-block::

            from cellmaps_utils import cellmaps_io
            import time

            cellmaps_io.write_task_finish_json(outdir='./mydir', start_time=int(time.time())-10,
                                               end_time=int(time.time()),
                                               status=0)

        :param outdir: directory to write file
        :type outdir: str
        :param start_time: time in seconds since epoch
                           if set to ``-1`` or ``None`` value will be set
                           to current time
        :type start_time: int
        :param end_time: time in seconds since epoch
                         if set to ``-1`` or ``None`` value will be set to
                         current time
        :type end_time: int
        :param status: status of task, ``0`` means success, otherwise error
        :type status: int
        """
        if outdir is None or not os.path.isdir(outdir):
            logger.error('Output directory is not set or not a '
                         'directory, cannot write'
                         'task finish json file')
            return

        if start_time is None or start_time == -1:
            start_time = int(time.time())

        if end_time is None or end_time == -1:
            end_time = int(time.time())
        task = {'end_time': end_time,
                'elapsed_time': int(end_time - start_time),
                'status': str(status)
                }
        with open(os.path.join(outdir,
                               'task_' + str(start_time) +
                               '_finish.json'), 'w') as f:
            json.dump(task, f, indent=2)


def setup_filelogger(outdir=None, handlerprefix='cellmaps'):
    """
    Sets up a logger to write all debug and higher logs
    to output **outdir**/output.log
    and all error level log messages and higher
    to output **outdir**/error.log

    :param outdir: directory where to store ``output.log``
                   and ``error.log`` files
    :type outdir: str
    :param handlerprefix: prefix of name to give to handlers and formatters
    :type handlerprefix: str
    """
    logging.config.dictConfig({'version': 1,
                               'disable_existing_loggers': False,
                               'loggers': {
                                 '': {
                                     'level': 'NOTSET',
                                     'handlers': [handlerprefix + '_file_handler',
                                                  handlerprefix + '_error_file_handler']
                                 }
                               },
                               'handlers': {
                                   handlerprefix + '_file_handler': {
                                       'level': 'DEBUG',
                                       'class': 'logging.FileHandler',
                                       'formatter': handlerprefix + '_formatter',
                                       'filename': os.path.join(outdir, 'output.log'),
                                       'mode': 'a'
                                   },
                                   handlerprefix + '_error_file_handler': {
                                       'level': 'ERROR',
                                       'class': 'logging.FileHandler',
                                       'formatter': handlerprefix + '_formatter',
                                       'filename': os.path.join(outdir, 'error.log'),
                                       'mode': 'a'
                                   }
                               },
                               'formatters': {
                                   handlerprefix + '_formatter': {
                                       'format': constants.LOG_FORMAT
                                   }
                               }
                               })
