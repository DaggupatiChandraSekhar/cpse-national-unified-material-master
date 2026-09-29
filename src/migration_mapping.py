import pandas as pd

from src.config import (
    HARMONIZED_RESULTS_FILE,
    REVIEW_QUEUE_FILE,
    OUTPUT_DIR,
)


def _safe_read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def _ensure_review_columns(review_queue):
    defaults = {
        "review_status": "PENDING",
        "review_priority": "MEDIUM",
        "reviewer": "",
        "review_comment": "",
        "approved_harmonized_id": "",
        "reviewed_at": "",
    }

    review_queue = review_queue.copy()

    for column, default in defaults.items():
        if column not in review_queue.columns:
            review_queue[column] = default

    return review_queue


def _build_review_lookup(review_queue):
    """
    Create a material-level lookup from pair-level review records.
    """

    review_queue = _ensure_review_columns(review_queue)

    records = []

    for _, row in review_queue.iterrows():
        material_ids = [
            row.get("material_id_a"),
            row.get("material_id_b"),
        ]

        for material_id in material_ids:
            if pd.isna(material_id):
                continue

            records.append(
                {
                    "material_id": str(material_id),
                    "review_status": str(
                        row.get("review_status", "PENDING")
                    ).upper(),
                    "review_priority": row.get(
                        "review_priority", "MEDIUM"
                    ),
                    "reviewer": row.get("reviewer", ""),
                    "review_comment": row.get("review_comment", ""),
                    "approved_harmonized_id": row.get(
                        "approved_harmonized_id", ""
                    ),
                    "reviewed_at": row.get("reviewed_at", ""),
                    "match_score": row.get("match_score", None),
                }
            )

    if not records:
        return pd.DataFrame(
            columns=[
                "material_id",
                "review_status",
                "review_priority",
                "reviewer",
                "review_comment",
                "approved_harmonized_id",
                "reviewed_at",
                "match_score",
            ]
        )

    lookup = pd.DataFrame(records)

    status_order = {
        "APPROVED": 0,
        "REJECTED": 1,
        "ESCALATED": 2,
        "PENDING": 3,
    }

    lookup["_status_order"] = lookup["review_status"].map(
        status_order
    ).fillna(4)

    lookup = lookup.sort_values(
        by=["material_id", "_status_order"]
    ).drop_duplicates(
        subset=["material_id"],
        keep="first",
    )

    return lookup.drop(columns=["_status_order"])


def build_migration_mapping(harmonized, review_queue):
    """
    Build the migration mapping and apply human review outcomes.
    """

    required_columns = [
        "material_id",
        "material_description",
        "material_group",
        "source_cpse",
        "plant",
        "harmonized_material_id",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in harmonized.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns in harmonized results: "
            + ", ".join(missing_columns)
        )

    mapping = harmonized[required_columns].copy()

    mapping["material_id"] = mapping["material_id"].astype(str)

    mapping["mapping_status"] = "AUTO_MATCHED"
    mapping["match_score"] = None
    mapping["review_required"] = False
    mapping["review_status"] = ""
    mapping["review_priority"] = ""
    mapping["reviewer"] = ""
    mapping["review_comment"] = ""
    mapping["reviewed_at"] = ""
    mapping["approved_harmonized_id"] = ""

    review_lookup = _build_review_lookup(review_queue)

    if not review_lookup.empty:
        mapping = mapping.merge(
            review_lookup,
            on="material_id",
            how="left",
            suffixes=("", "_review"),
        )

        review_columns = [
            "review_status",
            "review_priority",
            "reviewer",
            "review_comment",
            "reviewed_at",
            "approved_harmonized_id",
            "match_score",
        ]

        for column in review_columns:
            review_column = f"{column}_review"

            if review_column in mapping.columns:
                if column == "match_score":
                    mapping[column] = mapping[review_column]
                else:
                    mapping[column] = (
                        mapping[review_column]
                        .fillna(mapping[column])
                    )

                mapping = mapping.drop(
                    columns=[review_column]
                )

    mapping["review_status"] = (
        mapping["review_status"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    review_mask = mapping["review_status"].isin(
        ["PENDING", "ESCALATED"]
    )

    approved_mask = mapping["review_status"].eq("APPROVED")

    rejected_mask = mapping["review_status"].eq("REJECTED")

    mapping.loc[review_mask, "mapping_status"] = (
        "REVIEW_REQUIRED"
    )

    mapping.loc[approved_mask, "mapping_status"] = (
        "REVIEW_APPROVED"
    )

    mapping.loc[rejected_mask, "mapping_status"] = (
        "REVIEW_REJECTED"
    )

    mapping["review_required"] = (
        mapping["review_status"].isin(
            ["PENDING", "ESCALATED"]
        )
    )

    approved_id_mask = (
        approved_mask
        & mapping["approved_harmonized_id"].notna()
        & mapping["approved_harmonized_id"].astype(str).ne("")
    )

    mapping.loc[
        approved_id_mask,
        "harmonized_material_id",
    ] = mapping.loc[
        approved_id_mask,
        "approved_harmonized_id",
    ]

    mapping["match_score"] = pd.to_numeric(
        mapping["match_score"],
        errors="coerce",
    )

    mapping["mapping_confidence_band"] = "UNAVAILABLE"

    mapping.loc[
        mapping["match_score"] >= 0.85,
        "mapping_confidence_band",
    ] = "HIGH"

    mapping.loc[
        (mapping["match_score"] >= 0.65)
        & (mapping["match_score"] < 0.85),
        "mapping_confidence_band",
    ] = "MEDIUM"

    mapping.loc[
        mapping["match_score"] < 0.65,
        "mapping_confidence_band",
    ] = "LOW"

    mapping["mapping_generated_at"] = pd.Timestamp.utcnow()

    return mapping


def summarize_mapping(mapping):
    """
    Generate migration mapping statistics.
    """

    summary = pd.DataFrame(
        [
            {
                "total_records": len(mapping),
                "auto_matched": int(
                    (mapping["mapping_status"] == "AUTO_MATCHED").sum()
                ),
                "review_required": int(
                    (mapping["mapping_status"] == "REVIEW_REQUIRED").sum()
                ),
                "review_approved": int(
                    (mapping["mapping_status"] == "REVIEW_APPROVED").sum()
                ),
                "review_rejected": int(
                    (mapping["mapping_status"] == "REVIEW_REJECTED").sum()
                ),
                "high_confidence": int(
                    (
                        mapping["mapping_confidence_band"]
                        == "HIGH"
                    ).sum()
                ),
                "medium_confidence": int(
                    (
                        mapping["mapping_confidence_band"]
                        == "MEDIUM"
                    ).sum()
                ),
                "low_confidence": int(
                    (
                        mapping["mapping_confidence_band"]
                        == "LOW"
                    ).sum()
                ),
            }
        ]
    )

    return summary


def main():
    harmonized = _safe_read_csv(HARMONIZED_RESULTS_FILE)
    review_queue = _safe_read_csv(REVIEW_QUEUE_FILE)

    mapping = build_migration_mapping(
        harmonized,
        review_queue,
    )

    output_file = OUTPUT_DIR / "migration_mapping.csv"
    summary_file = OUTPUT_DIR / "migration_mapping_summary.csv"

    mapping.to_csv(output_file, index=False)

    summary = summarize_mapping(mapping)
    summary.to_csv(summary_file, index=False)

    print(f"Saved {len(mapping)} records to {output_file}")
    print(f"Saved summary to {summary_file}")
    print(mapping["mapping_status"].value_counts().to_string())


if __name__ == "__main__":
    main()