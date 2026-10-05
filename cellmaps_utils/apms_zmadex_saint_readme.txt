Affinity Purification Mass spectrometry (AP-MS)
-----------------------------------------------

Affinity Purification-Mass Spectrometry (AP-MS) is a powerful technique used to uncover the intricate networks of
protein interactions within cells. Different methods can be used but the most popular approach is to attach a purifiable
tag to a protein of interest, the "bait". In the context of CM4AI the tag is directly attached to the endogenous protein
of interest using gene editing to maintain physiological level of expression. The tagged bait is then purified from cell
extract with its interacting partners. Once separated, the captured proteins are identified using a mass spectrometer
allowing to infer protein-protein interactions.

This RO-Crate uses the Zmadex/SAINT analysis. It does not carry the legacy SAINT columns
(Spec, AvgSpec, TopoAvgP.x, SaintScore.x, logOddsScore and similar), because those values do not
exist in this analysis. Earlier CM4AI AP-MS releases used that older schema and are documented
separately.

@@DATASET_SUMMARY@@


Two different questions, two different sets of columns
------------------------------------------------------

Zmadex, SAINTBFDR* and Pass* measure INTERACTION CONFIDENCE. They answer "is this prey a real
interactor of this bait?" and are computed within a single drug arm.

DrugEffect* measures TREATMENT-ASSOCIATED CHANGE. It answers "does this bait-prey pair change
between vorinostat and DMSO?" and lives in its own file, apms_drug_effect.tsv.

Confusing the two is the most common way to misread this dataset. A prey can be a high confidence
interactor with no drug effect, or show a strong drug effect while failing every interaction
filter.


apms.tsv and apms_unfiltered.tsv column labels
-----------------------------------------------

Both files carry the identical 14 columns. apms.tsv is filtered, apms_unfiltered.tsv is the
complete pre-filter matrix.

Bait: Gene symbol of the pulled down protein.

Prey: Uniprot ID of a protein identified by MS in the pull down (putative bait interactor).
      Always a single accession, never a protein group.

PreyGene: Gene symbol of the identified protein.

Batch: Experimental batch (SET1 through SET6) the measurement belongs to. Batch is part of the
       record key. Two baits, HDAC2 and USP7, were run in two different batches, so Bait and Prey
       together are NOT a unique key. Use Batch, Bait and Prey.

Zmadex: Median absolute deviation based enrichment score of the prey in the bait pull down
        relative to the other pull downs in the batch. Higher means more specific enrichment.

BaitControlLog2FC: Log2 fold change of prey abundance in the tagged bait pull down versus the
                   background/control. Computed WITHIN one drug arm, so it is a measure of
                   bait-prey enrichment, not of drug response.

ObservedCount: Number of replicates in which the prey was observed.

MissingCount: Number of replicates in which the prey was not observed.

SAINTBFDRIntensity: SAINTexpress Bayesian False Discovery Rate computed on intensity. Lower is
                    more confident. A value of 0 is a real and common value, it is not missing
                    data. An EMPTY cell means the statistic could not be computed.

SAINTBFDRSpectralCount: SAINTexpress Bayesian False Discovery Rate computed on spectral counts.
                        Lower is more confident. Same empty/zero distinction as above.

PassZ: TRUE if the prey passes the Zmadex threshold.

PassSAINTIntensity: TRUE if the prey passes the SAINT intensity BFDR threshold.

PassSAINTSpectralCount: TRUE if the prey passes the SAINT spectral count BFDR threshold.

ReferenceLabel: Membership of the bait-prey pair in reference sets used for benchmarking.
                One of corum, string, corum;string, decoy, or empty.
                This is PRIOR KNOWLEDGE used to evaluate the scoring, it is NOT evidence of an
                interaction in this experiment. A pair labelled corum is not thereby a hit, and a
                pair labelled decoy is not thereby a false positive.

A note on empty cells: an empty value means the statistic could not be computed, and is written as
an empty field rather than NA, NaN or 0. It is never safe to read an empty cell as zero.


apms_drug_effect.tsv column labels
-----------------------------------

Present in the vorinostat RO-Crate only. Produced by MSstats. Every record is a single
vorinostat-versus-DMSO contrast for one bait and one prey, so there is one contrast per
Batch/Bait pair, with no drug dimension of its own.

Batch, Bait, Prey: The same key as apms.tsv. Join on all three.

DrugEffectLog2FC: Log2 fold change of prey abundance in the vorinostat pull down versus the DMSO
                  pull down for that bait. Positive means more abundant under vorinostat.
                  Do not confuse this with BaitControlLog2FC, which is bait versus control.

DrugEffectSE: Standard error of the log2 fold change.

DrugEffectTValue: T statistic of the contrast.

DrugEffectDF: Degrees of freedom of the contrast.

DrugEffectPValue: Raw p-value of the contrast.

DrugEffectAdjustedPValue: Multiple testing adjusted p-value.

DrugEffectSignificant: 1 if MSstats called the contrast significant, otherwise 0.

DrugEffect: Categorical call, one of:
            up           - significantly more abundant under vorinostat
            down         - significantly less abundant under vorinostat
            insig        - no significant change
            gained       - detected only under vorinostat, paired with
                           DrugEffectIssue = oneConditionMissing
            lost         - detected only under DMSO, paired with
                           DrugEffectIssue = oneConditionMissing
            unidentified - not detected in either condition, paired with
                           DrugEffectIssue = completeMissing

DrugEffectIssue: Empty, oneConditionMissing, or completeMissing. Explains why DrugEffectLog2FC and
                 the test statistics may be empty.

DrugEffectComparison: The original MSstats contrast label, of the form
                      <Batch>_<Bait>_VRST-<Batch>_<Bait>_DMSO.

Protein groups: where MSstats could not resolve a single protein, Prey holds a semicolon separated
protein group. These rows are published unchanged and are NOT split onto their individual
accessions, because doing so creates ambiguous duplicate keys. They will not match apms.tsv, whose
Prey is always a single accession.


Joining the two files
----------------------

Join on Batch, Bait and Prey. All three are required, because HDAC2 and USP7 each appear in two
batches.

    import pandas as pd

    apms = pd.read_csv('apms.tsv', sep='\t', dtype=str, na_filter=False)
    drug = pd.read_csv('apms_drug_effect.tsv', sep='\t', dtype=str, na_filter=False)
    merged = apms.merge(drug, on=['Batch', 'Bait', 'Prey'], how='left')

Read the files with dtype=str and na_filter=False if you need the values to round trip unchanged.


Data processing
---------------

Raw data acquired on a Orbitrap Fusion(TM) Lumos(TM) Tribrid(TM) Mass Spectrometer (Thermo Scientific).
Raw data are processed using Maxquant using LFQ quantification against a reviewed human UniProt
reference. Evidence files are processed to generate SAINT input, and SAINTexpress is run to
estimate the probability that each observed bait-prey pair is a true interaction rather than a
non-specific or random association. The Zmadex score adds a robust, median absolute deviation
based measure of how specifically a prey is enriched in one bait pull down relative to the others
in its batch. Drug effects are computed separately with MSstats.


References
----------
SAINT: https://saint-apms.sourceforge.net/Main.html
       https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4102138/
       https://pubmed.ncbi.nlm.nih.gov/21131968/
MSstats: https://msstats.org
CM4AI gene sets: https://cm4ai.org/product-documentation/
