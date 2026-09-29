import pandas as pd


def create_harmonized_mapping(materials_df, evaluated_df):
    """
    Create harmonized material groups from high-confidence matches.
    """

    materials_df = materials_df.copy()
    evaluated_df = evaluated_df.copy()

    materials_df["harmonized_material_id"] = materials_df["material_id"]

    high_confidence_matches = evaluated_df[
        evaluated_df["decision"] == "MATCH"
    ].sort_values(
        "match_score",
        ascending=False,
    )

    for _, match in high_confidence_matches.iterrows():
        material_a = match["material_id_a"]
        material_b = match["material_id_b"]

        group_a = materials_df.loc[
            materials_df["harmonized_material_id"] == material_a,
            "harmonized_material_id",
        ]

        group_b = materials_df.loc[
            materials_df["harmonized_material_id"] == material_b,
            "harmonized_material_id",
        ]

        if group_a.empty or group_b.empty:
            continue

        canonical_id = min(group_a.iloc[0], group_b.iloc[0])

        materials_df.loc[
            materials_df["harmonized_material_id"].isin(
                [group_a.iloc[0], group_b.iloc[0]]
            ),
            "harmonized_material_id",
        ] = canonical_id

    return materials_df


if __name__ == "__main__":
    from src.config import (
        PROCESSED_DATA_FILE,
        MATCH_RESULTS_FILE,
        OUTPUT_DIR,
        HARMONIZED_RESULTS_FILE,
    )

    materials_df = pd.read_csv(PROCESSED_DATA_FILE)
    evaluated_df = pd.read_csv(OUTPUT_DIR / "evaluated_matches.csv")

    harmonized_df = create_harmonized_mapping(
        materials_df,
        evaluated_df,
    )

    harmonized_df.to_csv(HARMONIZED_RESULTS_FILE, index=False)

    print(f"Harmonized records: {len(harmonized_df)}")
    print(f"Unique harmonized materials: {harmonized_df['harmonized_material_id'].nunique()}")
    print(f"Saved to: {HARMONIZED_RESULTS_FILE}")