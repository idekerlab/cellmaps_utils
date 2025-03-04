HiDeF Converters
=====================

HiDeF converters are designed to facilitate the transformation between CX2 and HiDeF network formats. These converters
allow users to generate HiDeF-compatible files (.nodes and .edges) from hierarchical networks in CX2 format, as well as
reconstruct hierarchical networks in HCX format from HiDeF data. This is particularly useful for integrating
hierarchical networks into Cytoscape while maintaining structural annotations.

**Example: Converting a CX2 Hierarchy to HiDeF Format**

To convert a CX2 hierarchical network into HiDeF format, use the HierarchyToHiDeFConverter class:

.. code-block::

    from cellmaps_utils.hidefconverter import HierarchyToHiDeFConverter

    converter = HierarchyToHiDeFConverter(input_dir="path/to/cx2_network", output_dir="path/to/output")
    nodes_file, edges_file = converter.generate_hidef_files()

This will produce two files:

- ``hidef_output_gene_names.nodes`` – containing node attributes
- ``hidef_output_gene_names.edges`` – defining hierarchical relationships

**Example: Converting HiDeF Files to an HCX Hierarchical Network**

To convert HiDeF files into an HCX hierarchical network, the HiDeFToHierarchyConverter should be used.

.. code-block::

    from cellmaps_utils.hidefconverter import HiDeFToHierarchyConverter

    converter = HiDeFToHierarchyConverter(
        output_dir="path/to/output",
        nodes_file_path="path/to/hidef_output_gene_names.nodes",
        edges_file_path="path/to/hidef_output_gene_names.edges",
        parent_edgelist_path="path/to/parent_network.edgelist"
    )
    converter.generate_hierarchy_hcx_file()

Expected Output:

- ``hierarchy.cx2`` – The reconstructed hierarchical network in HCX format.
- ``hierarchy_parent.cx2`` – The corresponding interactome (if a parent network was specified).


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
.. _tsv: https://en.wikipedia.org/wiki/Tab-separated_values
.. _csv: https://en.wikipedia.org/wiki/Comma-separated_values
.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _HCX: https://cytoscape.org/cx/cx2/hcx-specification
.. _Reference: https://cellmaps-utils.readthedocs.io/en/latest/cellmaps_utils.html#cellmaps-utils-hierdiff-hierarchy-comparison-module
