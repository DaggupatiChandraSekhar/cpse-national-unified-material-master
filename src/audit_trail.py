from pathlib import Path
from datetime import datetime
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
AUDIT_DIR = OUTPUT_DIR / "audit"

AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    path = OUTPUT_DIR / filename

    if path.exists():
        return pd.read_csv(path)

    return pd.DataFrame()


def safe_value(value):
    if pd.isna(value):
        return ""

    return str(value)


def main():
    validated = load_csv("validated_materials.csv")
    standardized = load_csv("standardized_materials.csv")
    national_master = load_csv("national_material_master.csv")
    migration = load_csv("national_migration_mapping.csv")
    matching = load_csv("match_results.csv")
    reviews = load_csv("review_approval_workflow.csv")
    duplicates = load_csv("duplicate_detection_report.csv")
    analytics = load_csv("analytics/platform_kpis.csv")

    audit_records = []
    timestamp = datetime.now().isoformat(timespec="seconds")

    def add_record(
        entity_type,
        entity_id,
        action,
        details,
        source_file="",
    ):
        entity_id = safe_value(entity_id)

        if not entity_id:
            return

        audit_records.append(
            {
                "audit_id": f"AUDIT-{len(audit_records) + 1:06d}",
                "timestamp": timestamp,
                "actor": "SYSTEM",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "details": details,
                "source_file": source_file,
            }
        )

    for _, row in validated.iterrows():
        material_id = row.get("material_id", "")

        add_record(
            "MATERIAL",
            material_id,
            "VALIDATED",
            "Material passed source-data validation.",
            "validated_materials.csv",
        )

    for _, row in standardized.iterrows():
        material_id = row.get("material_id", "")

        add_record(
            "MATERIAL",
            material_id,
            "STANDARDIZED",
            (
                "Description, UOM, manufacturer, part number, "
                "and classification standardized."
            ),
            "standardized_materials.csv",
        )

    for _, row in national_master.iterrows():
        national_code = row.get("national_material_code", "")

        add_record(
            "NATIONAL_CODE",
            national_code,
            "CREATED",
            "National material code generated.",
            "national_material_master.csv",
        )

    for _, row in matching.iterrows():
        material_a = safe_value(row.get("material_id_a", ""))
        material_b = safe_value(row.get("material_id_b", ""))

        pair_id = f"{material_a}|{material_b}"

        add_record(
            "MATCH_PAIR",
            pair_id,
            "MATCH_EVALUATED",
            (
                f"Match score: {safe_value(row.get('match_score', ''))}; "
                f"decision: {safe_value(row.get('decision', ''))}; "
                f"confidence band: "
                f"{safe_value(row.get('confidence_band', ''))}."
            ),
            "match_results.csv",
        )

    for _, row in duplicates.iterrows():
        material_a = safe_value(row.get("material_id_a", ""))
        material_b = safe_value(row.get("material_id_b", ""))

        duplicate_id = f"{material_a}|{material_b}"

        add_record(
            "DUPLICATE_PAIR",
            duplicate_id,
            "DUPLICATE_DETECTED",
            (
                f"Duplicate score: "
                f"{safe_value(row.get('duplicate_score', ''))}; "
                f"confidence band: "
                f"{safe_value(row.get('duplicate_confidence_band', ''))}; "
                f"review priority: "
                f"{safe_value(row.get('review_priority', ''))}."
            ),
            "duplicate_detection_report.csv",
        )

    for _, row in migration.iterrows():
        material_id = row.get("material_id", "")

        add_record(
            "MIGRATION",
            material_id,
            "MAPPING_CREATED",
            (
                f"Migration status: "
                f"{safe_value(row.get('migration_status', ''))}; "
                f"national code: "
                f"{safe_value(row.get('national_material_code', ''))}."
            ),
            "national_migration_mapping.csv",
        )

    for _, row in reviews.iterrows():
        material_a = safe_value(row.get("material_id_a", ""))
        material_b = safe_value(row.get("material_id_b", ""))
        status = safe_value(row.get("review_status", "PENDING"))

        review_id = f"{material_a}|{material_b}"

        add_record(
            "REVIEW",
            review_id,
            f"REVIEW_{status}",
            (
                f"Reviewer: {safe_value(row.get('reviewer', ''))}; "
                f"Comment: {safe_value(row.get('review_comment', ''))}; "
                f"Approved harmonized ID: "
                f"{safe_value(row.get('approved_harmonized_id', ''))}."
            ),
            "review_approval_workflow.csv",
        )

    if not analytics.empty:
        add_record(
            "ANALYTICS",
            "PLATFORM",
            "ANALYTICS_GENERATED",
            (
                f"Platform KPI records generated: "
                f"{len(analytics)}."
            ),
            "analytics/platform_kpis.csv",
        )

    audit_df = pd.DataFrame(audit_records)

    if audit_df.empty:
        audit_df = pd.DataFrame(
            columns=[
                "audit_id",
                "timestamp",
                "actor",
                "entity_type",
                "entity_id",
                "action",
                "details",
                "source_file",
            ]
        )

    audit_df.to_csv(
        AUDIT_DIR / "audit_trail.csv",
        index=False,
    )

    summary = (
        audit_df.groupby(
            ["entity_type", "action"],
            dropna=False,
        )
        .size()
        .reset_index(name="record_count")
        if not audit_df.empty
        else pd.DataFrame(
            columns=[
                "entity_type",
                "action",
                "record_count",
            ]
        )
    )

    summary.to_csv(
        AUDIT_DIR / "audit_summary.csv",
        index=False,
    )

    print("Audit trail completed.")
    print(f"Audit output folder: {AUDIT_DIR}")
    print(f"Audit records created: {len(audit_df)}")


if __name__ == "__main__":
    main()