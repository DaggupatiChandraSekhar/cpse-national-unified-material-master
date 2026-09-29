import json
import re

import pandas as pd
from rapidfuzz import fuzz


MODEL_VERSION = "cpse-material-matcher-v2"

MATCH_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.65
AMBIGUITY_GAP_THRESHOLD = 0.05


ATTRIBUTE_FIELDS = [
    "material_type",
    "size",
    "length",
    "voltage",
    "diameter",
    "core_count",
    "standard",
    "manufacturer",
    "part_number",
    "unit_of_measure",
]


TECHNICAL_FIELDS = [
    "material_type",
    "size",
    "length",
    "voltage",
    "diameter",
    "core_count",
    "standard",
]


def safe_text(value):
    """Convert missing values to normalized uppercase text."""

    if pd.isna(value):
        return ""

    text = str(value).upper().strip()
    text = re.sub(r"\s+", " ", text)

    return text


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


def normalize_for_comparison(value):
    """Normalize values for technical comparison."""

    text = safe_text(value)

    if not text:
        return ""

    text = text.replace(",", "")
    text = text.replace(" ", "")
    text = text.replace("-", "")
    text = text.replace("_", "")

    return text


def attribute_confidence(value_a, value_b):
    """
    Return attribute-level confidence.

    Both missing:
        0.0

    One missing:
        0.0

    Exact normalized match:
        1.0

    Partial similarity:
        Fuzzy similarity score.
    """

    normalized_a = normalize_for_comparison(value_a)
    normalized_b = normalize_for_comparison(value_b)

    if not normalized_a or not normalized_b:
        return 0.0

    if normalized_a == normalized_b:
        return 1.0

    return calculate_similarity(normalized_a, normalized_b)


def detect_technical_conflicts(material_a, material_b):
    """Identify technical attribute mismatches."""

    conflicts = []
    critical_conflicts = []
    minor_conflicts = []

    for field in TECHNICAL_FIELDS:
        value_a = safe_text(material_a.get(field, ""))
        value_b = safe_text(material_b.get(field, ""))

        if not value_a or not value_b:
            continue

        normalized_a = normalize_for_comparison(value_a)
        normalized_b = normalize_for_comparison(value_b)

        if normalized_a == normalized_b:
            continue

        conflict = {
            "attribute": field,
            "material_a_value": value_a,
            "material_b_value": value_b,
        }

        # Add each conflict exactly once.
        conflicts.append(conflict)

        if field in ["voltage", "standard", "material_type"]:
            critical_conflicts.append(conflict)

        elif field in ["size", "length", "diameter", "core_count"]:
            pass

        else:
            minor_conflicts.append(conflict)

    if critical_conflicts:
        severity = "CRITICAL"
    elif len(conflicts) >= 3:
        severity = "HIGH"
    elif conflicts:
        severity = "MEDIUM"
    else:
        severity = "NONE"

    return {
        "technical_conflict_flag": bool(conflicts),
        "technical_conflict_count": len(conflicts),
        "technical_conflicts": json.dumps(conflicts),
        "critical_conflicts": json.dumps(critical_conflicts),
        "minor_conflicts": json.dumps(minor_conflicts),
        "technical_conflict_severity": severity,
    }


def calculate_data_completeness(material):
    """Calculate completeness of important material attributes."""

    fields = [
        "material_description_normalized",
        "material_group_normalized",
        "manufacturer_normalized",
        "part_number_normalized",
        "unit_of_measure_normalized",
        *TECHNICAL_FIELDS,
    ]

    available = 0

    for field in fields:
        if safe_text(material.get(field, "")):
            available += 1

    return round(available / len(fields), 4)


def calculate_attribute_scores(material_a, material_b):
    """Calculate confidence for individual material attributes."""

    scores = {}

    for field in ATTRIBUTE_FIELDS:
        if field == "material_type":
            column = "material_type"

        elif field == "manufacturer":
            column = "manufacturer_normalized"

        elif field == "part_number":
            column = "part_number_normalized"

        elif field == "unit_of_measure":
            column = "unit_of_measure_normalized"

        elif field == "standard":
            column = "standard"

        else:
            column = field

        scores[field] = attribute_confidence(
            material_a.get(column, ""),
            material_b.get(column, ""),
        )

    return scores


