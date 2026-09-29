import re
import pandas as pd

from src.config import OUTPUT_DIR


UNIT_MAP = {
    "EA": "EA",
    "EACH": "EA",
    "PCS": "EA",
    "PC": "EA",
    "NOS": "EA",
    "NO": "EA",
    "UNIT": "EA",
    "UN": "EA",
    "KG": "KG",
    "KGS": "KG",
    "KILOGRAM": "KG",
    "M": "M",
    "MTR": "M",
    "METER": "M",
    "METRE": "M",
    "MM": "MM",
    "L": "L",
    "LTR": "L",
    "LITRE": "L",
    "LITER": "L",
    "ML": "ML",
    "V": "V",
    "VOLT": "V",
    "VOLTS": "V",
    "A": "A",
    "AMP": "A",
    "AMPS": "A",
    "W": "W",
    "WATT": "W",
    "KW": "KW",
    "KVA": "KVA",
    "HZ": "HZ",
    "M2": "M2",
    "SQM": "M2",
    "M3": "M3",
    "CBM": "M3",
}


MANUFACTURER_ALIASES = {
    "SIEMENS LTD": "SIEMENS",
    "SIEMENS LIMITED": "SIEMENS",
    "ABB LTD": "ABB",
    "ABB LIMITED": "ABB",
    "SCHNEIDER ELECTRIC INDIA": "SCHNEIDER ELECTRIC",
    "SCHNEIDER ELECTRIC INDIA PVT LTD": "SCHNEIDER ELECTRIC",
    "GE INDIA": "GE",
    "GENERAL ELECTRIC": "GE",
    "TATA STEEL LIMITED": "TATA STEEL",
    "TATA STEEL LTD": "TATA STEEL",
}


def normalize_unit(unit):
    """Convert common unit variations into a standard unit."""

    if pd.isna(unit):
        return pd.NA

    value = str(unit).strip().upper()

    if not value:
        return pd.NA

    return UNIT_MAP.get(value, value)


