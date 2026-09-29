from datetime import datetime, timezone

from src.config import OUTPUT_DIR
import pandas as pd


INPUT_FILE = OUTPUT_DIR / "duplicate_detection_report.csv"

OUTPUT_FILE = OUTPUT_DIR / "review_approval_workflow.csv"
SUMMARY_FILE = OUTPUT_DIR / "review_approval_summary.csv"


VALID_STATUSES = {
    "PENDING",
    "IN_REVIEW",
    "APPROVED",
    "REJECTED",
    "DEFERRED",
}


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def assign_priority(df):
    df["review_priority"] = "MEDIUM"

    if "duplicate_confidence_band" in df.columns:
        df.loc[
            df["duplicate_confidence_band"].astype(str).str.upper()
            == "HIGH",
            "review_priority",
        ] = "HIGH"

    df.loc[
        df["duplicate_type"].isin(
            [
                "EXACT_DUPLICATE",
                "FUNCTIONALLY_EQUIVALENT",
            ]
        ),
        "review_priority",
    ] = "HIGH"

    df.loc[
        df["duplicate_type"] == "NEAR_DUPLICATE",
        "review_priority",
    ] = "LOW"

    df.loc[
        df["duplicate_type"] == "POTENTIAL_MATCH",
        "review_priority",
    ] = "MEDIUM"

    if "technical_conflict" in df.columns:
        df.loc[
            df["technical_conflict"].astype(str).str.lower()
            == "true",
            "review_priority",
        ] = "HIGH"

    return df


def assign_review_reason(df):
    df["review_reason"] = ""

    df.loc[
        df["duplicate_type"] == "EXACT_DUPLICATE",
        "review_reason",
    ] = "Exact duplicate candidate requires approval before merge"

    df.loc[
        df["duplicate_type"] == "NEAR_DUPLICATE",
        "review_reason",
    ] = "Near-duplicate candidate requires validation"

    df.loc[
        df["duplicate_type"] == "FUNCTIONALLY_EQUIVALENT",
        "review_reason",
    ] = "Functionally equivalent material requires harmonization approval"

    df.loc[
        df["duplicate_type"] == "POTENTIAL_MATCH",
        "review_reason",
    ] = "Potential match requires manual technical review"

    if "technical_conflict" in df.columns:
        conflict_mask = (
            df["technical_conflict"].astype(str).str.lower()
            == "true"
        )

        df.loc[
            conflict_mask,
            "review_reason",
        ] = (
            df.loc[conflict_mask, "review_reason"]
            + "; technical attribute conflict detected"
        ).str.strip("; ")

    return df


def build_summary(df):
    summary = (
        df.groupby(
            [
                "review_status",
                "review_priority",
                "workflow_stage",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="review_record_count")
        .sort_values(
            "review_record_count",
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

    required_columns = [
        "duplicate_type",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df = assign_priority(df)

    df["review_status"] = "PENDING"
    df["reviewer_name"] = ""
    df["review_comment"] = ""
    df["reviewed_at"] = ""
    df["approved_harmonized_id"] = ""
    df["approval_timestamp"] = ""
    df["review_reason"] = ""

    df["workflow_stage"] = "MATERIAL_REVIEW"
    df["workflow_version"] = "v1"
    df["workflow_created_at"] = utc_timestamp()

    df = assign_review_reason(df)

    df["review_decision"] = ""
    df["review_outcome"] = "AWAITING_REVIEW"

    df.loc[
        df["review_status"] == "APPROVED",
        "review_outcome",
    ] = "APPROVED_FOR_HARMONIZATION"

    df.loc[
        df["review_status"] == "REJECTED",
        "review_outcome",
    ] = "REJECTED_FOR_HARMONIZATION"

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary = build_summary(df)

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    print(f"Created: {OUTPUT_FILE}")
    print(f"Created: {SUMMARY_FILE}")
    print(f"Total review records: {len(df)}")

    print("\nReview status:")
    print(
        df["review_status"]
        .value_counts()
        .to_string()
    )

    print("\nReview priority:")
    print(
        df["review_priority"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()