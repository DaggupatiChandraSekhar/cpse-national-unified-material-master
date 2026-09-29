import subprocess
import sys


PIPELINE_MODULES = [
    "src.data_validation",
    "src.preprocessing",
    "src.attribute_extraction",
    "src.candidate_generation",
    "src.matching_engine",
    "src.evaluation",
    "src.harmonization",
    "src.review_queue",
    "src.migration_mapping",
    "src.standardization",
    "src.national_code_generation",
    "src.national_migration_mapping",
    "src.duplicate_detection",
    "src.review_approval_workflow",
    "src.analytics_engine",
    "src.audit_trail",
]


def run_module(module_name):
    print("\n" + "=" * 70)
    print(f"RUNNING: {module_name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, "-m", module_name],
        check=False,
    )

    if result.returncode != 0:
        print(f"\nFAILED: {module_name}")
        sys.exit(result.returncode)

    print(f"COMPLETED: {module_name}")


def main():
    print("CPSE NATIONAL UNIFIED MATERIAL MASTER PIPELINE")
    print("=" * 70)

    for module_name in PIPELINE_MODULES:
        run_module(module_name)

    print("\n" + "=" * 70)
    print("FULL PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
