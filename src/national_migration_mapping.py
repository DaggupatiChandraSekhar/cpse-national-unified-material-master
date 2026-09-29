from datetime import datetime, timezone

from src.config import OUTPUT_DIR
import pandas as pd


INPUT_FILE = OUTPUT_DIR / "national_material_master.csv"
REVIEW_FILE = OUTPUT_DIR / "review_queue.csv"

OUTPUT_FILE = OUTPUT_DIR / "national_migration_mapping.csv"
SUMMARY_FILE = OUTPUT_DIR / "national_migration_mapping_summary.csv"


MIGRATION_BATCH = "BATCH-001"


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def get_review_columns(review_df):
    return {
        "material_id_a",
        "material_id_b",
        "review_status",
        "review_decision",
        "approved_national_material_code",
        "review_reason",
    }.intersection(review_df.columns)


def build_review_lookup(review_df):
    review_lookup = {}

    for _, row in review_df.iterrows():
        status = clean_text(
            row.get("review_status", "")
        ).upper()

        decision = clean_text(
            row.get("review_decision", "")
        ).upper()

        approved_code = clean_text(
            row.get("approved_national_material_code", "")
        )

        review_reason = clean_text(
            row.get("review_reason", "")
        )

        for column in ["material_id_a", "material_id_b"]:
            if column not in review_df.columns:
                continue

            material_id = clean_text(row.get(column, ""))

            if not material_id:
                continue

            review_lookup[material_id] = {
                "review_status": status,
                "review_decision": decision,
                "approved_national_material_code": approved_code,
                "review_reason": review_reason,
            }

    return review_lookup


def build_mapping(df):
    required_columns = [
        "material_id",
        "source_cpse",
        "plant",
        "material_description",
        "standardized_description",
        "material_classification",
        "national_material_code",
        "national_material_name",
        "national_code_status",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    mapping = df[required_columns].copy()

    mapping.rename(
        columns={
            "material_id": "legacy_material_id",
            "source_cpse": "legacy_cpse",
            "plant": "legacy_plant",
            "material_description": "legacy_description",
        },
        inplace=True,
    )

    mapping["legacy_material_id"] = (
        mapping["legacy_material_id"].astype(str)
    )

    mapping["migration_batch"] = MIGRATION_BATCH
    mapping["migration_status"] = "READY_FOR_MIGRATION"
    mapping["review_required"] = False
    mapping["review_status"] = "NOT_REQUIRED"
    mapping["review_decision"] = ""
    mapping["approved_national_material_code"] = ""
    mapping["review_reason"] = ""
    mapping["mapping_created_at"] = utc_timestamp()

    return mapping


def apply_review_decisions(mapping, review_df):
    if review_df.empty:
        return mapping

    review_lookup = build_review_lookup(review_df)

    for index, row in mapping.iterrows():
        material_id = clean_text(
            row["legacy_material_id"]
        )

        review = review_lookup.get(material_id)

        if not review:
            continue

        status = review["review_status"]
        decision = review["review_decision"]
        approved_code = review["approved_national_material_code"]
        review_reason = review["review_reason"]

        mapping.loc[index, "review_required"] = True
        mapping.loc[index, "review_status"] = (
            status if status else "PENDING"
        )
        mapping.loc[index, "review_decision"] = decision
        mapping.loc[index, "approved_national_material_code"] = (
            approved_code
        )

        if review_reason:
            mapping.loc[index, "review_reason"] = review_reason
        else:
            mapping.loc[index, "review_reason"] = (
                "Material appears in review workflow"
            )

        if decision in {"APPROVED", "ACCEPTED"}:
            mapping.loc[index, "migration_status"] = (
                "REVIEW_APPROVED"
            )

            if approved_code:
                mapping.loc[index, "national_material_code"] = (
                    approved_code
                )

        elif decision in {"REJECTED", "DECLINED"}:
            mapping.loc[index, "migration_status"] = (
                "REVIEW_REJECTED"
            )

        else:
            mapping.loc[index, "migration_status"] = (
                "REVIEW_REQUIRED"
            )

    return mapping


def build_summary(mapping):
    summary = (
        mapping.groupby(
            [
                "migration_status",
                "review_required",
                "review_status",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="material_count")
        .sort_values(
            "material_count",
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

    mapping = build_mapping(df)

    review_df = pd.DataFrame()

    if REVIEW_FILE.exists():
        review_df = pd.read_csv(REVIEW_FILE)

        if not review_df.empty:
            mapping = apply_review_decisions(
                mapping,
                review_df,
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    mapping.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    summary = build_summary(mapping)

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
    )

    print(f"Created: {OUTPUT_FILE}")
    print(f"Created: {SUMMARY_FILE}")
    print(f"Total mappings: {len(mapping)}")
    print(
        mapping["migration_status"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()