def calculate_match_score(material_a, material_b):
    """
    Calculate an explainable weighted matching score.

    Advanced weights:
    - Description: 25%
    - Technical attributes: 15%
    - Material group: 10%
    - Standard: 10%
    - Manufacturer: 10%
    - Part number: 10%
    - Unit of measure: 5%
    - Functional similarity: 10%
    - Data completeness: 5%
    """

    description_score = calculate_similarity(
        material_a.get("material_description_normalized", ""),
        material_b.get("material_description_normalized", ""),
    )

    group_score = calculate_similarity(
        material_a.get("material_group_normalized", ""),
        material_b.get("material_group_normalized", ""),
    )

    manufacturer_score = calculate_similarity(
        material_a.get("manufacturer_normalized", ""),
        material_b.get("manufacturer_normalized", ""),
    )

    part_number_score = calculate_similarity(
        material_a.get("part_number_normalized", ""),
        material_b.get("part_number_normalized", ""),
    )

    uom_score = calculate_similarity(
        material_a.get("unit_of_measure_normalized", ""),
        material_b.get("unit_of_measure_normalized", ""),
    )

    standard_score = calculate_similarity(
        material_a.get("standard", ""),
        material_b.get("standard", ""),
    )

    attribute_scores = calculate_attribute_scores(
        material_a,
        material_b,
    )

    technical_scores = [
        attribute_scores[field]
        for field in TECHNICAL_FIELDS
        if field in attribute_scores
    ]

    technical_attribute_score = (
        sum(technical_scores) / len(technical_scores)
        if technical_scores
        else 0.0
    )

    functional_score = round(
        (
            description_score
            + group_score
            + attribute_scores.get("material_type", 0.0)
        )
        / 3,
        4,
    )

    specification_score = round(
        (
            technical_attribute_score
            + standard_score
        )
        / 2,
        4,
    )

    completeness_a = calculate_data_completeness(material_a)
    completeness_b = calculate_data_completeness(material_b)

    data_completeness_score = round(
        (completeness_a + completeness_b) / 2,
        4,
    )

    technical_conflict_data = detect_technical_conflicts(
        material_a,
        material_b,
    )

    technical_penalty = 0.0

    if technical_conflict_data["technical_conflict_severity"] == "CRITICAL":
        technical_penalty = 0.25

    elif technical_conflict_data["technical_conflict_severity"] == "HIGH":
        technical_penalty = 0.15

    elif technical_conflict_data["technical_conflict_severity"] == "MEDIUM":
        technical_penalty = 0.05

    final_score = (
        description_score * 0.25
        + technical_attribute_score * 0.15
        + group_score * 0.10
        + standard_score * 0.10
        + manufacturer_score * 0.10
        + part_number_score * 0.10
        + uom_score * 0.05
        + functional_score * 0.10
        + data_completeness_score * 0.05
        - technical_penalty
    )

    final_score = max(
        0.0,
        min(1.0, final_score),
    )

    evidence = []

    if description_score >= 0.85:
        evidence.append("High description similarity")

    elif description_score >= 0.65:
        evidence.append("Moderate description similarity")

    if group_score >= 0.85:
        evidence.append("Same material group")

    if manufacturer_score >= 0.85:
        evidence.append("Same manufacturer")

    if part_number_score >= 0.85:
        evidence.append("Matching part number")

    if standard_score >= 0.85:
        evidence.append("Matching standard")

    if technical_attribute_score >= 0.85:
        evidence.append("Strong technical attribute agreement")

    if technical_conflict_data["technical_conflict_flag"]:
        evidence.append(
            "Technical conflicts detected: "
            f"{technical_conflict_data['technical_conflict_count']}"
        )

    if not evidence:
        evidence.append("Limited matching evidence")

    return {
        # Existing columns
        "description_score": description_score,
        "group_score": group_score,
        "manufacturer_score": manufacturer_score,
        "part_number_score": part_number_score,
        "uom_score": uom_score,
        "match_score": round(final_score, 4),

        # Advanced scores
        "technical_attribute_score": round(
            technical_attribute_score,
            4,
        ),
        "standard_score": standard_score,
        "functional_similarity_score": functional_score,
        "specification_similarity_score": specification_score,
        "data_completeness_score": data_completeness_score,

        # Attribute confidence
        **{
            f"{attribute}_confidence": round(
                score,
                4,
            )
            for attribute, score in attribute_scores.items()
        },

        # Technical conflicts
        **technical_conflict_data,

        # Evidence
        "matching_evidence": "; ".join(evidence),
        "evidence_count": len(evidence),
        "model_version": MODEL_VERSION,
        "threshold_used": MATCH_THRESHOLD,
    }


