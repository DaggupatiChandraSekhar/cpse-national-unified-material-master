from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

RAW_DATA_FILE = DATA_DIR / "synthetic_cpse_materials.csv"
PROCESSED_DATA_FILE = OUTPUT_DIR / "processed_materials.csv"
MATCH_RESULTS_FILE = OUTPUT_DIR / "match_results.csv"
HARMONIZED_RESULTS_FILE = OUTPUT_DIR / "harmonized_materials.csv"
REVIEW_QUEUE_FILE = OUTPUT_DIR / "review_queue.csv"

RANDOM_SEED = 42

MATCH_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.65

STANDARD_COLUMNS = [
    "material_id",
    "material_description",
    "material_group",
    "unit_of_measure",
    "manufacturer",
    "part_number",
    "plant",
    "source_cpse",
]