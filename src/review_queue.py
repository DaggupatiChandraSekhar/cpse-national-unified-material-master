import pandas as pd
from datetime import datetime, timezone


VALID_DECISIONS = {
    "APPROVED",
    "REJECTED",
    "PENDING",
    "ESCALATED",
}


def _utc_timestamp():
    """Return a UTC timestamp suitable for audit fields."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_columns(df):
    """
    Ensure expected review-related columns exist.
    """
    df = df.copy()

    defaults = {
        "review_status": "PENDING",
        "reviewer": "",
        "review_comment": "",
        "approved_harmonized_id": "",
        "reviewed_at": "",
    }

    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default

    return df


def _calculate_review_priority(row):
    """
    Assign review priority based on match uncertainty and technical risk.
    """

    score = float(row.get("match_score", 0) or 0)
    confidence = float(row.get("match_confidence", 0) or 0)

    conflict_count = int(row.get("technical_conflict_count", 0) or 0)

    ambiguous = str(row.get("ambiguity_flag", "")).upper() == "TRUE"

    if conflict_count > 0 or ambiguous:
        return "HIGH"

    if score >= 0.75 or confidence >= 0.75:
        return "MEDIUM"

    return "LOW"


def create_review_queue(evaluated_df):
    """
    Extract matches requiring human review and enrich them with
    review-management metadata.
    """

    evaluated_df = evaluated_df.copy()

    if "decision" not in evaluated_df.columns:
        raise ValueError(
            "The evaluated dataset must contain a 'decision' column."
        )

    review_df = evaluated_df[
        evaluated_df["decision"].astype(str).str.upper() == "REVIEW"
    ].copy()

    review_df = _ensure_columns(review_df)

    review_df["review_status"] = "PENDING"
    review_df["reviewer"] = ""
    review_df["review_comment"] = ""
    review_df["approved_harmonized_id"] = ""
    review_df["reviewed_at"] = ""

    review_df["review_priority"] = review_df.apply(
        _calculate_review_priority,
        axis=1,
    )

    priority_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

    review_df["_priority_order"] = review_df["review_priority"].map(
        priority_order
    )

    review_df = review_df.sort_values(
        by=["_priority_order", "match_score"],
        ascending=[True, False],
    ).drop(columns=["_priority_order"])

    return review_df.reset_index(drop=True)


def update_review_decision(
    review_df,
    material_id_a,
    material_id_b,
    decision,
    reviewer,
    comment="",
    approved_harmonized_id="",
):
    """
    Update the review decision for a material pair.
    """

    decision = str(decision).upper()

    if decision not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid review decision '{decision}'. "
            f"Allowed values: {sorted(VALID_DECISIONS)}"
        )

    review_df = _ensure_columns(review_df)

    review_df = review_df.copy()

    material_id_a = str(material_id_a)
    material_id_b = str(material_id_b)

    mask = (
        review_df["material_id_a"].astype(str).eq(material_id_a)
        & review_df["material_id_b"].astype(str).eq(material_id_b)
    )

    if not mask.any():
        raise ValueError(
            "No matching review record found for "
            f"material pair: {material_id_a}, {material_id_b}"
        )

    review_df.loc[mask, "review_status"] = decision
    review_df.loc[mask, "reviewer"] = reviewer
    review_df.loc[mask, "review_comment"] = comment
    review_df.loc[mask, "approved_harmonized_id"] = (
        approved_harmonized_id
    )
    review_df.loc[mask, "reviewed_at"] = _utc_timestamp()

    return review_df


def summarize_review_queue(review_df):
    """
    Generate review queue statistics.
    """

    review_df = _ensure_columns(review_df)

    total_records = len(review_df)

    pending = (
        review_df["review_status"]
        .astype(str)
        .str.upper()
        .eq("PENDING")
        .sum()
    )

    approved = (
        review_df["review_status"]
        .astype(str)
        .str.upper()
        .eq("APPROVED")
        .sum()
    )

    rejected = (
        review_df["review_status"]
        .astype(str)
        .str.upper()
        .eq("REJECTED")
        .sum()
    )

    escalated = (
        review_df["review_status"]
        .astype(str)
        .str.upper()
        .eq("ESCALATED")
        .sum()
    )

    summary = pd.DataFrame(
        [
            {
                "total_review_records": total_records,
                "pending_records": int(pending),
                "approved_records": int(approved),
                "rejected_records": int(rejected),
                "escalated_records": int(escalated),
                "completed_records": int(approved + rejected),
                "high_priority_records": int(
                    (
                        review_df["review_priority"]
                        .astype(str)
                        .str.upper()
                        .eq("HIGH")
                    ).sum()
                ),
            }
        ]
    )

    return summary


if __name__ == "__main__":
    from src.config import OUTPUT_DIR, REVIEW_QUEUE_FILE

    evaluated_file = OUTPUT_DIR / "evaluated_matches.csv"

    evaluated_df = pd.read_csv(evaluated_file)

    review_df = create_review_queue(evaluated_df)

    review_df.to_csv(REVIEW_QUEUE_FILE, index=False)

    summary_df = summarize_review_queue(review_df)

    summary_file = OUTPUT_DIR / "review_queue_summary.csv"
    summary_df.to_csv(summary_file, index=False)

    print(f"Review queue records: {len(review_df)}")
    print(f"Saved to: {REVIEW_QUEUE_FILE}")
    print(f"Saved summary to: {summary_file}")