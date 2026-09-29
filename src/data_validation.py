from pathlib import Path
import re

import pandas as pd

from src.config import DATA_DIR, OUTPUT_DIR, STANDARD_COLUMNS


REQUIRED_COLUMNS = [
    "material_id",
    "material_description",
    "material_group",
    "unit_of_measure",
    "manufacturer",
    "part_number",
    "plant",
    "source_cpse",
]

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

VALID_MATERIAL_ID_PATTERN = r"^[A-Za-z0-9._\-/]+$"


def load_material_file(file_path):
    """Load a CSV or Excel material master file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)

    raise ValueError(
        f"Unsupported file type: {path.suffix}. "
        "Use CSV, XLSX, or XLS."
    )


def _is_blank(series):
    """Return a boolean mask for null or whitespace-only values."""

    return (
        series.isna()
        | series.astype("string").str.strip().eq("")
    )


def validate_columns(df):
    """Check whether required columns are present."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    return {
        "valid": len(missing_columns) == 0,
        "missing_columns": missing_columns,
        "available_columns": list(df.columns),
    }


def _add_finding(findings, check, status, details, severity=None):
    finding = {
        "check": check,
        "status": status,
        "details": details,
    }

    if severity is not None:
        finding["severity"] = severity

    findings.append(finding)


def validate_material_data(df):
    """
    Generate validation findings for a material master.
    """

    findings = []

    column_check = validate_columns(df)

    if not column_check["valid"]:
        _add_finding(
            findings,
            "Required columns",
            "FAIL",
            "Missing columns: "
            + ", ".join(column_check["missing_columns"]),
            "CRITICAL",
        )

        return pd.DataFrame(findings)

    _add_finding(
        findings,
        "Required columns",
        "PASS",
        "All required columns are present.",
        "CRITICAL",
    )

    duplicate_count = int(
        df["material_id"].astype("string").duplicated().sum()
    )

    _add_finding(
        findings,
        "Duplicate material IDs",
        "PASS" if duplicate_count == 0 else "WARNING",
        f"{duplicate_count} duplicate material IDs found.",
        "HIGH",
    )

    for column in [
        "material_id",
        "material_description",
        "material_group",
        "unit_of_measure",
    ]:
        missing_count = int(_is_blank(df[column]).sum())

        _add_finding(
            findings,
            f"Missing values: {column}",
            "PASS" if missing_count == 0 else "WARNING",
            f"{missing_count} missing or blank values found.",
            "MEDIUM",
        )

    invalid_uom_count = int(
        (
            _is_blank(df["unit_of_measure"])
            | (
                df["unit_of_measure"]
                .astype("string")
                .str.strip()
                .str.upper()
                .isin(["UNKNOWN", "N/A", "NA", "NONE"])
            )
        ).sum()
    )

    _add_finding(
        findings,
        "Invalid units of measure",
        "PASS" if invalid_uom_count == 0 else "WARNING",
        f"{invalid_uom_count} invalid units of measure found.",
        "MEDIUM",
    )

    invalid_material_id_count = int(
        (
            ~_is_blank(df["material_id"])
            & ~df["material_id"]
            .astype("string")
            .str.strip()
            .str.match(VALID_MATERIAL_ID_PATTERN, na=False)
        ).sum()
    )

    _add_finding(
        findings,
        "Material ID format",
        "PASS" if invalid_material_id_count == 0 else "WARNING",
        (
            f"{invalid_material_id_count} material IDs contain "
            "unexpected characters."
        ),
        "MEDIUM",
    )

    invalid_cpse_count = int(
        _is_blank(df["source_cpse"]).sum()
    )

    _add_finding(
        findings,
        "Missing CPSE",
        "PASS" if invalid_cpse_count == 0 else "WARNING",
        f"{invalid_cpse_count} missing CPSE values found.",
        "MEDIUM",
    )

    invalid_plant_count = int(
        _is_blank(df["plant"]).sum()
    )

    _add_finding(
        findings,
        "Missing plant",
        "PASS" if invalid_plant_count == 0 else "WARNING",
        f"{invalid_plant_count} missing plant values found.",
        "MEDIUM",
    )

    empty_description_count = int(
        _is_blank(df["material_description"]).sum()
    )

    _add_finding(
        findings,
        "Empty material descriptions",
        "PASS" if empty_description_count == 0 else "WARNING",
        (
            f"{empty_description_count} empty material descriptions "
            "found."
        ),
        "HIGH",
    )

    return pd.DataFrame(findings)


