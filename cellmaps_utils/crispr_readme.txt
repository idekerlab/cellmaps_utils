@@H5AD@@ file
-----------------------------------------------------------
cell line: @@CELL_LINE@@
screening modality: perturb seq using CRISPR-dCas9-ZIM3
screen targets: @@NUM_SCREEN_TARGETS_AND_GENE_SET@@ genes
non-targeting controls: @@NUM_NON_TARGET_CTRLS@@
number of guides per perturbation: @@NUM_PERTURB_GUIDES@@
treatment: @@TREATMENT@@
processing done: https://www.sc-best-practices.org/conditions/perturbation_modeling.html#analysing-single-pooled-crispr-screens All steps from this guide, up to but not including section 19.4.5.
data type: anndata object (.h5ad)
additional notes: the .X layer of the Anndata object is already set to the X_pert layer output from the mixscape pipeline



