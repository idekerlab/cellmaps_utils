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

The code below will create a directory name ``mycratedir`` in the current working directory
and register it as a `RO-Crate`_ which entails the creation of a ``ro-crate-metadata.json`` file
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


Editing `RO-Crate`_
=====================

todo

Logging
========


.. _CM4AI: https://cm4ai.org
.. _RO-Crate: https://www.researchobject.org/ro-crate
.. _FAIRSCAPE CLI: https://fairscape.github.io/fairscape-cli
