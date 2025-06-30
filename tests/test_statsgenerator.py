import unittest
import tempfile
import os
import json
from unittest.mock import patch

import pandas as pd
from cellmaps_utils.statsgenerator import (
    extract_cell_line_names,
    find_first_csv_or_tsv,
    get_ensembl_ids,
    count_unique_image_filenames_per_cell_line,
    get_protein_names,
    save_summary_table,
    generate_dataset_statistics
)

class TestDatasetStatistics(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_extract_cell_line_names_found(self):
        metadata = {
            "@graph": [{"description": "Experiment using MDA-MB-468 cell line"}]
        }
        file_path = os.path.join(self.base_path, "ro-crate-metadata.json")
        with open(file_path, "w") as f:
            json.dump(metadata, f)

        result = extract_cell_line_names(file_path)
        self.assertEqual(result, ["MDA-MB-468"])

    def test_extract_cell_line_names_not_found(self):
        metadata = {
            "@graph": [{"description": "No matching cell line"}]
        }
        file_path = os.path.join(self.base_path, "ro-crate-metadata.json")
        with open(file_path, "w") as f:
            json.dump(metadata, f)

        result = extract_cell_line_names(file_path)
        self.assertEqual(result, ["<not found>"])

    def test_find_first_csv_or_tsv(self):
        file_path = os.path.join(self.base_path, "data.tsv")
        with open(file_path, "w") as f:
            f.write("ENSEMBL ID\nENSG000001234\n")

        found = find_first_csv_or_tsv(self.base_path)
        self.assertTrue(found.endswith("data.tsv"))

    def test_get_ensembl_ids(self):
        df = pd.DataFrame({"ENSEMBL ID": ["ENSG000001", "ENSG000002"]})
        file_path = os.path.join(self.base_path, "mock.csv")
        df.to_csv(file_path, index=False)

        result = get_ensembl_ids(file_path)
        self.assertEqual(result, ["ENSG000001", "ENSG000002"])

    def test_count_unique_image_filenames_per_cell_line(self):
        meta = {
            "@graph": [{"name": "image crate for Kolf2.1J"}]
        }
        metadata_path = os.path.join(self.base_path, "ro-crate-metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(meta, f)

        # Setup: image file in "green"
        green_path = os.path.join(self.base_path, "green")
        os.makedirs(green_path)
        with open(os.path.join(green_path, "img1.png"), "w") as f:
            f.write("fake image")

        result = count_unique_image_filenames_per_cell_line([self.base_path])
        self.assertEqual(result["Kolf2.1J"], 1)

    def test_get_protein_names(self):
        df = pd.DataFrame({
            "Bait": ["TP53_abc", "BRCA1_123"],
            "PreyGene.x": ["EGFR_1", "MYC_test"]
        })
        file_path = os.path.join(self.base_path, "interact.csv")
        df.to_csv(file_path, index=False)

        result = get_protein_names(file_path)
        self.assertEqual(result, {"TP53", "BRCA1", "EGFR", "MYC"})

    def test_save_summary_table(self):
        proteins = {"MDA-MB-468": {"A", "B"}, "Kolf2.1J": {"X", "Y"}}
        interactions = {"MDA-MB-468": {"B", "C"}, "Kolf2.1J": {"Y"}}
        image_counts = {"MDA-MB-468": 4, "Kolf2.1J": 10}

        file_path = os.path.join(self.base_path, "output.csv")
        save_summary_table(proteins, interactions, image_counts, output_file=file_path)

        df = pd.read_csv(file_path)
        self.assertEqual(len(df), 4)  # 1 MDA + 3 Kolf2 rows
        self.assertIn("Total proteins investigated", df.columns)
        self.assertEqual(df[df["Cell Line/Type"] == "MDA-MB-468"]["Total proteins investigated"].values[0], 3)

    def test_generate_dataset_statistics_workflow(self):
        # Setup minimal image crate
        img_dir = os.path.join(self.base_path, "blue")
        os.makedirs(img_dir)
        with open(os.path.join(img_dir, "img.tif"), "w") as f:
            f.write("fake")

        # Add metadata with a cell line
        with open(os.path.join(self.base_path, "ro-crate-metadata.json"), "w") as f:
            json.dump({"@graph": [{"name": "Study with Kolf2.1J"}]}, f)

        # Add ENSEMBL file
        df = pd.DataFrame({"ENSEMBL ID": ["ENSG000001"]})
        df.to_csv(os.path.join(self.base_path, "table.tsv"), sep="\t", index=False)

        # Patch gene symbol lookup to avoid mygene dependency
        with patch("cellmaps_utils.statsgenerator.get_gene_symbols_from_ensembl_ids") as mock_mapper:
            mock_mapper.return_value = {"ENSG000001": "TESTGENE"}
            generate_dataset_statistics(images_crates=[self.base_path], interaction_crates=[])

if __name__ == "__main__":
    unittest.main()
