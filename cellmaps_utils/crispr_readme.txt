@@PREFIX@@_feature_reference.csv
@@FEATURE_REF_UNDERLINE@@

This file contains the list of CRISPRi guide RNAs used for this screen and serves as feature
reference dictionary when aligning single-cell RNA expression libraries. With this analysis the
Cell bacrcode ID can be linked back to gRNA expres sed in that cell.

Meaning of values in filenames mentioned below
----------------------------------------------

Meaning of values within filename
C9 Clone 9 of md (had to screen dozens of clones)
S6, S16 => when run on sequencer (sample number)
L004 => lane on chip
R1 (forward), R2 (3' to 5') =>  For sample sequenced in both directions (need both)

@@PREFIX@@_CRISPRi... files
@@CRISPR_UNDERLINE@@


Feature guide capture. This set of FASTQ file contain the sequences of the
guide RNA linked to the cell barcode.

@@PREFIX@@_scRNAseq... files
@@SCRNA_UNDERLINE@@

Single-cell RNA expression library. This set of FASTQ file contains single-cell RNA expression
data.




