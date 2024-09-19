@@H5AD@@ file
-----------------------------------------------------------

This file is a .h5ad file. Details about the data structure of this format
can be found here: https://anndata.readthedocs.io/en/latest/. This data is
a cell x gene matrix, with all preprocesing steps done in accordance to
single cell best practices guide
(https://www.sc-best-practices.org/conditions/perturbation_modeling.html#analysing-single-pooled-crispr-screens)
up to section 19.4.5. The .X layer is set to the 'X_pert' output of the
mixscape pipeline.

cell line: @@CELL_LINE@@
screening modality: perturb seq using CRISPR-dCas9-ZIM3
screen targets: @@NUM_SCREEN_TARGETS_AND_GENE_SET@@ genes
non-targeting controls: @@NUM_NON_TARGET_CTRLS@@
number of guides per perturbation: @@NUM_PERTURB_GUIDES@@
treatment: @@TREATMENT@@


