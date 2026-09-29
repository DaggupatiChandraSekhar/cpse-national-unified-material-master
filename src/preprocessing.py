import re
import pandas as pd


def normalize_text(value):
    """Normalize text for consistent matching."""
    if pd.isna(value):
        return ""

    value = str(value).upper().strip()

    value = value.replace("&", " AND ")
    value = value.replace("-", " ")
    value = value.replace("/", " ")
    value = value.replace(".", " ")

    value = re.sub(r"\s+", " ", value)

    return value


def normalize_materials(df):
    """Apply text normalization to material master data."""
    df = df.copy()

    text_columns = [
        "material_description",
        "material_group",
        "unit_of_measure",
        "manufacturer",
        "part_number",
        "plant",
        "source_cpse",
    ]

    for column in text_columns:
        if column in df.columns:
            df[f"{column}_normalized"] = df[column].apply(normalize_text)

    return df


def load_and_preprocess(input_file):
    """Load the raw CSV and return normalized material data."""
    df = pd.read_csv(input_file)

    df = normalize_materials(df)

    return df


if __name__ == "__main__":
    from src.config import RAW_DATA_FILE, PROCESSED_DATA_FILE, OUTPUT_DIR

    OUTPUT_DIR.mkdir(exist_ok=True)

    processed_df = load_and_preprocess(RAW_DATA_FILE)
    processed_df.to_csv(PROCESSED_DATA_FILE, index=False)

    print(f"Processed records: {len(processed_df)}")
    print(f"Saved to: {PROCESSED_DATA_FILE}")