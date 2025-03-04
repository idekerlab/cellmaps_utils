Hierarchy Robustness
=========================

Understanding the robustness of hierarchical networks is crucial in evaluating their stability. The ``HierarchyDiff``
class provides methods to assess the robustness of communities by measuring their overlap across multiple alternative
hierarchies. This approach assigns a robustness score to each node based on Jaccard similarity, quantifying the extent
to which nodes remain stable in different hierarchical structures.

The robustness score is calculated as the fraction of alternative hierarchies where a node's Jaccard Index (JI) exceeds
a predefined threshold. The higher the overlap across alternative hierarchies, the higher the robustness score.

The ``HierarchyDiff`` offers additional methods to compare different versions of hierarchies to assess
their structural similarities that can be found in the `Reference`_ section.

**Example: Computing Hierarchy Robustness**

*Step 1*: To calculate robustness first run ``cellmaps_generate_hierarchy`` N number of times. In this example,
we run it 300 times, and each time we randomly remove 10% of edges from the Protein-Protein Interaction Network.

.. code-block::

    from cellmaps_generate_hierarchy.ppi import CosineSimilarityPPIGenerator
    from cellmaps_generate_hierarchy.hierarchy import CDAPSHiDeFHierarchyGenerator
    from cellmaps_generate_hierarchy.maturehierarchy import HiDeFHierarchyRefiner
    from cellmaps_generate_hierarchy.hcx import HCXFromCDAPSCXHierarchy
    from cellmaps_generate_hierarchy.runner import CellmapsGenerateHierarchy
    import os

    # Specify coembedding directories
    inputdir1 = 'coembedding_dir1'
    inputdir2 = 'coembedding_dir2'

    # Create directories where results from N runs will be saved
    bootstrapped_hierarchies_dir = 'bootstrapped_hierarchies'
    os.mkdir(bootstrapped_hierarchies_dir)


    ppigen = CosineSimilarityPPIGenerator(embeddingdirs=[inputdir1, inputdir2])
    refiner = HiDeFHierarchyRefiner()
    converter = HCXFromCDAPSCXHierarchy()

    # Set ``bootstrap_edges`` to 10 to randomly remove 10% of edges
    hiergen = CDAPSHiDeFHierarchyGenerator(refiner=refiner,
                                           hcxconverter=converter,
                                           bootstrap_edges=10)
    # Generate hierarchy N (N=300) times
    for i in range(300):
        x = CellmapsGenerateHierarchy(outdir=f"{bootstrapped_hierarchies_dir}/hierarchydir_{i}",
                                      inputdirs=[inputdir1, inputdir2],
                                      ppigen=ppigen,
                                      hiergen=hiergen)
        x.run()

*Step 2*: Use ``compute_hierarchy_robustness`` method to compute robustness and annotate hierarchy with robustness score

.. code-block::

    from cellmaps_utils.hierdiff import HierarchyDiff

    # Specify path to reference hierarchy (usually hierarchy generated without bootstrapping edges)
    reference_hierarchy_path = 'path/to/reference/hierarchy.cx2'

    # Make a list with paths of alternative hierarchies (from step 1)
    hierarchy_file_name = 'hierarchy.cx2'
    alternative_hierarchy_paths = []
    for i in range(300):
        alternative_hierarchy_paths.append(f"{bootstrapped_hierarchies_dir}/hierarchydir_{i}/{hierarchy_file_name}")

    # Compute robustness and annotate hierarchy with robustness score
    diff = HierarchyDiff()
    robust_hierarchy = diff.compute_hierarchy_robustness(reference_hierarchy_path, alternative_hierarchy_paths)

    # Save hierarchy annotated with robustness score
    robust_hierarchy.write_as_raw_cx2("path/to/output/annotated_hierarchy.cx2")

Expected Output: ``annotated_hierarchy.cx2`` – A hierarchical network with robustness scores added to each node.


*Alternative way to run ``cellmaps_generate_hierarchy`` N (N=300) times using bash script*

.. code-block:: bash

    #!/bin/bash -l
    #SBATCH --output=./outfile/generate_hierarchy.%A_%a.out
    #SBATCH --error=./errfile/generate_hierarchy.%A_%a.err
    #SBATCH --job-name=generate_hierarchy
    #SBATCH --partition="nrnb-compute"
    #SBATCH --time=100:00:00
    #SBATCH --array=1-300%5
    #SBATCH --mem=100G
    #SBATCH --cpus-per-task=8

    echo "My SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID

    source activate cellmaps_toolkit

    output_hierarchy='./existing_output_directory/hierarchydir_'$SLURM_ARRAY_TASK_ID

    cellmaps_generate_hierarchycmd.py $output_hierarchy --coembedding_dirs ./path/to/coembedding_dir1 ./path/to/coembedding_dir_2 --bootstrap_edges 10


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
