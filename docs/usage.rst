=====
Usage
=====

Below are examples on how to use the cellmaps_utils package

In a project (RO-Crate)
------------------------

To use cellmaps_utils in a project::

    # for version of package, description, url
    import cellmaps_utils

    # for logging utilities
    from cellmaps_utils import logutils

    # for RO-Crate editing
    from cellmaps_utils.provenance import ProvenanceUtil

    # for constants
    from cellmaps_utils import constants


Registering `RO-Crate`_
==========================

Here is an example on how to create a Research Object Crate (`RO-Crate`_) using
the class `ProvenanceUtil() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil>`__ (a wrapper for `FAIRSCAPE CLI`_) included in this package.
The code below will register an existing directory named ``mycratedir`` in the current working directory
and register it as a `RO-Crate`_. Registering a `RO-Crate`_ entails the creation of a ``ro-crate-metadata.json`` file
containing information passed into the `register_rocrate() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_rocrate>`__ method

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


Registering `software`_ in `RO-Crate`_
=================================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
this example registers `software`_  with `register_software() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_software>`_
This example registers software that is available at a specific URL with `RO-Crate`_ and
sets the id of the software in the ``software_id`` variable.

.. code-block:: python

    import os
    import cellmaps_utils
    from cellmaps_utils.provenance import ProvenanceUtil

    # register software in RO-CRATE
    prov = ProvenanceUtil()
    software_id = prov.register_software('mycratedir', name='cellmaps_utils',
                                         description='Description of software',
                                         author='Bob Smith',
                                         version='1.0',
                                         file_format='py',
                                         url='https://github.com/idekerlab/cellmaps_utils')

Running the above code will add meta data to ``mycratedir/ro-crate-metadata.json`` file

Registering `dataset`_ in `RO-Crate`_
===========================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
this example registers a `dataset`_ (a set of one or more files)
with `register_dataset() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_dataset>`_

.. code-block:: python

    import os
    from datetime import date
    import cellmaps_utils
    from cellmaps_utils.provenance import ProvenanceUtil

    # register created directory as RO-Crate
    prov = ProvenanceUtil()

    # describe file
    dataset_dict = {'name': 'Empty test file',
                    'author': 'Bob Smith',
                    'version': '1.0',
                    'date-published': date.today().strftime(prov.get_default_date_format_str()),
                    'description': 'This is just an empty file',
                    'data-format': 'txt',
                    'keywords': ['file','empty']}

    # create an empty file
    empty_file = os.path.join('mycratedir','emptyfile.txt')
    open(empty_file, 'a').close()

    # register dataset and set skip_copy to True
    # because the file will already exist
    # in RO-Crate
    empty_dataset_id = prov.register_dataset('mycratedir',
                                             data_dict=dataset_dict,
                                             source_file=empty_file,
                                             skip_copy=True)


Running the above code will add meta data to ``mycratedir/ro-crate-metadata.json`` file

Registering `computation`_ in `RO-Crate`_
===============================================

Assuming a `RO-Crate`_ named ``mycratedir`` already exists
with registered `software`_ and `dataset`_, this examples
registers a `computation`_ with `register_computation() <cellmaps_utils.html#cellmaps_utils.provenance.ProvenanceUtil.register_computation>`_

.. code-block:: python

    from cellmaps_utils.provenance import ProvenanceUtil

    software_id = '12345'  # faked here, but can be created by register_software() call
    empty_dataset_id = '6789'  # faked here, but can be created by register_dataset() call
    prov = ProvenanceUtil()
    computation_id = prov.register_computation('mycratedir',
                                               name='my computation',
                                               run_by=str(prov.get_login()),
                                               command='configurable for computation',
                                               description='description of computation',
                                               keywords=['example', 'fake', 'computation'],
                                               used_software=[software_id],
                                               generated=[empty_dataset_id])

Running the above code will add meta data to ``mycratedir/ro-crate-metadata.json`` file


Configuring logging for command line
======================================

Example showing how to use the function `logutils.setup_cmd_logging() <cellmaps_utils.html#cellmaps_utils.logutils.setup_cmd_logging>`__
to setup logging levels and configuration for command line tools
that expose a ``-v`` (verbosity) or alternate logging config ``--logconf``:

