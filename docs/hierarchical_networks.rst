Hierarchical networks support (CX2/ HCX)
-----------------------------------------

Cellmaps Utils provide utilities supporting hierarchical networks, generated either by
`Cellmaps Generate Hierarchy <https://cellmaps-generate-hierarchy.readthedocs.io/>`_ or from other sources.

The `CX2`_ format is fully compatible with the Cell Maps tools, making it the recommended format for use. If user has
a network in another common format, the Cell Maps Utils package provides utilities to convert it to CX2.

For hierarchical networks, if the user wishes to display network subsystems in Cytoscape, the necessary format is
`HCX`_ — a specialized version of CX2 with additional annotations. This package includes utilities to facilitate
the seamless creation of HCX format from CX2 networks.

.. toctree::
   :maxdepth: 2

   hidef_converters
   ddot_converters
   cx2_to_hcx_conversion
   upload_to_ndex
   hierarchy_robustness

.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _HCX: https://cytoscape.org/cx/cx2/hcx-specification
