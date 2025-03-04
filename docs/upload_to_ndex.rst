Uploading interactome and hierarchy to NDEx
=================================================

To properly make use of Cell View and subnetworks vizualization in Cytoscape Web, it is necessary to upload both
interactome and hierarchy. It is important to properly switch network annotations, which is detailed in `HCX`_ format
documentation. Cell Maps Utils package provides a class ``NDExHierarchyUploader`` to simplify the process.

This code block below uses the hierarchy and interactome from `Example 2`_ above.

.. code-block::

    import os
    import ndex2
    from cellmaps_utils.ndexupload import NDExHierarchyUploader

    #Specify NDEx server
    ndexserver = 'www.ndexbio.org''
    ndexuser = '<USER>'
    ndexpassword = '<PASSWORD>'

    # Initialize NDExHierarchyUploader with the specified NDEx server and credentials
    uploader = NDExHierarchyUploader(ndexserver, ndexuser, ndexpassword, visibility=True)

    # Upload the hierarchy and parent network to NDEx
    parent_uuid, parenturl, hierarchy_uuid, hierarchyurl = uploader.save_hierarchy_and_parent_network(hierarchy, interactome)

    print(f"Parent network UUID is {parent_uuid} and its URL in NDEx is {parenturl}")
    print(f"Hierarchy network UUID is {hierarchy_uuid} and its URL in NDEx is {hierarchyurl}")

It is possible to also directly upload from files (this will replace the ``HCX::interactionNetworkName`` network
annotation with ``HCX::interactionNetworkUUID``):

.. code-block::

    import os
    import ndex2
    from cellmaps_utils.ndexupload import NDExHierarchyUploader

    #Specify NDEx server
    ndexserver = 'www.ndexbio.org''
    ndexuser = '<USER>'
    ndexpassword = '<PASSWORD>'

    # Initialize NDExHierarchyUploader with the specified NDEx server and credentials
    uploader = NDExHierarchyUploader(ndexserver, ndexuser, ndexpassword, visibility=True)

    # Upload the hierarchy and parent network to NDEx
    parent_uuid, parenturl, hierarchy_uuid, hierarchyurl = uploader.upload_hierarchy_and_parent_network_from_files(hierarchy_path='path/to/output/hierarchy.cx2', parent_path='path/to/interactome.cx2')

    print(f"Parent network UUID is {parent_uuid} and its URL in NDEx is {parenturl}")
    print(f"Hierarchy network UUID is {hierarchy_uuid} and its URL in NDEx is {hierarchyurl}")

If your hierarchy already has ``HCX::interactionNetworkUUID`` annotation, there is no need to use
``NDExHierarchyUploader`` and it can be directly saved to NDEx:

.. code-block::

    import os
    import ndex2

    #Specify NDEx server
    ndexserver = 'www.ndexbio.org''
    ndexuser = '<USER>'
    ndexpassword = '<PASSWORD>'

    ndexclient = ndex2.client.Ndex2(host=ndexserver, username=ndexuser, password=ndexpassword)
    ndexclient.save_new_cx2_network(hierarchy.to_cx2(), visibility=self._visibility)

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
