DDOT Converters
=====================


DDOT converters facilitate the transformation between CX2 and DDOT formats for both interaction networks and
hierarchical networks. The DDOT format is structurally similar to HiDeF but is commonly used for representing
interactomes and ontologies.

**Example 1: Converting a CX2 Interaction Network to DDOT Format**

To convert a CX2 interactome into a DDOT file, use the InteractomeToDDOTConverter class:

.. code-block::

    from cellmaps_utils.ddotconverter import InteractomeToDDOTConverter

    converter = InteractomeToDDOTConverter(
        output_dir="path/to/output",
        interactome_path="path/to/interactome.cx2"
    )
    converter.generate_ddot_format_file()

Expected Output: ``interactome_ddot.txt``

.. code-block::

    GeneA    GeneB    interaction_type
    GeneC    GeneD    interaction_type

**Example 2: Converting a DDOT Interaction Network Back to CX2**

To convert a DDOT interactome into a CX2 format, use the DDOTToInteractomeConverter class:

.. code-block::

    from cellmaps_utils.ddotconverter import DDOTToInteractomeConverter

    converter = DDOTToInteractomeConverter(
        output_dir="path/to/output",
        interactome_ddot_path="path/to/interactome_ddot.txt"
    )
    converter.generate_interactome_file()

Expected Output: ``interactome.cx2``

**Example 3: Converting a CX2 Hierarchical Network to DDOT Ontology Format**

To convert a hierarchical network (CX2) into DDOT ontology format, use HierarchyToDDOTConverter:

.. code-block::

    from cellmaps_utils.ddotconverter import HierarchyToDDOTConverter

    converter = HierarchyToDDOTConverter(
        output_dir="path/to/output",
        hierarchy_path="path/to/hierarchy.cx2"
    )
    converter.generate_ontology_ddot_file()

Expected Output: ``ontology.ont``

.. code-block::

    Cluster1    Cluster2    default
    Cluster1    GeneA    gene

**Example 4: Converting a DDOT Ontology Back to a CX2 Hierarchical Network**

To convert a DDOT ontology into CX2 hierarchical format (HCX), use DDOTToHierarchyConverter:

.. code-block::

    from cellmaps_utils.ddotconverter import DDOTToHierarchyConverter

    converter = DDOTToHierarchyConverter(
        output_dir="path/to/output",
        ontology_ddot_path="path/to/ontology.ont",
        parent_ddot_path="path/to/interactome_ddot.txt"  # Optional: Parent interactome
    )
    converter.generate_hierarchy_hcx_file()

Expected Output:

- ``hierarchy.cx2`` – The reconstructed hierarchical network.
- ``hierarchy_parent.cx2`` (if parent interactome was used).


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
