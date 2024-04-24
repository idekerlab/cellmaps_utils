=====
Usage
=====

Below are examples on how to use the cellmaps_utils package

In a project
-------------

To use cellmaps_utils in a project::

    # for version of package, description, url
    import cellmaps_utils

    # for logging utilities
    from cellmaps_utils import logutils

    # for RO-Crate editing
    from cellmaps_utils.provenance import ProvenanceUtil

    # for constants
    from cellmaps_utils import constants


Registering `RO-Crate`_
==========================

Here is an example on how to create a Research Object Crate (`RO-Crate`_) using
the class `ProvenanceUtil() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil>`__ (a wrapper for `FAIRSCAPE CLI`_) included in this package.
The code below will register an existing directory named ``mycratedir`` in the current working directory
and register it as a `RO-Crate`_. Registering a `RO-Crate`_ entails the creation of a ``ro-crate-metadata.json`` file
containing information passed into the `register_rocrate() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_rocrate>`__ method

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


Registering `software`_ in `RO-Crate`_
=================================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
this example registers `software`_  with `register_software() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_software>`_
This example registers software that is available at a specific URL with `RO-Crate`_ and
sets the id of the software in the ``software_id`` variable.

.. code-block:: python

    import os
    import cellmaps_utils
    from cellmaps_utils.provenance import ProvenanceUtil

    # register software in RO-CRATE
    prov = ProvenanceUtil()
    software_id = prov.register_software('mycratedir', name='cellmaps_utils',
                                         description='Description of software',
                                         author='Bob Smith',
                                         version='1.0',
                                         file_format='py',
                                         url='https://github.com/idekerlab/cellmaps_utils')

Running the above code will add meta data to ``mycratedir/ro-crate-metadata.json`` file

Registering `dataset`_ in `RO-Crate`_
===========================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
this example registers a `dataset`_ (a set of one or more files)
with `register_dataset() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_dataset>`_

.. code-block:: python

    import os
    from datetime import date
    import cellmaps_utils
    from cellmaps_utils.provenance import ProvenanceUtil

    # register created directory as RO-Crate
    prov = ProvenanceUtil()

    # describe file
    dataset_dict = {'name': 'Empty test file',
                    'author': 'Bob Smith',
                    'version': '1.0',
                    'date-published': date.today().strftime(prov.get_default_date_format_str()),
                    'description': 'This is just an empty file',
                    'data-format': 'txt',
                    'keywords': ['file','empty']}

    # create an empty file
    empty_file = os.path.join('mycratedir','emptyfile.txt')
    open(empty_file, 'a').close()

    # register dataset and set skip_copy to True
    # because the file will already exist
    # in RO-Crate
    empty_dataset_id = prov.register_dataset('mycratedir',
                                             data_dict=dataset_dict,
                                             source_file=empty_file,
                                             skip_copy=True)


Running the above code will add meta data to ``mycratedir/ro-crate-metadata.json`` file

Registering `computation`_ in `RO-Crate`_
===============================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
with registered `software`_ and `dataset`_, this examples
registers a `computation`_ with `register_computation() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_computation>`_

.. code-block:: python

    from cellmaps_utils.provenance import ProvenanceUtil

    software_id = '12345'  # faked here, but can be created by register_software() call
    empty_dataset_id = '6789'  # faked here, but can be created by register_dataset() call
    prov = ProvenanceUtil()
    computation_id = prov.register_computation('mycratedir',
                                               name='my computation',
                                               run_by=str(prov.get_login()),
                                               command='configurable for computation',
                                               description='description of computation',
                                               keywords=['example', 'fake', 'computation'],
                                               used_software=[software_id],
                                               generated=[empty_dataset_id])

Running the above code will add meta data to ``mycratedir/ro-crate-metadata.json`` file


Configuring logging for command line
======================================

Example showing how to use the function `logutils.setup_cmd_logging() <cellmaps_utils.html#cellmaps_utils.logutils.setup_cmd_logging>`__
to setup logging levels and configuration for command line tools
that expose a ``-v`` (verbosity) or alternate logging config ``--logconf``:

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

Example on how to use the function `logutils.setup_filelogger() <cellmaps_utils.html#cellmaps_utils.logutils.setup_filelogger>`__ that
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

.. warning::

    It is up to **caller** to clear/remove these added logging handlers
    if directory no longer exists


Cell Maps for AI Data Release
------------------------------

This section describes how to generate a new `CM4AI`_ data release. The
intended audience is for data generation sites and anyone interested in knowing
how the datasets on `CM4AI`_ site are created


Perturbation/CRISPR data release
=================================

The command line tool ``cellmaps_utilscmd.py crisprconverter`` takes a  `h5ad`_ file
and copies that file along with other meta data files into a `RO-Crate`_ suitable
for persistance to `FAIRSCAPE`_ and ultimately publication on `CM4AI`_

