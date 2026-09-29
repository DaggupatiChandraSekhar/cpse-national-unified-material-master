import re
import pandas as pd


def extract_attributes(description):
    """
    Extract common technical attributes from a material description.
    """

    description = str(description).upper()

    attributes = {
        "size": None,
        "length": None,
        "voltage": None,
        "diameter": None,
        "core_count": None,
        "material_type": None,
        "standard": None,
    }

    # Dimensions such as M16, M16 X 80, 6205, etc.
    size_match = re.search(r"\bM\d+\b", description)
    if size_match:
        attributes["size"] = size_match.group()

    # Length in millimeters
    length_match = re.search(r"\b(\d+)\s*MM\b", description)
    if length_match:
        attributes["length"] = int(length_match.group(1))

    # Voltage such as 1.1 KV or 1100 VOLT
    voltage_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(KV|VOLT|V)\b",
        description,
    )
    if voltage_match:
        attributes["voltage"] = voltage_match.group(0)

    # Diameter in millimeters
    diameter_match = re.search(r"\bDIA\s*(\d+)\s*MM\b", description)
    if diameter_match:
        attributes["diameter"] = int(diameter_match.group(1))

    # Cable core count
    core_match = re.search(r"\b(\d+)\s*CORE\b", description)
    if core_match:
        attributes["core_count"] = int(core_match.group(1))

    # Common material types
    material_types = [
        "STEEL",
        "MILD STEEL",
        "STAINLESS STEEL",
        "ABS",
        "XLPE",
        "PVC",
        "RUBBER",
        "ALUMINIUM",
        "COPPER",
    ]

    for material in material_types:
        if material in description:
            attributes["material_type"] = material
            break

    # Common standards and grades
    standards = [
        "ISO VG 68",
        "SAE 90",
        "SAE90",
        "ISO68",
        "HT",
        "2RS",
        "ZZ",
        "XLPE",
    ]

    for standard in standards:
        if standard in description:
            attributes["standard"] = standard
            break

    return attributes


def add_technical_attributes(df):
    """
    Add extracted technical attributes as columns.
    """

    df = df.copy()

    extracted = df["material_description"].apply(extract_attributes)
    extracted_df = pd.DataFrame(extracted.tolist(), index=df.index)

    df = pd.concat([df, extracted_df], axis=1)

    return df


if __name__ == "__main__":
    from src.config import PROCESSED_DATA_FILE, OUTPUT_DIR

    OUTPUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(PROCESSED_DATA_FILE)
    df = add_technical_attributes(df)

    df.to_csv(PROCESSED_DATA_FILE, index=False)

    print(f"Technical attributes extracted for {len(df)} records.")