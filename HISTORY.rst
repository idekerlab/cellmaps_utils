=======
History
=======

0.5.0 (TBD)
------------------

* Add ``HiDeFToHierarchyConverter``, a class to convert a edge list and node list
  in HiDeF format to hierarchy in HCX.
* Add ``InteractomeToDDOTConverter`` and ``DDOTToInteractomeConverter``, classes to convert network in
  CX2 format to DDOT format and vice versa, ``HierarchyToDDOTConverter`` and ``DDOTToHierarchyConverter``,
  classes to convert hierarchy network in HCX format to DDOT and vice versa.

0.4.0 (2024-07-02)
-------------------

* Updated provenance utils, added checks in for missing data in input RO-Crate,
  and allowing to continue but logging errors in the process

* Add ``HierarchyToHiDeFConverter``, a class to convert a hierarchy network
  (in CX2 format) to a HiDeF format nodes and edges lists.

* Add ``NDExHierarchyUploader``, a class for uploading hierarchy and
  its parent network to NDEx.

* Updated ``cellmaps_utilscmd.py`` ``apmsconverter``, ``ifconverter``,
  ``crisprconverter`` to support tissue as well as output
  ``data_info.json`` file to resulting RO-Crate so subsequent tools can
  more easily get provenance information


* Updated ``cellmaps_utilscmd.py crisprconverter`` to consume ``.h5ad``
  files and updated readme.txt file

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
