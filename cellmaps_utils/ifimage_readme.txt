This data set has been generated in the Emma Lundberg lab (https://ell-core.stanford.edu/)
as part of the CM4AI Research Program (https://cm4ai.org/).

This data set displays the spatial localization of proteins in the cell line MDA-MB-468.
MDA-MB-468 cells were seeded into 96-well glass bottom plates
and treated either with the chemotherapeutic drug Paclitaxel or with the chemotherapeutic
drug Vorinostat (SAHA) or not treated. For drug treatment, higher cell numbers were
seeded than for the cells that were not treated to reach a sufficient amount of
remaining cells at the end of the experiment (treatment with Paclitaxel or Vorinostat
disturbs cell growth). After fixation of the cells with PFA, for each protein, the
subcellular distribution of the protein was investigated by immunofluorescence-based
staining (ICC-IF) and confocal microscopy. Each well was stained with
DAPI (to label nuclei, "blue" channel),
a Calreticulin antibody (to label the endoplasmic reticulum, "yellow" channel),
a Tubulin antibody (to label Microtubuli, "red" channel), and an antibody against a
protein of interest (a different antibody / protein for each well, "green" channel).
In the green channel, for each well, each one of the proteins was stained with an antibody
from the proteinatlas.org project.

The .tsv file describes each image in the data set. Each row represents one image.
The columns describe the staining from which the image was taken:
"Antibody ID" describes the antibody ID for the antibody applied to stain the protein
visible in the "green" channel. The antibody ID can be looked up at proteinatlas.org
to find out more information about the antibody.
"ENSEMBL ID" indicates the ENSEMBL ID(s) of the gene(s) of the proteins visualized
in the "green" channel.

Treatment refers to how the cells that are depicted in the image were treated
(with Paclitaxel, Vorinostat, or untreated)
"Well" refers to the well coordinate on the 96-well plate
"Region" is a unique identifier for the position in the well, where the cells were acquired.