def assign_decision(
    score,
    conflict_severity,
    confidence_gap=None,
):
    """Assign match decision using score and technical risk."""

    if score >= MATCH_THRESHOLD and conflict_severity == "NONE":
        return "MATCH"

    if score >= MATCH_THRESHOLD and confidence_gap is not None:
        if confidence_gap < AMBIGUITY_GAP_THRESHOLD:
            return "REVIEW"

    if score >= REVIEW_THRESHOLD:
        return "REVIEW"

    return "NO_MATCH"


def assign_confidence_band(score):
    """Convert confidence score into an interpretable band."""

    if score >= 0.90:
        return "VERY_HIGH"

    if score >= 0.85:
        return "HIGH"

    if score >= 0.75:
        return "MEDIUM"

    if score >= 0.65:
        return "LOW"

    return "VERY_LOW"


def add_confidence_gaps(results_df):
    """Calculate best-match confidence gap for each source material."""

    results_df = results_df.copy()

    # Ensure both material IDs use strings.
    results_df["material_id_a"] = (
        results_df["material_id_a"]
        .astype(str)
        .str.strip()
    )

    results_df["material_id_b"] = (
        results_df["material_id_b"]
        .astype(str)
        .str.strip()
    )

    # Rank candidates by confidence.
    results_df["candidate_rank"] = (
        results_df
        .groupby("material_id_a")["match_confidence"]
        .rank(
            method="first",
            ascending=False,
        )
        .astype(int)
    )

    sorted_results = results_df.sort_values(
        ["material_id_a", "match_confidence"],
        ascending=[True, False],
    )

    # Get the second-highest confidence score for each material.
    second_scores = (
        sorted_results
        .groupby("material_id_a")["match_confidence"]
        .nth(1)
        .rename("second_best_confidence")
    )

    second_scores.index = second_scores.index.astype(str)

    # Merge using string IDs on both sides.
    results_df = results_df.merge(
        second_scores,
        left_on="material_id_a",
        right_index=True,
        how="left",
    )

    results_df["second_best_confidence"] = (
        results_df["second_best_confidence"]
        .fillna(0.0)
    )

    results_df["best_confidence"] = (
        results_df
        .groupby("material_id_a")["match_confidence"]
        .transform("max")
    )

    results_df["confidence_gap"] = (
        results_df["best_confidence"]
        - results_df["second_best_confidence"]
    ).round(4)

    results_df["ambiguity_flag"] = (
        (results_df["candidate_rank"] == 1)
        & (
            results_df["confidence_gap"]
            < AMBIGUITY_GAP_THRESHOLD
        )
    )

    results_df["ambiguity_reason"] = results_df.apply(
        lambda row: (
            "Small confidence gap between top candidates"
            if row["ambiguity_flag"]
            else ""
        ),
        axis=1,
    )

    return results_df


