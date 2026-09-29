from pathlib import Path
import csv
import random


random.seed(42)

OUTPUT_FILE = Path("data/synthetic_cpse_materials.csv")

cpse_data = {
    "CPSE_A": ["PLANT01", "PLANT02"],
    "CPSE_B": ["PLANT03", "PLANT04"],
    "CPSE_C": ["PLANT05", "PLANT06"],
    "CPSE_D": ["PLANT07", "PLANT08"],
}

materials = [
    ("FASTENERS", "HEX BOLT M16 X 80 MM HIGH TENSILE STEEL", "EA", "TVS", "M16-80-HT"),
    ("FASTENERS", "M16 HEXAGONAL BOLT 80MM HT STEEL", "EA", "TVS", "M16-80-HT"),
    ("FASTENERS", "HEX NUT M16 HIGH TENSILE STEEL", "EA", "TVS", "M16-NUT-HT"),
    ("FASTENERS", "M16 HEX NUT HT STEEL", "EA", "TVS", "M16-NUT-HT"),
    ("FASTENERS", "FLAT WASHER M16 MS", "EA", "UNBRANDED", "M16-WASHER"),
    ("FASTENERS", "M16 PLAIN WASHER MILD STEEL", "EA", "UNBRANDED", "M16-WASHER"),
    ("BEARINGS", "BEARING BALL 6205 ZZ", "EA", "SKF", "6205-ZZ"),
    ("BEARINGS", "BALL BEARING 6205 ZZ SKF", "EA", "SKF", "6205-ZZ"),
    ("BEARINGS", "DEEP GROOVE BALL BEARING 6206 2RS", "EA", "FAG", "6206-2RS"),
    ("BEARINGS", "6206 DOUBLE SEALED BALL BEARING FAG", "EA", "FAG", "6206-2RS"),
    ("LUBRICANTS", "INDUSTRIAL LUBRICANT ISO VG 68", "LTR", "SERVO", "ISO68"),
    ("LUBRICANTS", "HYDRAULIC OIL ISO VG 68", "LTR", "SERVO", "ISO68"),
    ("LUBRICANTS", "GEAR OIL SAE 90", "LTR", "CASTROL", "SAE90"),
    ("LUBRICANTS", "INDUSTRIAL GEAR LUBRICANT SAE 90", "LTR", "CASTROL", "SAE90"),
    ("CABLES", "POWER CABLE 4 CORE 1.1 KV XLPE", "MTR", "POLYCAB", "4C-1.1KV"),
    ("CABLES", "4 CORE XLPE POWER CABLE 1100 VOLT", "MTR", "POLYCAB", "4C-1.1KV"),
    ("CABLES", "PVC INSULATED CONTROL CABLE 2.5 SQ MM", "MTR", "FINOLEX", "2.5SQMM"),
    ("CABLES", "CONTROL CABLE PVC 2.5 MM2", "MTR", "FINOLEX", "2.5SQMM"),
    ("SAFETY", "INDUSTRIAL SAFETY HELMET ABS", "EA", "KARAM", "HELMET-ABS"),
    ("SAFETY", "ABS HARD HAT INDUSTRIAL SAFETY", "EA", "KARAM", "HELMET-ABS"),
]


rows = []

for i in range(300):
    cpse = list(cpse_data.keys())[i % 4]
    plants = cpse_data[cpse]
    plant = plants[i % len(plants)]

    material = materials[i % len(materials)]

    material_group, description, uom, manufacturer, part_number = material

    rows.append({
        "material_id": f"MAT{i + 1:03d}",
        "material_description": description,
        "material_group": material_group,
        "unit_of_measure": uom,
        "manufacturer": manufacturer,
        "part_number": part_number,
        "plant": plant,
        "source_cpse": cpse,
    })


OUTPUT_FILE.parent.mkdir(exist_ok=True)

with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "material_id",
            "material_description",
            "material_group",
            "unit_of_measure",
            "manufacturer",
            "part_number",
            "plant",
            "source_cpse",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Created {len(rows)} records.")
print(f"Saved to: {OUTPUT_FILE}")