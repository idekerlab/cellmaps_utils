=====
Usage
=====

This page should provide information on how to use cellmaps_utils


In a project
-------------

To use cellmaps_utils in a project::

    import cellmaps_utils





Creating `RO-Crate`_
=====================

Here is an example on how to create a Research Object Crate (`RO-Crate`_) using
the class ``ProvenanceUtils`` (a wrapper for `FAIRSCAPE CLI`_) included in this package.

The code below will register an existing directory named ``mycratedir`` in the current working directory
and register it as a `RO-Crate`_. Registering a `RO-Crate`_ entails the creation of a ``ro-crate-metadata.json`` file
containing information passed into the ``register_rocrate`` method

.. code-block:: python

   import os
   from cellmaps_utils.provenance import ProvenanceUtil

   # create directory
   os.makedirs('mycratedir', mode=0o755)

   # register created directory as RO-Crate
   prov = ProvenanceUtil()
   prov.register_rocrate('mycratedir', name='RO-Crate 1',
                         organization_name='foo_organization', project_name='create_project',
                         description='My First RO-CRATE',
                         keywords=['test', 'rocrate'])

Adding/Registering software to `RO-Crate`_
===========================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
this example registers software

.. code-block:: python

    todo


Adding/Registering dataset to `RO-Crate`_
===========================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
this example registers a dataset (a set of one or more files)

.. code-block:: python

    todo


Adding/Registering computation to `RO-Crate`_
===============================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
with registered software and dataset, this examples
registers a computation

.. code-block:: python

    todo

Configuring logging for command line
======================================

Example showing how to use the function `logutils.setup_cmd_logging()`
to setup logging levels and configuration for command line tools
that expose a `-v` (verbosity) or alternate logging config `--logconf`:

.. code-block:: python

    import argparse
    import logging
    from cellmaps_utils import constants
    from cellmaps_utils import logutils

    logger = logging.getLogger('mytestlogger')

    parser = argparse.ArgumentParser(description='desc of my command',
                                     formatter_class=constants.ArgParseFormatter)
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
    theargs = parser.parse_args(['-vv'])
    logutils.setup_cmd_logging(theargs)
    logger.debug('will not be printed')
    logger.warning('will be printed')

Configuring logging into directory/`RO-Crate`_
================================================

Example on how to use the function `logutils.setup_filelogger()` that
adds handlers to log all messages to ``output.log`` and all warning or
higher log messages to ``error.log`` to a directory/`RO-Crate`_

.. code-block:: python

    import os
    import logging
    from cellmaps_utils import logutils

    logger = logging.getLogger('mytestlogger')

    os.makedirs('mycratedir', mode=0o755)

    logutils.setup_filelogger(outdir='mycratedir',
                              handlerprefix='someprefix')
    # will write debug message to output.log
    logger.debug('Some debug message')

    # will write error message to both output.log & error.log
    logger.error('Some error message')

.. note::

    It is up to logger to clear/remove these added logging handlers
    if directory no longer exists

.. _CM4AI: https://cm4ai.org
.. _RO-Crate: https://www.researchobject.org/ro-crate
.. _FAIRSCAPE CLI: https://fairscape.github.io/fairscape-cli
