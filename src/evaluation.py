import pandas as pd


MATCH_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.65


def classify_match(score):
    """
    Classify a match according to confidence thresholds.
    """

    if pd.isna(score):
        return "NO_MATCH"

    if score >= MATCH_THRESHOLD:
        return "MATCH"

    if score >= REVIEW_THRESHOLD:
        return "REVIEW"

    return "NO_MATCH"


def evaluate_matches(results_df):
    """
    Add evaluation labels and quality indicators to matching results.

    Uses existing matching-engine decisions when available.
    Otherwise, derives a decision from match_score.
    """

    df = results_df.copy()

    # Preserve the enhanced matching-engine decision.
    if "match_decision" in df.columns:
        df["decision"] = df["match_decision"]

    else:
        df["decision"] = df["match_score"].apply(
            classify_match
        )

    # Confidence band.
    if "match_confidence" not in df.columns:
        df["match_confidence"] = df["match_score"]

    df["confidence_band"] = df[
        "match_confidence"
    ].apply(assign_confidence_band)

    # Technical-risk indicators.
    if "technical_conflict_flag" not in df.columns:
        df["technical_conflict_flag"] = False

    if "technical_conflict_count" not in df.columns:
        df["technical_conflict_count"] = 0

    if "technical_conflict_severity" not in df.columns:
        df["technical_conflict_severity"] = "NONE"

    # Ambiguity indicators.
    if "ambiguity_flag" not in df.columns:
        df["ambiguity_flag"] = False

    if "confidence_gap" not in df.columns:
        df["confidence_gap"] = None

    # Review reason.
    df["evaluation_reason"] = df.apply(
        determine_evaluation_reason,
        axis=1,
    )

    # Risk category.
    df["risk_category"] = df.apply(
        determine_risk_category,
        axis=1,
    )

    return df


def assign_confidence_band(score):
    """Assign an interpretable confidence band."""

    if pd.isna(score):
        return "VERY_LOW"

    if score >= 0.90:
        return "VERY_HIGH"

    if score >= 0.85:
        return "HIGH"

    if score >= 0.75:
        return "MEDIUM"

    if score >= 0.65:
        return "LOW"

    return "VERY_LOW"


def determine_evaluation_reason(row):
    """Explain why a candidate received its evaluation decision."""

    decision = row.get("decision", "")
    conflict_flag = row.get(
        "technical_conflict_flag",
        False,
    )
    ambiguity_flag = row.get(
        "ambiguity_flag",
        False,
    )

    if decision == "MATCH":
        if conflict_flag:
            return "High score but technical conflict requires attention"

        return "High-confidence match"

    if decision == "REVIEW":
        reasons = []

        if conflict_flag:
            reasons.append("technical conflicts")

        if ambiguity_flag:
            reasons.append("ambiguous top candidates")

        if row.get("match_confidence", 0.0) < MATCH_THRESHOLD:
            reasons.append("confidence below match threshold")

        if reasons:
            return "Review required: " + ", ".join(reasons)

        return "Review required"

    return "Insufficient confidence for matching"


def determine_risk_category(row):
    """Assign a risk category for governance and review prioritization."""

    decision = row.get("decision", "")
    severity = row.get(
        "technical_conflict_severity",
        "NONE",
    )

    ambiguity_flag = row.get(
        "ambiguity_flag",
        False,
    )

    if severity == "CRITICAL":
        return "CRITICAL"

    if decision == "NO_MATCH":
        return "LOW_CONFIDENCE"

    if ambiguity_flag:
        return "AMBIGUOUS"

    if severity == "HIGH":
        return "HIGH_TECHNICAL_RISK"

    if severity == "MEDIUM":
        return "MEDIUM_TECHNICAL_RISK"

    if decision == "REVIEW":
        return "REVIEW_REQUIRED"

    return "LOW_RISK"


def summarize_evaluation(results_df):
    """
    Return summary counts and percentages.
    """

    if results_df.empty:
        return pd.DataFrame(
            columns=[
                "decision",
                "count",
                "percentage",
            ]
        )

    summary = (
        results_df["decision"]
        .value_counts()
        .rename_axis("decision")
        .reset_index(name="count")
    )

    summary["percentage"] = (
        summary["count"] / len(results_df) * 100
    ).round(2)

    return summary


def summarize_confidence_bands(results_df):
    """Summarize the distribution of confidence bands."""

    if results_df.empty:
        return pd.DataFrame(
            columns=[
                "confidence_band",
                "count",
                "percentage",
            ]
        )

    summary = (
        results_df["confidence_band"]
        .value_counts()
        .rename_axis("confidence_band")
        .reset_index(name="count")
    )

    summary["percentage"] = (
        summary["count"] / len(results_df) * 100
    ).round(2)

    return summary


