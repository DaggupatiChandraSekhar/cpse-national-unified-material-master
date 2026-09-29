import pandas as pd
from rapidfuzz import fuzz


def generate_candidates(df, description_threshold=45):
    """
    Generate candidate material pairs using description similarity.

    Materials are compared only within the same material group.
    """

    candidates = []

    for i in range(len(df)):
        material_a = df.iloc[i]

        for j in range(i + 1, len(df)):
            material_b = df.iloc[j]

            # Compare materials within the same category.
            if material_a["material_group_normalized"] != material_b["material_group_normalized"]:
                continue

            description_score = fuzz.token_set_ratio(
                material_a["material_description_normalized"],
                material_b["material_description_normalized"],
            )

            if description_score >= description_threshold:
                candidates.append({
                    "material_id_a": material_a["material_id"],
                    "material_id_b": material_b["material_id"],
                    "description_score": round(description_score / 100, 4),
                    "material_group": material_a["material_group"],
                })

    return pd.DataFrame(candidates)


if __name__ == "__main__":
    from src.config import PROCESSED_DATA_FILE, OUTPUT_DIR

    df = pd.read_csv(PROCESSED_DATA_FILE)

    candidates_df = generate_candidates(df)

    output_file = OUTPUT_DIR / "candidate_pairs.csv"
    candidates_df.to_csv(output_file, index=False)

    print(f"Generated candidate pairs: {len(candidates_df)}")
    print(f"Saved to: {output_file}")