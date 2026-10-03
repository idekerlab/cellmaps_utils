Size Exclusion Mass Spectrometry (SEC-MS)
-----------------------------------------------

Size Exclusion Chromatography-Mass Spectrometry (SEC-MS) is a technique used to
identify protein complexes and characterize protein-protein interactions based
on how proteins separate by size. Cell extracts are first separated by size
exclusion chromatography, which distributes proteins and protein complexes
across a series of fractions according to their apparent molecular size.
Large protein assemblies generally elute in earlier fractions, while
smaller complexes and individual proteins elute later.

Each fraction is then analyzed by mass spectrometry to identify and
quantify the proteins present. Proteins that consistently co-elute
across the same fractions are likely to be members of the same protein
complex or to participate in related molecular assemblies. Computational
analysis of these co-elution profiles can therefore be used to infer
protein-protein interactions and reconstruct protein complexes.

Data processing
---------------

Raw SEC-MS data were acquired on a timsTOF Pro 2 mass spectrometer. Each
size exclusion chromatography (SEC) experiment was separated into 72
fractions, with each fraction analyzed independently by mass spectrometry.

Raw mass spectrometry data were processed using Spectronaut for peptide
and protein identification and quantification. Spectronaut protein-level
output was used to obtain the abundance of each detected protein across the
SEC fractions. These measurements were organized into a wide-format protein
abundance matrix, where each row represents a protein and each quantitative
column represents an SEC fraction.

The series of protein abundance measurements across fractions defines the
SEC elution profile for each protein. Proteins belonging to the same protein
complex tend to co-elute during size exclusion chromatography and therefore
exhibit similar elution profiles. These profiles can be used in downstream
analyses to identify co-eluting proteins, infer protein-protein interactions
and protein complexes, and detect changes in protein complex organization
between experimental conditions.

For the CM4AI MDA-MB-468 dataset, SEC-MS profiling was performed for untreated
cells and cells treated with paclitaxel or vorinostat, enabling comparison of
protein complex organization in response to drug treatment.

secms_#.tsv column labels (# is replicate number, in case of cm4ai, technical)
-------------------------------------------------------------------------------

PG.ProteinLabel:	Spectronaut protein-group label used to identify the
                    quantified protein or protein group.

PG.ProteinGroups:	Protein group identifier assigned by Spectronaut; may
                    represent one or more proteins that cannot be distinguished
                    by the observed peptides.

PG.ProteinAccessions:	Protein accession identifier(s) associated with the
                        protein group, typically from the reference protein
                        database.

PG.Genes:	Gene symbol(s) corresponding to the protein(s) in the protein group.

PG.UniProtIds:	UniProt identifier(s) associated with the protein group.

[#] Biosep_XXX.PG.Quantity:	Protein-group abundance reported by
                            Spectronaut for this LC-MS run/sample. The portion
                            before .PG.Quantity identifies the source raw-data
                            file/run.



Note: Columns ending in .PG.Quantity contain the quantitative protein-group
      abundance values for individual SEC-MS fractions/runs; one such
      column is present for each measured fraction/sample.

TODO: Obtain how .PG.Quantity is calculated.