def validate_migration_mapping(mapping_df):
    """
    Validate migration mapping records.
    """

    findings = []

    required_mapping_columns = [
        "material_id",
        "harmonized_material_id",
        "mapping_status",
    ]

    missing_columns = [
        column
        for column in required_mapping_columns
        if column not in mapping_df.columns
    ]

    if missing_columns:
        _add_finding(
            findings,
            "Migration mapping columns",
            "FAIL",
            "Missing columns: " + ", ".join(missing_columns),
            "CRITICAL",
        )

        return pd.DataFrame(findings)

    _add_finding(
        findings,
        "Migration mapping columns",
        "PASS",
        "All required mapping columns are present.",
        "CRITICAL",
    )

    missing_harmonized_ids = int(
        _is_blank(mapping_df["harmonized_material_id"]).sum()
    )

    _add_finding(
        findings,
        "Missing harmonized material IDs",
        "PASS" if missing_harmonized_ids == 0 else "FAIL",
        f"{missing_harmonized_ids} missing harmonized material IDs found.",
        "CRITICAL",
    )

    duplicate_material_ids = int(
        mapping_df["material_id"]
        .astype("string")
        .duplicated()
        .sum()
    )

    _add_finding(
        findings,
        "Duplicate mapping material IDs",
        "PASS"
        if duplicate_material_ids == 0
        else "WARNING",
        (
            f"{duplicate_material_ids} duplicate material IDs "
            "found in migration mapping."
        ),
        "HIGH",
    )

    allowed_statuses = {
        "AUTO_MATCHED",
        "REVIEW_REQUIRED",
        "REVIEW_APPROVED",
        "REVIEW_REJECTED",
    }

    invalid_status_count = int(
        (
            ~mapping_df["mapping_status"]
            .astype("string")
            .str.upper()
            .isin(allowed_statuses)
        ).sum()
    )

    _add_finding(
        findings,
        "Invalid mapping statuses",
        "PASS" if invalid_status_count == 0 else "WARNING",
        f"{invalid_status_count} invalid mapping statuses found.",
        "MEDIUM",
    )

    unresolved_review_count = 0

    if "review_required" in mapping_df.columns:
        unresolved_review_count = int(
            (
                mapping_df["review_required"].fillna(False).astype(bool)
                & ~mapping_df["mapping_status"]
                .astype("string")
                .str.upper()
                .eq("REVIEW_APPROVED")
            ).sum()
        )

    _add_finding(
        findings,
        "Unresolved review records",
        "PASS" if unresolved_review_count == 0 else "WARNING",
        (
            f"{unresolved_review_count} records still require "
            "review resolution."
        ),
        "HIGH",
    )

    return pd.DataFrame(findings)


def clean_material_data(df):
    """Prepare validated data for downstream processing."""

    cleaned = df.copy()

    for column in REQUIRED_COLUMNS:
        if column not in cleaned.columns:
            cleaned[column] = pd.NA

    text_columns = [
        "material_id",
        "material_description",
        "material_group",
        "manufacturer",
        "part_number",
        "plant",
        "source_cpse",
    ]

    for column in text_columns:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.strip()
        )

    cleaned["unit_of_measure"] = (
        cleaned["unit_of_measure"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    cleaned = cleaned.drop_duplicates(
        subset=["material_id"],
        keep="first",
    )

    return cleaned


def save_validation_outputs(
    df,
    validation_results,
    row_validation_results=None,
):
    """Save cleaned data and validation findings."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_file = OUTPUT_DIR / "validated_materials.csv"
    validation_file = OUTPUT_DIR / "validation_summary.csv"

    df.to_csv(cleaned_file, index=False)
    validation_results.to_csv(validation_file, index=False)

    row_validation_file = None

    if row_validation_results is not None:
        row_validation_file = OUTPUT_DIR / "row_validation_results.csv"
        row_validation_results.to_csv(
            row_validation_file,
            index=False,
        )

    return cleaned_file, validation_file, row_validation_file


def create_row_validation_results(df):
    """
    Create a row-level validation report for required fields.
    """

    results = df.copy()

    results["validation_status"] = "PASS"
    results["validation_issue_count"] = 0
    results["validation_issues"] = ""

    issues_by_row = []

    for index, row in results.iterrows():
        issues = []

        for column in REQUIRED_COLUMNS:
            if column not in results.columns:
                issues.append(f"Missing column: {column}")
                continue

            value = row[column]

            if pd.isna(value) or str(value).strip() == "":
                issues.append(f"Blank {column}")

        results.at[index, "validation_issue_count"] = len(issues)
        results.at[index, "validation_issues"] = "; ".join(issues)

        if issues:
            results.at[index, "validation_status"] = "FAIL"

        issues_by_row.append(issues)

    return results


def main():
    input_file = DATA_DIR / "synthetic_cpse_materials.csv"

    materials = load_material_file(input_file)

    validation_results = validate_material_data(materials)
    row_validation_results = create_row_validation_results(materials)

    cleaned_materials = clean_material_data(materials)

    (
        cleaned_file,
        validation_file,
        row_validation_file,
    ) = save_validation_outputs(
        cleaned_materials,
        validation_results,
        row_validation_results,
    )

    print(f"Input records: {len(materials)}")
    print(f"Validated records: {len(cleaned_materials)}")
    print(f"Saved cleaned data to: {cleaned_file}")
    print(f"Saved validation summary to: {validation_file}")
    print(f"Saved row validation to: {row_validation_file}")

    print("\nValidation summary:")
    print(validation_results.to_string(index=False))


if __name__ == "__main__":
    main()