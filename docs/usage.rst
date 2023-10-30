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

Example on how to configure logging for a command line
tool that leverages ``-v`` flag or ``--logconf`` set by
the caller

.. code-block:: python

    todo

Configuring logging into directory/`RO-Crate`_
================================================

Example on how configure logging of all debug and higher
log messages to ``output.log`` and all warning and
higher log messages to ``output.log`` to a directory/`RO-Crate`_

.. code-block:: python

    todo

.. note::

    It is up to logger to clear this logging configuration
    if directory no longer exists

.. _CM4AI: https://cm4ai.org
.. _RO-Crate: https://www.researchobject.org/ro-crate
.. _FAIRSCAPE CLI: https://fairscape.github.io/fairscape-cli