.. code-block:: python

    import argparse
    import logging
    from cellmaps_utils import constants
    from cellmaps_utils import logutils

    logger = logging.getLogger('mytestlogger')

    parser = argparse.ArgumentParser(description='desc of my command',
                                     formatter_class=constants.ArgParseFormatter)
    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'this format: https://docs.python.org/3/library/'
                             'logging.config.html#logging-config-fileformat '
                             'Setting this overrides -v parameter which uses '
                             ' default logger. (default None)')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module. Messages are '
                             'output at these python logging levels '
                             '-v = ERROR, -vv = WARNING, -vvv = INFO, '
                             '-vvvv = DEBUG, -vvvvv = NOTSET (default no '
                             'logging)')
    theargs = parser.parse_args(['-vv'])
    logutils.setup_cmd_logging(theargs)
    logger.debug('will not be printed')
    logger.warning('will be printed')

Configuring logging into directory/`RO-Crate`_
================================================

Example on how to use the function `logutils.setup_filelogger() <cellmaps_utils.html#cellmaps_utils.logutils.setup_filelogger>`__ that
adds handlers to log all messages to ``output.log`` and all warning or
higher log messages to ``error.log`` to a directory/`RO-Crate`_

.. code-block:: python

    import os
    import logging
    from cellmaps_utils import logutils

    logger = logging.getLogger('mytestlogger')

    os.makedirs('mycratedir', mode=0o755)

    logutils.setup_filelogger(outdir='mycratedir',
                              handlerprefix='someprefix')
    # will write debug message to output.log
    logger.debug('Some debug message')

    # will write error message to both output.log & error.log
    logger.error('Some error message')

.. warning::

    It is up to **caller** to clear/remove these added logging handlers
    if directory no longer exists


Cell Maps for AI Data Release
------------------------------

This section describes how to generate a new `CM4AI`_ data release. The
intended audience is for data generation sites and anyone interested in knowing
how the datasets on `CM4AI`_ site are created.

There are four steps to the data release:

1) Each individual dataset must be run through ``cellmaps_utilscmd.py XX``
   command to generate `RO-Crate`_ directories.

2) These `RO-Crate`_ directories must be compressed

3) ``cellmaps_utilscmd.py rocratetable`` must be given these compressed `RO-Crate`_ files to generate table

4) Compressed `RO-Crate`_ files must be uploaded to `CM4AI`_

5) The table generated must be sent to admin of `CM4AI`_ site so they can load it and
   display the new data release


1) Perturbation/CRISPR data release (step 1 above)
===================================================

The command line tool ``cellmaps_utilscmd.py crisprconverter`` takes a  `h5ad`_ file
and copies that file along with other meta data files into a `RO-Crate`_ suitable
for persistance to `FAIRSCAPE`_ and ultimately publication on `CM4AI`_

The example below generates a `RO-Crate`_ directory under the ``0.1alpha`` folder using
`h5ad`_ file named ``foo.h5ad`` passed in via the ``--h5ad`` flag

.. code-block::

    echo "completely fake h5ad file" > foo.h5ad

    cellmaps_utilscmd.py -vv crisprconverter 0.1alpha --h5ad foo.h5ad --author 'Mali Lab' \
                         --name 'CRISPR' --organization_name 'Mali Lab' \
                         --project_name CM4AI --release '0.1 alpha' --treatment untreated \
                         --dataset 4channel --cell_line KOLF2.1J --gene_set chromatin \
                         --tissue undifferentiated --num_perturb_guides 6 \
                         --num_non_target_ctrls 109 --num_screen_targets 108


Example contents generated by above command:

.. code-block::

    0.1alpha/
    └── cm4ai_chromatin_kolf2.1j_undifferentiated_untreated_crispr_4channel_0.1_alpha
        ├── perturbation.h5ad
        ├── dataset_info.json
        ├── readme.txt
        └── ro-crate-metadata.json

.. note::

    Invoke ``cellmaps_utilscmd.py crisperconverter -h`` for usage information

.. warning::

    This tool does not currently validate .h5ad, but when it does the above example
    will fail

1) Affinity Purification Mass Spectrometry (AP-MS) data release
============================================================================

The command line tool ``cellmaps_utilscmd.py apmsconverter`` consumes one or more `tsv`_ files
that are combined and stored into a `RO-Crate`_ suitable
for persistance to `FAIRSCAPE`_ and ultimately publication on `CM4AI`_

The example below generates a `RO-Crate`_ directory under the ``0.1alpha`` folder using
`tsv`_ file named ``DNMT3A.tsv`` that is passed in via the ``--inputs`` flag


