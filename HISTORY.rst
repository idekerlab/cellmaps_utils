=======
History
=======

0.4.0 (TBD)
-------------------

* Updated ``cellmaps_utilscmd.py crisprconverter`` to consume ``.h5ad``
  files and to support tissue as well as output ``dataset_info.json`` file
  to resulting RO-Crate so subsequent tools can more easily get provenance
  information

0.3.0 (2024-04-15)
-------------------

* Bumped fairscape-cli dependency to ``0.2.0``


0.2.0 (2024-02-20)
------------------

* Bumped fairscape-cli dependency to ``0.1.14`` to support schemas

* Added support for ``schema`` to **data_dict** parameter in ``ProvenanceUtil.register_dataset()``

* Added ``--release`` flag to ``cellmaps_utilscmd.py rocratetable`` and
  in output table renamed "Name of Computation" to "Name" as well as
  added "Type", "Cell Line", "Treatment", "Gene set", and "Version" to
  table output

* Set default logging level to ``ERROR`` for ``cellmaps_utilscmd.py`` command

0.1.0 (2024-01-01)
------------------

* First release on PyPI.
