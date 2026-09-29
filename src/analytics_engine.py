from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
ANALYTICS_DIR = OUTPUT_DIR / "analytics"

ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    path = OUTPUT_DIR / filename

    if path.exists():
        return pd.read_csv(path)

    return pd.DataFrame()


def save_csv(df, filename):
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        ANALYTICS_DIR / filename,
        index=False,
    )


def count_status(df, column, value):
    if df.empty or column not in df.columns:
        return 0

    return int(
        df[column]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq(value.upper())
        .sum()
    )


def calculate_rate(numerator, denominator):
    if denominator == 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2,
    )


def distribution(df, column, output_name, count_name="record_count"):
    if df.empty or column not in df.columns:
        return

    result = (
        df[column]
        .fillna("UNKNOWN")
        .astype(str)
        .replace("", "UNKNOWN")
        .value_counts()
        .rename_axis(column)
        .reset_index(name=count_name)
    )

    save_csv(result, output_name)


def main():
    validated = load_csv("validated_materials.csv")
    standardized = load_csv("standardized_materials.csv")
    national_master = load_csv("national_material_master.csv")
    migration = load_csv("national_migration_mapping.csv")
    matching = load_csv("match_results.csv")
    duplicates = load_csv("duplicate_detection_report.csv")
    reviews = load_csv("review_approval_workflow.csv")

    total_source_materials = len(validated)

    metrics = {
        "total_source_materials": total_source_materials,
        "validated_materials": len(validated),
        "standardized_materials": len(standardized),
        "national_material_codes": len(national_master),
        "migration_records": len(migration),
        "matching_pairs": len(matching),
        "duplicate_records": len(duplicates),
        "review_records": len(reviews),
    }

    validated_passed = count_status(
        validated,
        "validation_status",
        "VALID",
    )

    standardized_completed = count_status(
        standardized,
        "standardization_status",
        "STANDARDIZED",
    )

    metrics["validated_passed"] = validated_passed
    metrics["validation_rate_percent"] = calculate_rate(
        validated_passed,
        total_source_materials,
    )

    metrics["standardization_rate_percent"] = calculate_rate(
        standardized_completed,
        len(standardized),
    )

    metrics["national_code_coverage_percent"] = calculate_rate(
        len(national_master),
        len(standardized),
    )

    if not reviews.empty:
        metrics["pending_reviews"] = count_status(
            reviews,
            "review_status",
            "PENDING",
        )

        metrics["in_review"] = count_status(
            reviews,
            "review_status",
            "IN_REVIEW",
        )

        metrics["approved_reviews"] = count_status(
            reviews,
            "review_status",
            "APPROVED",
        )

        metrics["rejected_reviews"] = count_status(
            reviews,
            "review_status",
            "REJECTED",
        )

        metrics["deferred_reviews"] = count_status(
            reviews,
            "review_status",
            "DEFERRED",
        )

        completed_reviews = (
            metrics["approved_reviews"]
            + metrics["rejected_reviews"]
        )

        metrics["review_completion_rate_percent"] = calculate_rate(
            completed_reviews,
            len(reviews),
        )
    else:
        metrics["pending_reviews"] = 0
        metrics["in_review"] = 0
        metrics["approved_reviews"] = 0
        metrics["rejected_reviews"] = 0
        metrics["deferred_reviews"] = 0
        metrics["review_completion_rate_percent"] = 0.0

    if not migration.empty:
        metrics["migration_ready"] = count_status(
            migration,
            "migration_status",
            "READY_FOR_MIGRATION",
        )

        metrics["migration_review_required"] = count_status(
            migration,
            "migration_status",
            "REVIEW_REQUIRED",
        )

        metrics["migration_approved"] = count_status(
            migration,
            "migration_status",
            "REVIEW_APPROVED",
        )

        metrics["migration_rejected"] = count_status(
            migration,
            "migration_status",
            "REVIEW_REJECTED",
        )

        migration_ready_total = (
            metrics["migration_ready"]
            + metrics["migration_approved"]
        )

        metrics["migration_readiness_rate_percent"] = calculate_rate(
            migration_ready_total,
            len(migration),
        )
    else:
        metrics["migration_ready"] = 0
        metrics["migration_review_required"] = 0
        metrics["migration_approved"] = 0
        metrics["migration_rejected"] = 0
        metrics["migration_readiness_rate_percent"] = 0.0

    if not duplicates.empty:
        metrics["exact_duplicates"] = count_status(
            duplicates,
            "duplicate_type",
            "EXACT_DUPLICATE",
        )

        metrics["near_duplicates"] = count_status(
            duplicates,
            "duplicate_type",
            "NEAR_DUPLICATE",
        )

        metrics["functional_equivalents"] = count_status(
            duplicates,
            "duplicate_type",
            "FUNCTIONALLY_EQUIVALENT",
        )

        metrics["potential_matches"] = count_status(
            duplicates,
            "duplicate_type",
            "POTENTIAL_MATCH",
        )

        metrics["technical_conflicts"] = count_status(
            duplicates,
            "technical_conflict",
            "TRUE",
        )
    else:
        metrics["exact_duplicates"] = 0
        metrics["near_duplicates"] = 0
        metrics["functional_equivalents"] = 0
        metrics["potential_matches"] = 0
        metrics["technical_conflicts"] = 0

    metrics_df = pd.DataFrame(
        [
            {
                "metric": key,
                "value": value,
            }
            for key, value in metrics.items()
        ]
    )

    save_csv(
        metrics_df,
        "platform_kpis.csv",
    )

    distribution(
        standardized,
        "material_classification",
        "classification_distribution.csv",
        "material_count",
    )

    distribution(
        standardized,
        "source_cpse",
        "cpse_distribution.csv",
        "material_count",
    )

    distribution(
        duplicates,
        "duplicate_type",
        "duplicate_distribution.csv",
    )

    distribution(
        duplicates,
        "duplicate_confidence_band",
        "duplicate_confidence_distribution.csv",
    )

    distribution(
        duplicates,
        "review_priority",
        "review_priority_distribution.csv",
    )

    distribution(
        duplicates,
        "technical_conflict",
        "technical_conflict_distribution.csv",
    )

    distribution(
        reviews,
        "review_status",
        "review_status_distribution.csv",
    )

    distribution(
        migration,
        "migration_status",
        "migration_status_distribution.csv",
    )

    if not matching.empty and "decision" in matching.columns:
        distribution(
            matching,
            "decision",
            "matching_decision_distribution.csv",
        )

    analytics_summary = pd.DataFrame(
        [
            {
                "analytics_area": "Data Quality",
                "metric": "Validation Rate",
                "value": metrics["validation_rate_percent"],
                "unit": "percent",
            },
            {
                "analytics_area": "Standardization",
                "metric": "Standardization Rate",
                "value": metrics["standardization_rate_percent"],
                "unit": "percent",
            },
            {
                "analytics_area": "National Master",
                "metric": "National Code Coverage",
                "value": metrics["national_code_coverage_percent"],
                "unit": "percent",
            },
            {
                "analytics_area": "Review Workflow",
                "metric": "Review Completion Rate",
                "value": metrics["review_completion_rate_percent"],
                "unit": "percent",
            },
            {
                "analytics_area": "Migration",
                "metric": "Migration Readiness Rate",
                "value": metrics["migration_readiness_rate_percent"],
                "unit": "percent",
            },
            {
                "analytics_area": "Duplicates",
                "metric": "Exact Duplicate Pairs",
                "value": metrics["exact_duplicates"],
                "unit": "records",
            },
            {
                "analytics_area": "Duplicates",
                "metric": "Technical Conflicts",
                "value": metrics["technical_conflicts"],
                "unit": "records",
            },
        ]
    )

    save_csv(
        analytics_summary,
        "analytics_summary.csv",
    )

    print("Analytics engine completed.")
    print(f"Analytics output folder: {ANALYTICS_DIR}")
    print("\nPlatform KPIs:")
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()