.. code-block::

    echo -ne 'Bait\tPrey\tPreyGene.x\tSpec\tSpecSum\tAvgSpec\tNumReplicates.x\t' > DNMT3A.tsv
    echo -ne 'ctrlCounts\tAvgP.x\tMaxP.x\tTopoAvgP.x\tTopoMaxP.x\tSaintScore.x\t' >> DNMT3A.tsv
    echo -e 'logOddsScore\tFoldChange.x\tBFDR.x\tboosted_by.x' >> DNMT3A.tsv
    echo -ne 'DNMT3A\tO00422\tSAP18_HUMAN\t6|7|8|10\t31\t7.75\t4\t0|0|0|0|0|0|0|0\t' >> DNMT3A.tsv
    echo -e '1\t1\t1\t1\t1\t13.51\t77.5\t0\tNA' >> DNMT3A.tsv
    echo -ne 'DNMT3A\tO00571\tDDX3X_HUMAN\t3|7|11|9\t30\t7.5\t4\t0|1|3|3|0|0|0|0\t' >> DNMT3A.tsv
    echo -e '0.99\t1\t0.99\t1\t0.99\t3.63\t8.57\t0\tNA' >> DNMT3A.tsv

    cellmaps_utilscmd.py apmsconverter 0.1alpha --inputs DNMT3A.tsv \
                         --author 'Krogan Lab' --name 'AP-MS' \
                         --organization_name 'Krogan Lab' --project_name 'CM4AI' \
                         --release '0.1 alpha' --treatment untreated \
                         --cell_line 'MDA-MB-468' --gene_set 'chromatin'

Example contents generated by above command:

.. code-block::

    0.1alpha/
    └── cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha
        ├── apms.tsv
        ├── dataset_info.json
        ├── readme.txt
        └── ro-crate-metadata.json

.. note::

    Invoke ``cellmaps_utilscmd.py apmsconverter -h`` for usage information


1) Size Exclusion Chromatography with Mass Spectrometry (SEC-MS) data release
==========================================================================================

TODO


1) Immunofluorescent Image (IFImage) data release
==================================================================

The command line tool ``cellmaps_utilscmd.py ifconverter`` consumes a  `csv`_ file
that contains image links and other information to download and stored into a `RO-Crate`_ suitable
for persistance to `FAIRSCAPE`_ and ultimately publication on `CM4AI`_

The example below generates a `RO-Crate`_ directory under the ``0.1alpha`` folder using
`csv`_ file named ``example.csv`` that is passed in via the ``--inputs`` flag


.. code-block::

    # be sure to download this file: https://github.com/idekerlab/cellmaps_utils/raw/main/examples/iftool/example.csv
    # and name it example.csv
    wget https://github.com/idekerlab/cellmaps_utils/raw/main/examples/iftool/example.csv

    cellmaps_utilscmd.py ifconverter 0.1alpha --input example.csv \
                         --author 'Lundberg Lab' --name 'IF images' \
                         --organization_name 'Lundberg Lab' --project_name 'CM4AI' \
                         --release '0.1 alpha' --treatment paclitaxel \
                         --cell_line 'MDA-MB-468' --gene_set 'chromatin'

Example contents generated by above command:

.. code-block::

    0.1alpha/
    └── cm4ai_chromatin_mda-mb-468_paclitaxel_ifimage_0.1_alpha
        ├── antibody_gene_table.tsv
        ├── blue
        │   └── B2AI_1_Paclitaxel_C1_R1_z01_blue.jpg
        ├── dataset_info.json
        ├── green
        │   └── B2AI_1_Paclitaxel_C1_R1_z01_green.jpg
        ├── readme.txt
        ├── red
        │   └── B2AI_1_Paclitaxel_C1_R1_z01_red.jpg
        ├── ro-crate-metadata.json
        └── yellow
            └── B2AI_1_Paclitaxel_C1_R1_z01_yellow.jpg

.. note::

    Invoke ``cellmaps_utilscmd.py ifconverter -h`` for usage information

2) Compress `RO-Crate`_ from step one
=========================================

In this step the `RO-Crate`_ directories are compressed into files.

.. note::

    The code fragment below assumes all `RO-Crate`_ directories were put into ``0.1alpha``
    directory.

.. code-block::

    # assuming all RO-Crates above were put into 0.1alpha directory
    cd 0.1alpha

    for Y in `find . -name "*_*" -maxdepth 1 -type d` ; do
      echo $Y
      tar -cz $Y > ${Y}.tar.gz
    done

If examples above were run then the ``0.1alpha`` directory will look like this:

.. code-block::

    .
    ├── cm4ai_chromatin_kolf2.1j_undifferentiated_untreated_crispr_4channel_0.1_alpha
    ├── cm4ai_chromatin_kolf2.1j_undifferentiated_untreated_crispr_4channel_0.1_alpha.tar.gz
    ├── cm4ai_chromatin_mda-mb-468_paclitaxel_ifimage_0.1_alpha
    ├── cm4ai_chromatin_mda-mb-468_paclitaxel_ifimage_0.1_alpha.tar.gz
    ├── cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha
    └── cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha.tar.gz

