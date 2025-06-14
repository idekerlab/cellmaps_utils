import os
import argparse
import json
import pandas as pd
import re
from collections import defaultdict
from functools import lru_cache
import mygene

CELL_LINES = ['MDA-MB-468', 'Kolf2.1J']

@lru_cache(maxsize=10000)
def query_gene_symbols(ensembl_id_tuple):
    mg = mygene.MyGeneInfo()
    results = mg.querymany(list(ensembl_id_tuple), scopes='ensembl.gene', fields='symbol', species='human')
    mapping = {}
    for entry in results:
        if not entry.get('notfound') and 'symbol' in entry:
            mapping[entry['query']] = entry['symbol']
        else:
            mapping[entry['query']] = f"UNKNOWN:{entry['query']}"
    return mapping

def get_gene_symbols_from_ensembl_ids(ensembl_ids):
    unique_ids = set(ensembl_ids)
    return query_gene_symbols(tuple(unique_ids))

def extract_cell_line_names(json_path):
    known_cell_lines = CELL_LINES
    found = []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def collect_texts(d):
            texts = []
            for value in d.values():
                if isinstance(value, str):
                    texts.append(value)
                elif isinstance(value, list):
                    texts.extend([v for v in value if isinstance(v, str)])
                elif isinstance(value, dict):
                    texts.extend(collect_texts(value))
            return texts

        all_text = collect_texts(data)
        if "@graph" in data and isinstance(data["@graph"], list):
            for entry in data["@graph"]:
                if isinstance(entry, dict):
                    all_text.extend(collect_texts(entry))
        combined_text = " ".join(all_text)

        for cl in known_cell_lines:
            if re.search(rf'\b{re.escape(cl)}\b', combined_text, re.IGNORECASE):
                found.append(cl)

        return sorted(found) if found else ["<not found>"]
    except Exception as e:
        return [f"Error reading file: {e}"]

def find_first_csv_or_tsv(folder):
    for fname in os.listdir(folder):
        if fname.lower().endswith(".csv") or fname.lower().endswith(".tsv"):
            return os.path.join(folder, fname)
    return None

def get_ensembl_ids(file_path):
    try:
        if file_path.endswith(".tsv"):
            df = pd.read_csv(file_path, sep='\t')
        else:
            df = pd.read_csv(file_path)
        if "ENSEMBL ID" in df.columns:
            return df["ENSEMBL ID"].dropna().tolist()
    except Exception:
        pass
    return []

def get_protein_names(file_path):
    try:
        if file_path.endswith(".tsv"):
            df = pd.read_csv(file_path, sep='\t')
        else:
            df = pd.read_csv(file_path)
        if "Bait" in df.columns and "PreyGene.x" in df.columns:
            bait = df["Bait"].dropna().tolist()
            prey = df["PreyGene.x"].dropna().tolist()
            all_proteins = bait + prey
            cleaned = {p.split("_")[0] for p in all_proteins}
            return cleaned
    except Exception:
        pass
    return set()

def count_unique_image_filenames_per_cell_line(images_crates):
    channels = ['blue', 'green', 'red', 'yellow']
    cell_line_to_filenames = defaultdict(set)

    for crate in images_crates:
        crate = crate.strip()
        if not os.path.isdir(crate):
            continue
        metadata_path = os.path.join(crate, "ro-crate-metadata.json")
        if not os.path.isfile(metadata_path):
            continue
        cell_lines = extract_cell_line_names(metadata_path)
        for color in channels:
            color_path = os.path.join(crate, color)
            if not os.path.isdir(color_path):
                continue
            filenames = [f for f in os.listdir(color_path) if os.path.isfile(os.path.join(color_path, f))]
            for cl in cell_lines:
                cell_line_to_filenames[cl].update(filenames)

    return {cl: len(files) for cl, files in cell_line_to_filenames.items()}

def check_and_aggregate_images(images_crates):
    cell_line_to_ensembl = defaultdict(set)

    for path in images_crates:
        path = path.strip()
        metadata_path = os.path.join(path, "ro-crate-metadata.json")
        if not os.path.isfile(metadata_path):
            continue
        cell_lines = extract_cell_line_names(metadata_path)
        if not cell_lines or cell_lines == ["<not found>"]:
            continue
        ensembl_file = find_first_csv_or_tsv(path)
        if not ensembl_file:
            continue
        ensembl_ids = get_ensembl_ids(ensembl_file)
        if not ensembl_ids:
            continue
        for cell_line in cell_lines:
            cell_line_to_ensembl[cell_line].update(ensembl_ids)

    all_gene_symbols = defaultdict(set)
    for cl, ids in cell_line_to_ensembl.items():
        symbol_map = get_gene_symbols_from_ensembl_ids(list(ids))
        all_gene_symbols[cl] = set(symbol_map.values())

    print("\nImages Crates:")
    for cl in CELL_LINES:
        print(f"{cl}: {len(all_gene_symbols[cl])} unique proteins")
    return all_gene_symbols

def check_and_aggregate_interactions(interaction_crates):
    cell_line_to_proteins = defaultdict(set)

    for path in interaction_crates:
        path = path.strip()
        metadata_path = os.path.join(path, "ro-crate-metadata.json")
        if not os.path.isfile(metadata_path):
            continue
        cell_lines = extract_cell_line_names(metadata_path)
        if not cell_lines or cell_lines == ["<not found>"]:
            continue
        interaction_file = find_first_csv_or_tsv(path)
        if not interaction_file:
            continue
        names = get_protein_names(interaction_file)
        if not names:
            continue
        for cell_line in cell_lines:
            cell_line_to_proteins[cell_line].update(names)

    print("\nInteraction Crates:")
    for cl in CELL_LINES:
        print(f"{cl}: {len(cell_line_to_proteins[cl])} unique proteins")
    return cell_line_to_proteins

def save_summary_table(proteins, interactions, image_counts, output_file="statistics.csv"):
    data = []
    differentiation = {
        "MDA-MB-468": ["NA"],
        "Kolf2.1J": ["undifferentiated", "neuron", "cardiomycyte"]
    }

    for cl in CELL_LINES:
        interaction_proteins = interactions.get(cl, set())
        protein_crate_proteins = proteins.get(cl, set())
        total = interaction_proteins.union(protein_crate_proteins)
        image_count = image_counts.get(cl, "")

        for diff in differentiation[cl]:
            row = {
                "Cell Line/Type": cl,
                "Differentiation": diff,
                "Protein interactions detected": len(interaction_proteins),
                "Number of immunofluorescent images": image_count,
                "Number immunofluorescent proteins detected": len(protein_crate_proteins),
                "Number of genes knocked down in perturb seq": "",
                "Total proteins investigated": len(total)
            }
            data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"\n📝 Summary table saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate statistics for datasets")
    parser.add_argument("--interaction_crates", nargs='+', help="List of interaction RO-Crate folder paths.")
    parser.add_argument("--images_crates", nargs='+', help="List of image RO-Crate folder paths.")
    args = parser.parse_args()

    proteins = defaultdict(set)
    interactions = defaultdict(set)
    image_counts = defaultdict(int)

    if args.images_crates:
        proteins = check_and_aggregate_images(args.images_crates)
        image_counts = count_unique_image_filenames_per_cell_line(args.images_crates)

    if args.interaction_crates:
        interactions = check_and_aggregate_interactions(args.interaction_crates)

    print("\nAll:")
    for cl in CELL_LINES:
        union = proteins[cl] | interactions[cl]
        print(f"{cl}: {len(union)} unique proteins")

    save_summary_table(proteins, interactions, image_counts)
