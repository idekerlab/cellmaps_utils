
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

IMAGE_GENE_NODE_ATTR_FILE = 'image_gene_node_attributes.tsv'
"""
Image gene node attributes filename
"""

IMAGE_GENE_NODE_ERRORS_FILE = 'image_gene_node_attributes.errors'
"""
Image gene node attributes errors filename
"""

IMAGE_GENE_NODE_COLS = ['name', 'represents', 'ambiguous',
                        'antibody', 'filename']
"""
Columns in :py:const:`IMAGE_GENE_NODE_ATTR_FILE` file
"""

PPI_EDGELIST_FILE = 'ppi_edgelist.tsv'
"""
Protein to Protein interaction edgelist file name
"""

PPI_EDGELIST_COLS = ['geneA', 'geneB']
"""
Columns in :py:const:`PPI_EDGELIST_FILE`
"""

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