def normalize_manufacturer(value):
    """Standardize manufacturer text and known aliases."""

    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    if not value:
        return pd.NA

    value = re.sub(r"[^A-Z0-9 ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    value = MANUFACTURER_ALIASES.get(value, value)

    return value


def normalize_part_number(value):
    """
    Standardize part-number formatting while preserving meaningful
    alphanumeric structure.
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    if not value:
        return pd.NA

    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[^A-Z0-9./_-]", "", value)

    return value


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def classify_material(row):
    """Assign a broad material classification."""

    group = str(row.get("material_group", "")).upper()
    description = str(row.get("material_description", "")).upper()
    material_type = str(row.get("material_type", "")).upper()

    text = f"{group} {description} {material_type}"

    if _contains_any(
        text,
        ["FASTENER", "BOLT", "NUT", "WASHER", "SCREW", "RIVET"],
    ):
        return "FASTENERS"

    if _contains_any(
        text,
        ["BEARING", "ROLLER", "BALL BEARING", "BUSH", "BUSHING"],
    ):
        return "BEARINGS"

    if _contains_any(
        text,
        ["CABLE", "WIRE", "CONDUCTOR", "SWITCH", "BREAKER", "RELAY"],
    ):
        return "ELECTRICAL"

    if _contains_any(
        text,
        ["PIPE", "VALVE", "FLANGE", "FITTING", "ELBOW", "TEE"],
    ):
        return "PIPES_VALVES_FITTINGS"

    if _contains_any(
        text,
        ["PUMP", "MOTOR", "COMPRESSOR", "TURBINE", "GEARBOX"],
    ):
        return "ROTATING_EQUIPMENT"

    if _contains_any(
        text,
        ["OIL", "GREASE", "LUBRICANT", "HYDRAULIC FLUID"],
    ):
        return "LUBRICANTS"

    if _contains_any(
        text,
        ["GLOVE", "HELMET", "SAFETY", "MASK", "GOGGLE", "PPE"],
    ):
        return "SAFETY_ITEMS"

    if _contains_any(
        text,
        ["BEAM", "PLATE", "SHEET", "CHANNEL", "ANGLE", "STRUCTURAL"],
    ):
        return "STRUCTURAL_MATERIALS"

    if _contains_any(
        text,
        ["FILTER", "STRAINER", "CARTRIDGE"],
    ):
        return "FILTERS"

    if _contains_any(
        text,
        ["CHEMICAL", "SOLVENT", "ADHESIVE", "SEALANT"],
    ):
        return "CHEMICALS"

    return "GENERAL_MATERIAL"


def create_standard_description(row):
    """Create a consistent description from available attributes."""

    parts = []

    description = row.get("material_description", "")
    material_type = row.get("material_type", "")
    standard = row.get("standard", "")
    size = row.get("size", "")
    length = row.get("length", "")
    voltage = row.get("voltage", "")
    diameter = row.get("diameter", "")
    core_count = row.get("core_count", "")
    material_grade = row.get("material_grade", "")

    if pd.notna(description) and str(description).strip():
        parts.append(str(description).strip().upper())

    attributes = [
        ("TYPE", material_type),
        ("GRADE", material_grade),
        ("STD", standard),
        ("SIZE", size),
        ("LENGTH", length),
        ("VOLTAGE", voltage),
        ("DIAMETER", diameter),
        ("CORES", core_count),
    ]

    for label, value in attributes:
        if pd.notna(value) and str(value).strip():
            normalized_value = str(value).strip().upper()
            parts.append(f"{label}:{normalized_value}")

    return " | ".join(parts)


def calculate_standardization_confidence(row):
    """
    Estimate whether the standardized record has sufficient
    information for downstream harmonization.
    """

    available_fields = [
        "material_description",
        "material_group",
        "unit_of_measure",
        "manufacturer",
        "part_number",
    ]

    populated_count = sum(
        pd.notna(row.get(field))
        and str(row.get(field)).strip() != ""
        for field in available_fields
    )

    if populated_count >= 5:
        return "HIGH"

    if populated_count >= 3:
        return "MEDIUM"

    return "LOW"


def identify_standardization_issues(row):
    """Identify missing information that may affect matching."""

    issues = []

    if pd.isna(row.get("material_description")):
        issues.append("MISSING_DESCRIPTION")

    if pd.isna(row.get("unit_of_measure")):
        issues.append("MISSING_UOM")

    if pd.isna(row.get("material_group")):
        issues.append("MISSING_MATERIAL_GROUP")

    if pd.isna(row.get("manufacturer")):
        issues.append("MISSING_MANUFACTURER")

    if pd.isna(row.get("part_number")):
        issues.append("MISSING_PART_NUMBER")

    return ";".join(issues)


def standardize_materials(df):
    """Apply standardization and classification to all materials."""

    standardized = df.copy()

    standardized["standardized_unit_of_measure"] = (
        standardized["unit_of_measure"].apply(normalize_unit)
    )

    standardized["standardized_manufacturer"] = (
        standardized["manufacturer"].apply(normalize_manufacturer)
    )

    standardized["standardized_part_number"] = (
        standardized["part_number"].apply(normalize_part_number)
    )

    standardized["material_classification"] = standardized.apply(
        classify_material,
        axis=1,
    )

    standardized["standardized_description"] = standardized.apply(
        create_standard_description,
        axis=1,
    )

    standardized["standardization_confidence"] = standardized.apply(
        calculate_standardization_confidence,
        axis=1,
    )

    standardized["standardization_issues"] = standardized.apply(
        identify_standardization_issues,
        axis=1,
    )

    standardized["standardization_status"] = "STANDARDIZED"

    standardized.loc[
        standardized["standardization_confidence"] == "LOW",
        "standardization_status",
    ] = "NEEDS_REVIEW"

    return standardized


def create_standardization_summary(standardized):
    """Create summary statistics for standardized materials."""

    summary = pd.DataFrame(
        [
            {
                "total_records": len(standardized),
                "standardized_records": int(
                    (
                        standardized["standardization_status"]
                        == "STANDARDIZED"
                    ).sum()
                ),
                "needs_review_records": int(
                    (
                        standardized["standardization_status"]
                        == "NEEDS_REVIEW"
                    ).sum()
                ),
                "high_confidence": int(
                    (
                        standardized["standardization_confidence"]
                        == "HIGH"
                    ).sum()
                ),
                "medium_confidence": int(
                    (
                        standardized["standardization_confidence"]
                        == "MEDIUM"
                    ).sum()
                ),
                "low_confidence": int(
                    (
                        standardized["standardization_confidence"]
                        == "LOW"
                    ).sum()
                ),
                "unique_classifications": standardized[
                    "material_classification"
                ].nunique(),
            }
        ]
    )

    return summary


def main():
    input_file = OUTPUT_DIR / "validated_materials.csv"

    if not input_file.exists():
        raise FileNotFoundError(
            "validated_materials.csv not found. "
            "Run data_validation.py first."
        )

    materials = pd.read_csv(input_file)

    standardized = standardize_materials(materials)

    output_file = OUTPUT_DIR / "standardized_materials.csv"
    summary_file = OUTPUT_DIR / "standardization_summary.csv"

    standardized.to_csv(output_file, index=False)

    summary = create_standardization_summary(standardized)
    summary.to_csv(summary_file, index=False)

    print(f"Input records: {len(materials)}")
    print(f"Standardized records: {len(standardized)}")
    print(f"Saved to: {output_file}")
    print(f"Saved summary to: {summary_file}")

    print("\nMaterial classifications:")
    print(
        standardized["material_classification"]
        .value_counts()
        .to_string()
    )

    print("\nStandardization confidence:")
    print(
        standardized["standardization_confidence"]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()