3) Run ``cellmaps_utilscmd.py rocratetable`` on `RO-Crate`_ files
===================================================================

In this step, the `RO-Crate`_ files are examined and a table is generated
that can be sent to the `CM4AI`_ site admin to show the new data release

.. note::

    The code fragment below assumes all `RO-Crate`_ directories were put into ``0.1alpha``
    directory.

.. code-block::

    # assuming all RO-Crates above were put into 0.1alpha directory
    # along with gzip files

    cd 0.1alpha

    cellmaps_utilscmd.py rocratetable table --downloadurlprefix 'https://cm4ai.org/Data/' --rocrates `/bin/ls | grep -v ".gz"`


The above command will create a directory named ``table`` and within that directory
will be a `tsv`_ file named ``data.tsv``

.. code-block::

    table
    └── data.tsv


Contents of `tsv`_ ``data.tsv`` file:

.. code-block::

    FAIRSCAPE ARK ID	Date	Version	Type	Cell Line	Tissue	Treatment	Gene set	Generated By Software	Name	Description	KeywordDownload RO-Crate Data Package	Download RO-Crate Data Package Size MB	Generated By Software	Output Dataset	Responsible Lab
    d4d80b1d-8d49-4204-8c0d-209c5b9ccdf2:cm4ai_chromatin_kolf2.1j_undifferentiated_untreated_crispr_4channel_0.1_alpha	2024-04-29	0.1 alpha	Data	KOLF2.1J	undifferentiated	untreated	chromatin		CRISPR	CM4AI 0.1 alpha KOLF2.1J untreated CRISPR undifferentiated 4channel chromatin	CM4AI,0.1 alpha,KOLF2.1J,untreated,CRISPR,undifferentiated,4channel,chromatin	https://cm4ai.org/Data/cm4ai_chromatin_kolf2.1j_undifferentiated_untreated_crispr_4channel_0.1_alpha.tar.gz	1	Mali Lab
    134e01c8-90ea-457d-9e6e-ca046ecc860f:cm4ai_chromatin_mda-mb-468_paclitaxel_ifimage_0.1_alpha	2024-04-29	0.1 alpha	Data	MDA-MB-468	breast; mammary gland	paclitaxel	chromatin		IF images	CM4AI 0.1 alpha MDA-MB-468 paclitaxel IF microscopy images breast; mammary gland chromatin	CM4AI,0.1 alpha,MDA-MB-468,paclitaxel,IF microscopy,images,breast; mammary gland,chromatin	https://cm4ai.org/Data/cm4ai_chromatin_mda-mb-468_paclitaxel_ifimage_0.1_alpha.tar.gz	1	Lundberg Lab
    7240c7d7-327c-423c-834d-1e99ab8a417b:cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha	2024-04-29	0.1 alpha	Data	MDA-MB-468	breast; mammary gland	untreated	chromatin		AP-MS	CM4AI 0.1 alpha MDA-MB-468 untreated breast; mammary gland AP-MS edgelist chromatin	CM4AI,0.1 alpha,MDA-MB-468,untreated,breast; mammary gland,AP-MS edgelist,chromatin	https://cm4ai.org/Data/cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha.tar.gz	1			Krogan Lab

.. note::

    ``cellmaps_utilscmd.py rocratetable`` runs way faster if the uncompressed
    `RO-Crate`_ directories are passed in. The script does need the ``.gz``
    files in the same directory to get file sizes output in the generated
    table.


4) Upload `RO-Crate`_ files
=============================

For this step the `RO-Crate`_ files ending with ``.gz`` should be uploaded to path matching
prefix set via ``--downloadurlprefix`` in Step 3

.. note::

    Be sure to verify URLs resolve for uploaded files



5) Send table from Step 4 to admin of `CM4AI`_ site
======================================================

In this step send the ``table/data.tsv`` file to `CM4AI`_ admin
and let them know if this table is to append or overwrite existing
data


Hierarchical networks support (CX2/ HCX)
-----------------------------------------

The `CX2`_ format is fully compatible with the Cell Maps tools, making it the recommended format for use. If user has
a network in another common format, the Cell Maps Utils package provides utilities to convert it to CX2.

For hierarchical networks, if the user wishes to display network subsystems in Cytoscape, the necessary format is
`HCX`_ — a specialized version of CX2 with additional annotations. This package includes utilities to facilitate
the seamless creation of HCX format from CX2 networks.

Cell Maps Utils package provide utility for simple

1) HiDeF Converters
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

2) DDOT Converters
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

3) CX2 to HCX conversion
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

4) Uploading interactome and hierarchy to NDEx
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


4) Hierarchy Robustness
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
