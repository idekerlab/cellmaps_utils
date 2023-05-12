
import argparse


class ArgParseFormatter(argparse.ArgumentDefaultsHelpFormatter,
                        argparse.RawDescriptionHelpFormatter):
    """
    Combine two :py:class:`argparse` Formatters to get help
    and default values
    displayed when showing help

    """
    pass


LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
             "%(filename)s::%(funcName)s():%(lineno)d %(message)s"
"""
Sets format of logging messages
"""

RO_CRATE_METADATA_FILE = 'ro-crate-metadata.json'
"""
`rocrate <https://www.researchobject.org/ro-crate>`__ metadata JSON file name
"""

TASK_FILE_PREFIX = 'task_'
"""
Prefix for task file
"""

TASK_START_FILE_SUFFIX = '_start.json'
"""
Suffix for task start file
"""

TASK_FINISH_FILE_SUFFIX = '_finish.json'
"""
Suffix for task finish file
"""

OUTPUT_LOG_FILE = 'output.log'
"""
Output log file name
"""

ERROR_LOG_FILE = 'error.log'
"""
Error log file name
"""

IMAGE_EMBEDDING_FILE = 'image_emd.tsv'
"""
Name of image embedding file
"""

PPI_EMBEDDING_FILE = 'ppi_emd.tsv'
"""
Name of Protein to Protein embedding file
"""

CO_EMBEDDING_FILE = 'coembedding_emd.tsv'
"""
Name of file containing coembedding
"""

IMAGE_GENE_NODE_ATTR_FILE = 'image_gene_node_attributes.tsv'
"""
Image gene node attributes filename
"""

IMAGE_GENE_NODE_ERRORS_FILE = 'image_gene_node_attributes.errors'
"""
Image gene node attributes errors filename
"""

IMAGE_GENE_NODE_NAME_COL = 'name'
"""
Gene Symbol name column
"""

IMAGE_GENE_NODE_REPRESENTS_COL = 'represents'
"""
Ensembl ids column
"""

IMAGE_GENE_NODE_AMBIGUOUS_COL = 'ambiguous'
"""
Ambiguous column
"""

IMAGE_GENE_NODE_ANTIBODY_COL = 'antibody'
"""
Antibody name column
"""

IMAGE_GENE_NODE_FILENAME_COL = 'filename'
"""
File name column
"""

IMAGE_GENE_NODE_COLS = [IMAGE_GENE_NODE_NAME_COL,
                        IMAGE_GENE_NODE_REPRESENTS_COL,
                        IMAGE_GENE_NODE_AMBIGUOUS_COL,
                        IMAGE_GENE_NODE_ANTIBODY_COL,
                        IMAGE_GENE_NODE_FILENAME_COL]
"""
Columns in :py:const:`IMAGE_GENE_NODE_ATTR_FILE` file
"""

PPI_EDGELIST_FILE = 'ppi_edgelist.tsv'
"""
Protein to Protein interaction edgelist file name
"""

PPI_EDGELIST_GENEA_COL = 'geneA'
"""
First column name
"""

PPI_EDGELIST_GENEB_COL = 'geneB'
"""
Second column name
"""

PPI_EDGELIST_COLS = [PPI_EDGELIST_GENEA_COL,
                     PPI_EDGELIST_GENEB_COL]
"""
Columns in :py:const:`PPI_EDGELIST_FILE`
"""

WEIGHTED_PPI_EDGELIST_WEIGHT_COL = 'Weight'
"""
weight column
"""

WEIGHTED_PPI_EDGELIST_COLS = [PPI_EDGELIST_GENEA_COL,
                              PPI_EDGELIST_GENEB_COL,
                              WEIGHTED_PPI_EDGELIST_WEIGHT_COL]

PPI_GENE_NODE_ATTR_FILE = 'ppi_gene_node_attributes.tsv'
"""
Protein to Protein gene node attributes file
"""

PPI_GENE_NODE_COLS = ['name', 'represents', 'ambiguous', 'bait']
"""
Columns in :py:const:`PPI_GENE_NODE_ATTR_FILE`
"""

PPI_GENE_NODE_ERRORS_FILE = 'ppi_gene_node_attributes.errors'
"""
Protein to Protein gene node attributes error filename
"""

PPI_NETWORK_PREFIX = 'ppi'

HIERARCHY_NETWORK_PREFIX = 'hierarchy'
"""
CX format hierarchy filename
"""

CX_SUFFIX = '.cx'
"""
Suffix for files in `CX <https://cytoscape.org/cx/specification/2022/01/11/cytoscape-exchange-format-specification-(version-1).html>`__ format
"""

CX2_SUFFIX = '.cx2'
"""
Suffix for files in `CX 2.0<https://cytoscape.org/cx/cx2/specification/2022/12/01/cytoscape-exchange-format-specification-(version-2).html>`__ format
"""

HCX_SUFFIX = '.hcx'
"""
Suffix for files in `HCX <https://cytoscape.org/cx>`__ format
"""

RED = 'red'
"""
Red color directory name and color name
in red color files
"""

BLUE = 'blue'
"""
Blue color directory name and color name
in blue color files
"""
GREEN = 'green'
"""
Green color directory name and color name
in green color files
"""

YELLOW = 'yellow'
"""
Yellow color directory name and color name
in yellow color files
"""

COLORS = [RED, BLUE, GREEN, YELLOW]
"""
List of colors
"""


