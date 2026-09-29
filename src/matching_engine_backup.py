import pandas as pd
from rapidfuzz import fuzz


def safe_text(value):
    """Convert missing values to empty strings."""
    if pd.isna(value):
        return ""
    return str(value).upper().strip()


def calculate_similarity(value_a, value_b):
    """Calculate normalized token similarity between two values."""
    value_a = safe_text(value_a)
    value_b = safe_text(value_b)

    if not value_a or not value_b:
        return 0.0

    return round(
        fuzz.token_set_ratio(value_a, value_b) / 100,
        4,
    )


def calculate_match_score(material_a, material_b):
    """
    Calculate a weighted similarity score between two materials.

    Weights:
    - Description: 50%
    - Material group: 15%
    - Manufacturer: 10%
    - Part number: 15%
    - Unit of measure: 10%
    """

    description_score = calculate_similarity(
        material_a["material_description_normalized"],
        material_b["material_description_normalized"],
    )

    group_score = calculate_similarity(
        material_a["material_group_normalized"],
        material_b["material_group_normalized"],
    )

    manufacturer_score = calculate_similarity(
        material_a["manufacturer_normalized"],
        material_b["manufacturer_normalized"],
    )

    part_number_score = calculate_similarity(
        material_a["part_number_normalized"],
        material_b["part_number_normalized"],
    )

    uom_score = calculate_similarity(
        material_a["unit_of_measure_normalized"],
        material_b["unit_of_measure_normalized"],
    )

    final_score = (
        description_score * 0.50
        + group_score * 0.15
        + manufacturer_score * 0.10
        + part_number_score * 0.15
        + uom_score * 0.10
    )

    return {
        "description_score": description_score,
        "group_score": group_score,
        "manufacturer_score": manufacturer_score,
        "part_number_score": part_number_score,
        "uom_score": uom_score,
        "match_score": round(final_score, 4),
    }


def run_matching_engine(materials_df, candidates_df):
    """Calculate detailed matching scores for candidate pairs."""

    results = []

    material_lookup = materials_df.set_index("material_id").to_dict("index")

    for _, candidate in candidates_df.iterrows():
        material_a = material_lookup[candidate["material_id_a"]]
        material_b = material_lookup[candidate["material_id_b"]]

        scores = calculate_match_score(material_a, material_b)

        result = {
            "material_id_a": candidate["material_id_a"],
            "material_id_b": candidate["material_id_b"],
            "material_group": candidate["material_group"],
            **scores,
        }

        results.append(result)

    return pd.DataFrame(results)


if __name__ == "__main__":
    from src.config import (
        PROCESSED_DATA_FILE,
        OUTPUT_DIR,
        MATCH_RESULTS_FILE,
    )

    materials_df = pd.read_csv(PROCESSED_DATA_FILE)
    candidates_df = pd.read_csv(OUTPUT_DIR / "candidate_pairs.csv")

    results_df = run_matching_engine(materials_df, candidates_df)

    results_df.to_csv(MATCH_RESULTS_FILE, index=False)

    print(f"Calculated match scores for {len(results_df)} candidate pairs.")
    print(f"Saved to: {MATCH_RESULTS_FILE}")