def save_explainability_outputs(results_df, output_dir):
    """Save separate explainability datasets for analytics and dashboard."""

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Main match results.
    results_df.to_csv(
        output_dir / "match_results.csv",
        index=False,
    )

    # Evidence output.
    evidence_columns = [
        "material_id_a",
        "material_id_b",
        "match_confidence",
        "match_decision",
        "confidence_band",
        "confidence_gap",
        "matching_evidence",
        "evidence_count",
        "model_version",
    ]

    results_df[
        [
            column
            for column in evidence_columns
            if column in results_df.columns
        ]
    ].to_csv(
        output_dir / "matching_evidence.csv",
        index=False,
    )

    # Attribute confidence output.
    attribute_columns = [
        "material_id_a",
        "material_id_b",
        "match_confidence",
    ]

    attribute_columns.extend(
        [
            column
            for column in results_df.columns
            if column.endswith("_confidence")
        ]
    )

    results_df[
        list(dict.fromkeys(attribute_columns))
    ].to_csv(
        output_dir / "attribute_confidence.csv",
        index=False,
    )

    # Technical conflicts output.
    conflict_columns = [
        "material_id_a",
        "material_id_b",
        "technical_conflict_flag",
        "technical_conflict_count",
        "technical_conflict_severity",
        "technical_conflicts",
        "critical_conflicts",
        "minor_conflicts",
    ]

    results_df[
        [
            column
            for column in conflict_columns
            if column in results_df.columns
        ]
    ].to_csv(
        output_dir / "technical_conflicts.csv",
        index=False,
    )

    # Confidence-gap output.
    gap_columns = [
        "material_id_a",
        "material_id_b",
        "match_confidence",
        "candidate_rank",
        "best_confidence",
        "second_best_confidence",
        "confidence_gap",
        "ambiguity_flag",
        "ambiguity_reason",
    ]

    results_df[
        [
            column
            for column in gap_columns
            if column in results_df.columns
        ]
    ].to_csv(
        output_dir / "confidence_gap_analysis.csv",
        index=False,
    )


def run_matching_engine(materials_df, candidates_df):
    """Calculate detailed explainable matching scores."""

    results = []

    material_lookup = (
        materials_df
        .set_index("material_id")
        .to_dict("index")
    )

    for _, candidate in candidates_df.iterrows():

        material_id_a = candidate["material_id_a"]
        material_id_b = candidate["material_id_b"]

        material_a = material_lookup[material_id_a]
        material_b = material_lookup[material_id_b]

        scores = calculate_match_score(
            material_a,
            material_b,
        )

        result = {
            "material_id_a": material_id_a,
            "material_id_b": material_id_b,
            "material_group": candidate.get(
                "material_group",
                "",
            ),
            **scores,
        }

        results.append(result)

    results_df = pd.DataFrame(results)

    if results_df.empty:
        return results_df

    results_df["match_confidence"] = results_df["match_score"]

    results_df = add_confidence_gaps(
        results_df,
    )

    results_df["confidence_band"] = results_df[
        "match_confidence"
    ].apply(assign_confidence_band)

    results_df["match_decision"] = results_df.apply(
        lambda row: assign_decision(
            row["match_confidence"],
            row["technical_conflict_severity"],
            row["confidence_gap"],
        ),
        axis=1,
    )

    results_df["match_reason"] = results_df.apply(
        lambda row: (
            "High-confidence match with no technical conflicts"
            if row["match_decision"] == "MATCH"
            else (
                "Requires human review due to confidence, ambiguity, "
                "or technical conflicts"
                if row["match_decision"] == "REVIEW"
                else "Insufficient similarity for harmonization"
            )
        ),
        axis=1,
    )

    return results_df


if __name__ == "__main__":

    from src.config import (
        PROCESSED_DATA_FILE,
        OUTPUT_DIR,
        MATCH_RESULTS_FILE,
    )

    materials_df = pd.read_csv(
        PROCESSED_DATA_FILE,
    )

    candidates_df = pd.read_csv(
        OUTPUT_DIR / "candidate_pairs.csv",
    )

    results_df = run_matching_engine(
        materials_df,
        candidates_df,
    )

    save_explainability_outputs(
        results_df,
        OUTPUT_DIR,
    )

    results_df.to_csv(
        MATCH_RESULTS_FILE,
        index=False,
    )

    print(
        f"Calculated explainable match scores for "
        f"{len(results_df)} candidate pairs."
    )

    print(
        f"Saved enhanced results to: {MATCH_RESULTS_FILE}"
    )

    print(
        f"Generated explainability files in: {OUTPUT_DIR}"
    )