def summarize_risk_categories(results_df):
    """Summarize technical and matching risk categories."""

    if results_df.empty:
        return pd.DataFrame(
            columns=[
                "risk_category",
                "count",
                "percentage",
            ]
        )

    summary = (
        results_df["risk_category"]
        .value_counts()
        .rename_axis("risk_category")
        .reset_index(name="count")
    )

    summary["percentage"] = (
        summary["count"] / len(results_df) * 100
    ).round(2)

    return summary


def summarize_technical_conflicts(results_df):
    """Summarize technical conflict severity."""

    if results_df.empty:
        return pd.DataFrame(
            columns=[
                "technical_conflict_severity",
                "count",
                "percentage",
            ]
        )

    summary = (
        results_df["technical_conflict_severity"]
        .fillna("NONE")
        .value_counts()
        .rename_axis("technical_conflict_severity")
        .reset_index(name="count")
    )

    summary["percentage"] = (
        summary["count"] / len(results_df) * 100
    ).round(2)

    return summary


def calculate_evaluation_kpis(results_df):
    """Calculate overall evaluation KPIs."""

    total = len(results_df)

    if total == 0:
        return pd.DataFrame(
            [
                {
                    "total_candidate_pairs": 0,
                    "match_count": 0,
                    "review_count": 0,
                    "no_match_count": 0,
                    "match_rate": 0.0,
                    "review_rate": 0.0,
                    "no_match_rate": 0.0,
                    "average_confidence": 0.0,
                    "technical_conflict_count": 0,
                    "technical_conflict_rate": 0.0,
                    "ambiguous_candidate_count": 0,
                    "ambiguous_candidate_rate": 0.0,
                }
            ]
        )

    match_count = int(
        (results_df["decision"] == "MATCH").sum()
    )

    review_count = int(
        (results_df["decision"] == "REVIEW").sum()
    )

    no_match_count = int(
        (results_df["decision"] == "NO_MATCH").sum()
    )

    technical_conflict_count = int(
        results_df["technical_conflict_flag"].fillna(False).sum()
    )

    ambiguous_candidate_count = int(
        results_df["ambiguity_flag"].fillna(False).sum()
    )

    average_confidence = round(
        results_df["match_confidence"].mean(),
        4,
    )

    return pd.DataFrame(
        [
            {
                "total_candidate_pairs": total,
                "match_count": match_count,
                "review_count": review_count,
                "no_match_count": no_match_count,
                "match_rate": round(
                    match_count / total * 100,
                    2,
                ),
                "review_rate": round(
                    review_count / total * 100,
                    2,
                ),
                "no_match_rate": round(
                    no_match_count / total * 100,
                    2,
                ),
                "average_confidence": average_confidence,
                "technical_conflict_count": technical_conflict_count,
                "technical_conflict_rate": round(
                    technical_conflict_count / total * 100,
                    2,
                ),
                "ambiguous_candidate_count": ambiguous_candidate_count,
                "ambiguous_candidate_rate": round(
                    ambiguous_candidate_count / total * 100,
                    2,
                ),
            }
        ]
    )


if __name__ == "__main__":

    from src.config import (
        MATCH_RESULTS_FILE,
        OUTPUT_DIR,
    )

    results_df = pd.read_csv(
        MATCH_RESULTS_FILE,
    )

    evaluated_df = evaluate_matches(
        results_df,
    )

    summary_df = summarize_evaluation(
        evaluated_df,
    )

    confidence_summary_df = summarize_confidence_bands(
        evaluated_df,
    )

    risk_summary_df = summarize_risk_categories(
        evaluated_df,
    )

    conflict_summary_df = summarize_technical_conflicts(
        evaluated_df,
    )

    kpis_df = calculate_evaluation_kpis(
        evaluated_df,
    )

    evaluated_file = OUTPUT_DIR / "evaluated_matches.csv"
    summary_file = OUTPUT_DIR / "evaluation_summary.csv"

    evaluated_df.to_csv(
        evaluated_file,
        index=False,
    )

    summary_df.to_csv(
        summary_file,
        index=False,
    )

    confidence_summary_df.to_csv(
        OUTPUT_DIR / "confidence_band_summary.csv",
        index=False,
    )

    risk_summary_df.to_csv(
        OUTPUT_DIR / "risk_category_summary.csv",
        index=False,
    )

    conflict_summary_df.to_csv(
        OUTPUT_DIR / "technical_conflict_summary.csv",
        index=False,
    )

    kpis_df.to_csv(
        OUTPUT_DIR / "evaluation_kpis.csv",
        index=False,
    )

    print("Evaluation completed.")

    print("\nDecision Summary:")
    print(summary_df.to_string(index=False))

    print("\nConfidence Summary:")
    print(confidence_summary_df.to_string(index=False))

    print("\nRisk Summary:")
    print(risk_summary_df.to_string(index=False))

    print("\nEvaluation KPIs:")

    print(kpis_df.to_string(index=False))