The example below generates a `RO-Crate`_ directory under the ``0.1alpha`` folder using
`h5ad`_ file named ``foo.h5ad`` passed in via the ``--h5ad`` flag

.. code-block::

    echo "completely fake h5ad file" > foo.h5ad

    cellmaps_utilscmd.py -vv crisprconverter 0.1alpha --h5ad foo.h5ad --author 'Mali Lab' \
                         --name 'CRISPR' --organization_name 'Mali Lab' \
                         --project_name CM4AI --release '0.1 alpha' --treatment untreated \
                         --dataset 4channel --cell_line KOLF2.1J --gene_set chromatin \
                         --tissue undifferentiated --num_perturb_guides 6 \
                         --num_non_target_ctrls 109 --num_screen_targets 108


Example contents generated by above command:

.. code-block::

    0.1alpha/
    └── cm4ai_chromatin_kolf2.1j_undifferentiated_untreated_crispr_4channel_0.1_alpha
        ├── KOLF2.1J_undifferentiated_untreated_chromatin.h5ad
        ├── dataset_info.json
        ├── readme.txt
        └── ro-crate-metadata.json

.. note::

    Invoke ``cellmaps_utilscmd.py crisperconverter -h`` for usage information

.. warning::

    This tool does not currently validate .h5ad, but when it does the above example
    will fail

Affinity Purification Mass Spectrometry (AP-MS) data release
==================================================================

The command line tool ``cellmaps_utilscmd.py apmsconverter`` consumes one or more `tsv`_ files
that are combined and stored into a `RO-Crate`_ suitable
for persistance to `FAIRSCAPE`_ and ultimately publication on `CM4AI`_

The example below generates a `RO-Crate`_ directory under the ``0.1alpha`` folder using
`tsv`_ file named ``DNMT3A.tsv`` that is passed in via the ``--inputs`` flag


.. code-block::

    echo -ne 'Bait\tPrey\tPreyGene.x\tSpec\tSpecSum\tAvgSpec\tNumReplicates.x\t' > DNMT3A.tsv
    echo -ne 'ctrlCounts\tAvgP.x\tMaxP.x\tTopoAvgP.x\tTopoMaxP.x\tSaintScore.x\t' >> DNMT3A.tsv
    echo -e 'logOddsScore\tFoldChange.x\tBFDR.x\tboosted_by.x' >> DNMT3A.tsv
    echo -ne 'DNMT3A\tO00422\tSAP18_HUMAN\t6|7|8|10\t31\t7.75\t4\t0|0|0|0|0|0|0|0\t' >> DNMT3A.tsv
    echo -e '1\t1\t1\t1\t1\t13.51\t77.5\t0\tNA' >> DNMT3A.tsv
    echo -ne 'DNMT3A\tO00571\tDDX3X_HUMAN\t3|7|11|9\t30\t7.5\t4\t0|1|3|3|0|0|0|0\t' >> DNMT3A.tsv
    echo -e '0.99\t1\t0.99\t1\t0.99\t3.63\t8.57\t0\tNA' >> DNMT3A.tsv

    cellmaps_utilscmd.py apmsconverter 0.1alpha --inputs DNMT3A.tsv \
                         --author 'Krogan Lab' --name 'AP-MS' \
                         --organization_name 'Krogan Lab' --project_name 'CM4AI' \
                         --release '0.1 alpha' --treatment untreated \
                         --cell_line 'MDA-MB-468' --gene_set 'chromatin'

Example contents generated by above command:

.. code-block::

    0.1alpha/
    └── cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha
        ├── apms.tsv
        ├── dataset_info.json
        ├── readme.txt
        └── ro-crate-metadata.json

.. note::

    Invoke ``cellmaps_utilscmd.py apmsconverter -h`` for usage information

.. warning::

    THIS tool does NOT yet add tissue to `RO-Crate`_ directory name!!!

Size Exclusion Chromatography with Mass Spectrometry (SEC-MS) data release
=============================================================================

TODO


Immunofluorescent Image (IFImage) data release
==================================================================

TODO



.. _CM4AI: https://cm4ai.org
.. _RO-Crate: https://www.researchobject.org/ro-crate
.. _FAIRSCAPE CLI: https://fairscape.github.io/fairscape-cli
.. _FAIRSCAPE: https://fairscape.github.io
.. _software: https://fairscape.github.io/fairscape-cli/getting-started/#register-software-metadata
.. _dataset: https://fairscape.github.io/fairscape-cli/getting-started/#register-dataset-metadata
.. _computation: https://fairscape.github.io/fairscape-cli/getting-started/#register-computation-metadata
.. _tar: https://en.wikipedia.org/wiki/Tar_(computing)
.. _gzip: https://en.wikipedia.org/wiki/Gzip
.. _h5ad: https://github.com/scverse/anndata/issues/180
