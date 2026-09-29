from src.config import OUTPUT_DIR
import pandas as pd


INPUT_FILE = OUTPUT_DIR / "match_results.csv"

OUTPUT_FILE = OUTPUT_DIR / "duplicate_detection_report.csv"
SUMMARY_FILE = OUTPUT_DIR / "duplicate_detection_summary.csv"


def safe_numeric(df, column, default=0.0):
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)

    return pd.to_numeric(
        df[column],
        errors="coerce",
    ).fillna(default)


def build_duplicate_group(row):
    material_a = str(row.get("material_id_a", "")).strip()
    material_b = str(row.get("material_id_b", "")).strip()

    if not material_a or not material_b:
        return ""

    return "|".join(sorted([material_a, material_b]))


def classify_duplicates(report):
    report["duplicate_type"] = "NO_MATCH"
    report["recommended_action"] = "NO_ACTION"

    exact_mask = report["description_score"] >= 99

    near_mask = (
        report["description_score"] >= 85
    ) & (
        report["description_score"] < 99
    )

    equivalent_mask = report["match_score"] >= 0.85

    review_mask = (
        report["match_score"] >= 0.65
    ) & (
        report["match_score"] < 0.85
    )

    report.loc[
        exact_mask,
        "duplicate_type",
    ] = "EXACT_DUPLICATE"

    report.loc[
        exact_mask,
        "recommended_action",
    ] = "MERGE_CANDIDATE"

    report.loc[
        near_mask & ~exact_mask,
        "duplicate_type",
    ] = "NEAR_DUPLICATE"

    report.loc[
        near_mask & ~exact_mask,
        "recommended_action",
    ] = "REVIEW_FOR_MERGE"

    report.loc[
        equivalent_mask,
        "duplicate_type",
    ] = "FUNCTIONALLY_EQUIVALENT"

    report.loc[
        equivalent_mask,
        "recommended_action",
    ] = "HARMONIZE"

    report.loc[
        review_mask,
        "duplicate_type",
    ] = "POTENTIAL_MATCH"

    report.loc[
        review_mask,
        "recommended_action",
    ] = "MANUAL_REVIEW"

    return report


def add_duplicate_confidence(report):
    report["duplicate_confidence_band"] = "LOW"

    high_mask = report["match_score"] >= 0.85
    medium_mask = (
        report["match_score"] >= 0.65
    ) & (
        report["match_score"] < 0.85
    )

    report.loc[
        high_mask,
        "duplicate_confidence_band",
    ] = "HIGH"

    report.loc[
        medium_mask,
        "duplicate_confidence_band",
    ] = "MEDIUM"

    return report


def add_technical_conflicts(report):
    conflict_columns = []

    for column in [
        "group_score",
        "manufacturer_score",
        "part_number_score",
        "uom_score",
    ]:
        if column in report.columns:
            conflict_columns.append(column)

    report["technical_conflict"] = False
    report["technical_conflict_reason"] = ""

    if conflict_columns:
        conflict_mask = (
            report[conflict_columns] < 0.50
        ).any(axis=1)

        report.loc[
            conflict_mask,
            "technical_conflict",
        ] = True

        report.loc[
            conflict_mask,
            "technical_conflict_reason",
        ] = "One or more technical attributes have low similarity"

    return report


def add_review_priority(report):
    report["review_priority"] = "LOW"

    high_priority_mask = (
        report["duplicate_type"].isin(
            [
                "EXACT_DUPLICATE",
                "FUNCTIONALLY_EQUIVALENT",
            ]
        )
        & report["technical_conflict"]
    )

    medium_priority_mask = (
        report["duplicate_type"].isin(
            [
                "NEAR_DUPLICATE",
                "POTENTIAL_MATCH",
            ]
        )
    )

    report.loc[
        medium_priority_mask,
        "review_priority",
    ] = "MEDIUM"

    report.loc[
        high_priority_mask,
        "review_priority",
    ] = "HIGH"

    return report


def add_explanations(report):
    report["duplicate_reason"] = ""

    report.loc[
        report["duplicate_type"] == "EXACT_DUPLICATE",
        "duplicate_reason",
    ] = "Descriptions are identical or nearly identical"

    report.loc[
        report["duplicate_type"] == "NEAR_DUPLICATE",
        "duplicate_reason",
    ] = "Descriptions are highly similar but not identical"

    report.loc[
        report["duplicate_type"] == "FUNCTIONALLY_EQUIVALENT",
        "duplicate_reason",
    ] = "Overall match score indicates functional equivalence"

    report.loc[
        report["duplicate_type"] == "POTENTIAL_MATCH",
        "duplicate_reason",
    ] = "Similarity is sufficient for manual review"

    report.loc[
        report["technical_conflict"],
        "duplicate_reason",
    ] = (
        report["duplicate_reason"]
        + "; technical attribute conflict detected"
    )

    return report


def build_summary(report):
    summary = (
        report.groupby(
            [
                "duplicate_type",
                "recommended_action",
                "duplicate_confidence_band",
                "review_priority",
                "technical_conflict",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="pair_count")
        .sort_values(
            "pair_count",
            ascending=False,
        )
    )

    return summary


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    if "match_score" not in df.columns:
        raise ValueError(
            "Column 'match_score' not found."
        )

    report = df.copy()

    report["match_score"] = safe_numeric(
        report,
        "match_score",
    )

    report["description_score"] = safe_numeric(
        report,
        "description_score",
    )

    report["group_score"] = safe_numeric(
        report,
        "group_score",
    )

    report["manufacturer_score"] = safe_numeric(
        report,
        "manufacturer_score",
    )

    report["part_number_score"] = safe_numeric(
        report,
        "part_number_score",
    )

    report["uom_score"] = safe_numeric(
        report,
        "uom_score",
    )

    report = classify_duplicates(report)
    report = add_duplicate_confidence(report)
    report = add_technical_conflicts(report)
    report = add_review_priority(report)
    report = add_explanations(report)

    report["duplicate_group_id"] = report.apply(
        build_duplicate_group,
        axis=1,
    )

    report["duplicate_detection_status"] = "ANALYZED"

    columns = [
        "material_id_a",
        "material_id_b",
        "duplicate_group_id",
        "match_score",
        "description_score",
        "group_score",
        "manufacturer_score",
        "part_number_score",
        "uom_score",
        "decision",
        "duplicate_type",
        "duplicate_confidence_band",
        "recommended_action",
        "review_priority",
        "technical_conflict",
        "technical_conflict_reason",
        "duplicate_reason",
        "duplicate_detection_status",
    ]

    available_columns = [
        column
        for column in columns
        if column in report.columns
    ]

    report = report[available_columns]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary = build_summary(report)

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    print(f"Created: {OUTPUT_FILE}")
    print(f"Created: {SUMMARY_FILE}")
    print(f"Total analyzed pairs: {len(report)}")

    print("\nDuplicate classification:")
    print(
        report["duplicate_type"]
        .value_counts()
        .to_string()
    )

    print("\nReview priority:")
    print(
        report["review_priority"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()