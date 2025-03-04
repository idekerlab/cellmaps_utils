CX2 to HCX conversion
=========================

The CX2 to HCX conversion process enhances a CX2 hierarchical network by adding HCX-specific annotations.
The HCX format is a specialized version of CX2 that enables hierarchical visualization in Cytoscape,
ensuring that relationships and interactome information are properly structured.

Why Convert to HCX?

- Enables hierarchical network visualization in Cytoscape.
- Adds interactome annotations to define relationships.
- Supports integration with NDEx, allowing retrieval of interactome data.

**Example 1: Converting a CX2 Hierarchical Network to HCX**

To convert a CX2 hierarchical network into an HCX format, use the ``convert_hierarchical_network_to_hcx`` function:

.. code-block::

    from cellmaps_utils.hcx_utils import convert_hierarchical_network_to_hcx

    hierarchy_path = "path/to/hierarchy.cx2"
    interactome_url = "https://www.ndexbio.org/network/uuid"

    hcx_network = convert_hierarchical_network_to_hcx(
        hierarchy=hierarchy_path,
        interactome_url=interactome_url
    )

    hcx_network.write_as_raw_cx2("path/to/output/hierarchy_hcx.cx2")

Expected Output: ``hierarchy_hcx.cx2`` – The HCX hierarchical network, enriched with interactome annotations.

.. _Example 2:

**Example 2: Converting a CX2 Hierarchy with a Local Interactome**

If you have a local interactome file instead of an NDEx link, you can still convert a CX2 hierarchy to HCX:

.. code-block::

    from ndex2.cx2 import RawCX2NetworkFactory
    from cellmaps_utils.hcx_utils import add_hcx_network_annotations, add_hcx_members_annotation, add_isroot_node_attribute, get_root_nodes

    hierarchy_path = "path/to/hierarchy.cx2"
    interactome_path = "path/to/interactome.cx2"

    # Load hierarchy network and interactome
    factory = RawCX2NetworkFactory()
    hierarchy = factory.get_cx2network(hierarchy_path)
    interactome = factory.get_cx2network(interactome_path)

    # Add HCX annotations
    hierarchy = add_hcx_network_annotations(hierarchy, interactome=interactome, outdir='path/to/output/')

    # Add HCX::members attribute to node attributes
    add_hcx_members_annotation(hierarchy, interactome)

    # Add isRoot attribute to node attributes
    add_isroot_node_attribute(hierarchy, get_root_nodes(hierarchy))

    # Save HCX file
    hierarchy.write_as_raw_cx2("path/to/output/hierarchy.cx2")

Expected Output (Hierarchy and interactome will be saved in the same directory ``path/to/output/``):

- ``hierarchy_hcx.cx2`` – HCX hierarchical network with interactome annotations.
- ``hierarchy_parent.cx2``

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
