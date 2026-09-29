from src.config import OUTPUT_DIR
import pandas as pd


INPUT_FILE = OUTPUT_DIR / "standardized_materials.csv"
OUTPUT_FILE = OUTPUT_DIR / "national_material_master.csv"
SUMMARY_FILE = OUTPUT_DIR / "national_code_summary.csv"


CLASS_PREFIXES = {
    "FASTENERS": "FST",
    "BEARINGS": "BRG",
    "ELECTRICAL": "ELC",
    "PIPES_VALVES_FITTINGS": "PVF",
    "ROTATING_EQUIPMENT": "ROT",
    "LUBRICANTS": "LUB",
    "SAFETY_ITEMS": "SFT",
    "GENERAL_MATERIAL": "GEN",
}


def clean_value(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def generate_codes(df):
    df = df.copy()

    counters = {}
    national_codes = []

    for _, row in df.iterrows():
        material_class = clean_value(
            row.get("material_classification", "")
        ).upper()

        prefix = CLASS_PREFIXES.get(
            material_class,
            "GEN"
        )

        counters[prefix] = counters.get(prefix, 0) + 1
        sequence = counters[prefix]

        national_code = f"IN-{prefix}-{sequence:05d}"
        national_codes.append(national_code)

    df["national_material_code"] = national_codes
    df["national_code_status"] = "ACTIVE"
    df["national_code_version"] = "v1"
    df["national_code_source"] = "standardized_materials"

    df["national_material_name"] = (
        df["standardized_description"]
        .fillna(df.get("material_description", ""))
        .replace("", pd.NA)
        .fillna("UNSPECIFIED MATERIAL")
    )

    df["national_material_group"] = (
        df["material_classification"]
        .fillna("GENERAL_MATERIAL")
        .replace("", "GENERAL_MATERIAL")
    )

    df["source_material_id"] = df["material_id"].astype(str)

    df["national_code_generation_status"] = "GENERATED"

    return df


def build_summary(result):
    summary = (
        result.groupby(
            [
                "national_material_group",
                "national_code_status",
                "national_code_generation_status",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="material_count")
        .sort_values(
            ["national_material_group", "material_count"],
            ascending=[True, False],
        )
    )

    summary["national_code_prefix"] = summary[
        "national_material_group"
    ].map(CLASS_PREFIXES).fillna("GEN")

    return summary


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "material_id",
        "standardized_description",
        "material_classification",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df["material_id"].duplicated().any():
        duplicate_ids = (
            df.loc[
                df["material_id"].duplicated(keep=False),
                "material_id",
            ]
            .astype(str)
            .unique()
            .tolist()
        )

        raise ValueError(
            "Duplicate material IDs found before code generation: "
            f"{duplicate_ids[:10]}"
        )

    result = generate_codes(df)

    if result["national_material_code"].duplicated().any():
        raise ValueError(
            "Duplicate national material codes generated."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(OUTPUT_FILE, index=False)

    summary = build_summary(result)
    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"Created: {OUTPUT_FILE}")
    print(f"Created: {SUMMARY_FILE}")
    print(f"Total records: {len(result)}")
    print(f"Unique national codes: {result['national_material_code'].nunique()}")

    print(
        result[
            [
                "material_id",
                "national_material_code",
                "national_material_name",
                "national_material_group",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()