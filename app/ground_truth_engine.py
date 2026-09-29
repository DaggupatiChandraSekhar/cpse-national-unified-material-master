from pathlib import Path
from datetime import datetime
import hashlib
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Your current project stores CSV outputs at the project root.
ROOT_DATA_DIR = PROJECT_ROOT

# Future-compatible outputs directory.
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Prefer the current root-level files when they exist.
# This keeps the existing project working without moving files.
GROUND_TRUTH_FILE = (
    ROOT_DATA_DIR / "ground_truth_labels.csv"
    if (ROOT_DATA_DIR / "ground_truth_labels.csv").exists()
    else OUTPUT_DIR / "ground_truth_labels.csv"
)

MATCH_RESULTS_FILE = (
    ROOT_DATA_DIR / "match_results.csv"
    if (ROOT_DATA_DIR / "match_results.csv").exists()
    else OUTPUT_DIR / "match_results.csv"
)

GROUND_TRUTH_AUDIT_FILE = (
    ROOT_DATA_DIR / "ground_truth_audit.csv"
    if (ROOT_DATA_DIR / "ground_truth_audit.csv").exists()
    else OUTPUT_DIR / "ground_truth_audit.csv"
)


# ============================================================
# VERSION
# ============================================================

GROUND_TRUTH_ENGINE_VERSION = "cpse-ground-truth-v3"


# ============================================================
# GROUND TRUTH SCHEMA
# ============================================================

GROUND_TRUTH_COLUMNS = [
    "ground_truth_id",
    "material_id_a",
    "material_id_b",
    "ai_prediction",
    "ai_confidence",
    "confidence_band",
    "candidate_rank",
    "confidence_gap",
    "technical_conflict_flag",
    "technical_conflict_severity",
    "model_version",
    "ground_truth_label",
    "reviewer_name",
    "review_status",
    "review_date",
    "review_comments",
    "evidence_reference",
    "ground_truth_engine_version",
]


GROUND_TRUTH_LABELS = [
    "IDENTICAL",
    "DUPLICATE",
    "NEAR_DUPLICATE",
    "FUNCTIONALLY_EQUIVALENT",
    "NO_MATCH",
    "REVIEW_REQUIRED",
]


REVIEW_STATUSES = [
    "VALIDATED",
    "ADJUDICATION_REQUIRED",
]


# ============================================================
# FILE MANAGEMENT
# ============================================================

def _ensure_parent(path):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def ensure_ground_truth_file():
    _ensure_parent(GROUND_TRUTH_FILE)

    if not GROUND_TRUTH_FILE.exists():
        df = pd.DataFrame(
            columns=GROUND_TRUTH_COLUMNS
        )

        df.to_csv(
            GROUND_TRUTH_FILE,
            index=False,
        )


def ensure_ground_truth_audit_file():
    _ensure_parent(GROUND_TRUTH_AUDIT_FILE)

    audit_columns = [
        "audit_id",
        "timestamp",
        "event_type",
        "ground_truth_id",
        "reviewer_name",
        "details",
        "previous_hash",
        "event_hash",
    ]

    if not GROUND_TRUTH_AUDIT_FILE.exists():
        pd.DataFrame(
            columns=audit_columns
        ).to_csv(
            GROUND_TRUTH_AUDIT_FILE,
            index=False,
        )


def load_ground_truth():
    ensure_ground_truth_file()

    try:
        df = pd.read_csv(
            GROUND_TRUTH_FILE
        )
    except Exception:
        df = pd.DataFrame()

    for column in GROUND_TRUTH_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df[GROUND_TRUTH_COLUMNS].copy()


def save_ground_truth(df):
    ensure_ground_truth_file()

    df = df.copy()

    for column in GROUND_TRUTH_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[GROUND_TRUTH_COLUMNS]

    df.to_csv(
        GROUND_TRUTH_FILE,
        index=False,
    )


# ============================================================
# MATCH RESULT LOADING
# ============================================================

def load_match_results():
    """
    Load AI-generated match results.

    The project currently stores match_results.csv at the
    project root. The fallback supports outputs/ for future
    deployment layouts.
    """

    if not MATCH_RESULTS_FILE.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(
            MATCH_RESULTS_FILE
        )
    except Exception:
        return pd.DataFrame()


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(value):
    try:
        if pd.isna(value):
            return np.nan

        return float(value)

    except Exception:
        return np.nan


def safe_string(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def confidence_band(value):
    value = safe_float(value)

    if pd.isna(value):
        return "UNKNOWN"

    if value >= 0.90:
        return "VERY_HIGH"

    if value >= 0.85:
        return "HIGH"

    if value >= 0.75:
        return "MEDIUM"

    if value >= 0.65:
        return "LOW"

    return "VERY_LOW"


def canonical_pair_key(material_a, material_b):
    """
    Canonical pair key.

    A-B and B-A represent the same material pair.
    """

    a = safe_string(material_a)
    b = safe_string(material_b)

    return tuple(
        sorted(
            [a, b]
        )
    )


# Backward-compatible alias.
def pair_key(material_a, material_b):
    return canonical_pair_key(
        material_a,
        material_b,
    )


# ============================================================
# AI FIELD NORMALIZATION
# ============================================================

def normalize_match_results(df):

    if df.empty:
        return df.copy()

    out = df.copy()

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if "match_confidence" not in out.columns:

        if "confidence_score" in out.columns:

            out["match_confidence"] = pd.to_numeric(
                out["confidence_score"],
                errors="coerce",
            )

        elif "match_score" in out.columns:

            out["match_confidence"] = pd.to_numeric(
                out["match_score"],
                errors="coerce",
            )

        else:

            out["match_confidence"] = np.nan

    else:

        out["match_confidence"] = pd.to_numeric(
            out["match_confidence"],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Confidence band
    # --------------------------------------------------------

    if "confidence_band" not in out.columns:

        out["confidence_band"] = (
            out["match_confidence"]
            .apply(confidence_band)
        )

    else:

        out["confidence_band"] = (
            out["confidence_band"]
            .fillna("")
            .astype(str)
            .str.upper()
        )

    # --------------------------------------------------------
    # AI decision
    # --------------------------------------------------------

    if "match_decision" not in out.columns:

        if "decision" in out.columns:

            out["match_decision"] = (
                out["decision"]
            )

        elif "ai_prediction" in out.columns:

            out["match_decision"] = (
                out["ai_prediction"]
            )

        else:

            out["match_decision"] = ""

    out["match_decision"] = (
        out["match_decision"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    # --------------------------------------------------------
    # Technical conflict
    # --------------------------------------------------------

    if "technical_conflict_flag" not in out.columns:
        out["technical_conflict_flag"] = False

    if "technical_conflict_severity" not in out.columns:
        out["technical_conflict_severity"] = "NONE"

    # --------------------------------------------------------
    # Ranking / ambiguity
    # --------------------------------------------------------

    if "candidate_rank" not in out.columns:
        out["candidate_rank"] = ""

    if "confidence_gap" not in out.columns:
        out["confidence_gap"] = ""

    if "ambiguity_flag" not in out.columns:
        out["ambiguity_flag"] = False

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    if "model_version" not in out.columns:
        out["model_version"] = ""

    return out


# ============================================================
# EXISTING LABEL LOOKUP
# ============================================================

def existing_ground_truth_keys():

    gt = load_ground_truth()

    if gt.empty:
        return set()

    keys = set()

    for _, row in gt.iterrows():

        keys.add(
            canonical_pair_key(
                row["material_id_a"],
                row["material_id_b"],
            )
        )

    return keys


# ============================================================
# REVIEW PRIORITY
# ============================================================

def calculate_priority(row):

    priority = 0

    conflict = safe_string(
        row.get(
            "technical_conflict_flag",
            "",
        )
    ).lower()

    if conflict in [
        "true",
        "1",
        "yes",
    ]:
        priority += 100

    severity = safe_string(
        row.get(
            "technical_conflict_severity",
            "",
        )
    ).upper()

    severity_weights = {
        "CRITICAL": 100,
        "HIGH": 80,
        "MEDIUM": 50,
        "LOW": 20,
        "NONE": 0,
    }

    priority += severity_weights.get(
        severity,
        0,
    )

    ambiguity = safe_string(
        row.get(
            "ambiguity_flag",
            "",
        )
    ).lower()

    if ambiguity in [
        "true",
        "1",
        "yes",
    ]:
        priority += 50

    decision = safe_string(
        row.get(
            "match_decision",
            "",
        )
    ).upper()

    if decision == "REVIEW":
        priority += 40

    confidence = safe_float(
        row.get(
            "match_confidence",
            np.nan,
        )
    )

    if not pd.isna(confidence):

        # Lower-confidence candidates require more review.
        priority += int(
            max(
                0,
                (1.0 - confidence) * 100,
            )
        )

    rank = safe_float(
        row.get(
            "candidate_rank",
            np.nan,
        )
    )

    if not pd.isna(rank):

        if rank == 1:
            priority += 20

        elif rank <= 5:
            priority += 10

    return priority


# ============================================================
# STRATIFIED GROUND TRUTH QUEUE
# ============================================================

def build_ground_truth_queue(
    sample_size=None,
    include_all=False,
):
    """
    Build a human-review queue from AI predictions.

    The queue:
    - excludes already-labelled pairs
    - uses canonical pair identity
    - prioritizes technical conflicts and ambiguity
    - preserves AI evidence
    - does NOT convert AI predictions into Ground Truth
    """

    matches = normalize_match_results(
        load_match_results()
    )

    if matches.empty:
        return pd.DataFrame()

    labelled = existing_ground_truth_keys()

    matches = matches.copy()

    matches["_pair_key"] = matches.apply(
        lambda row: canonical_pair_key(
            row.get(
                "material_id_a",
                "",
            ),
            row.get(
                "material_id_b",
                "",
            ),
        ),
        axis=1,
    )

    queue = matches[
        ~matches["_pair_key"].isin(
            labelled
        )
    ].copy()

    if queue.empty:
        return queue

    queue["_review_priority"] = queue.apply(
        calculate_priority,
        axis=1,
    )

    # --------------------------------------------------------
    # Stratification flags
    # --------------------------------------------------------

    queue["_confidence_bucket"] = pd.cut(
        queue["match_confidence"],
        bins=[
            -np.inf,
            0.65,
            0.75,
            0.85,
            0.90,
            np.inf,
        ],
        labels=[
            "VERY_LOW_LOW",
            "MEDIUM",
            "HIGH",
            "VERY_HIGH",
            "VERY_HIGH_PLUS",
        ],
        include_lowest=True,
    )

    queue["_review_reason"] = "STANDARD_REVIEW"

    conflict_mask = (
        queue[
            "technical_conflict_severity"
        ]
        .astype(str)
        .str.upper()
        .isin(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
            ]
        )
    )

    queue.loc[
        conflict_mask,
        "_review_reason",
    ] = "TECHNICAL_CONFLICT"

    review_mask = (
        queue[
            "match_decision"
        ]
        .astype(str)
        .str.upper()
        == "REVIEW"
    )

    queue.loc[
        review_mask,
        "_review_reason",
    ] = "AI_REVIEW"

    ambiguity_mask = (
        queue[
            "ambiguity_flag"
        ]
        .astype(str)
        .str.lower()
        .isin(
            [
                "true",
                "1",
                "yes",
            ]
        )
    )

    queue.loc[
        ambiguity_mask,
        "_review_reason",
    ] = "AMBIGUITY"

    # --------------------------------------------------------
    # Sort by review priority
    # --------------------------------------------------------

    queue = queue.sort_values(
        [
            "_review_priority",
            "candidate_rank",
        ],
        ascending=[
            False,
            True,
        ],
    )

    if (
        sample_size is not None
        and not include_all
    ):
        try:
            sample_size = int(
                sample_size
            )
        except Exception:
            sample_size = None

        if (
            sample_size is not None
            and sample_size > 0
        ):
            queue = queue.head(
                sample_size
            )

    return queue.reset_index(
        drop=True
    )


# ============================================================
# VALIDATION OF LABEL
# ============================================================

def validate_ground_truth_label(
    ground_truth_label,
):
    label = safe_string(
        ground_truth_label
    ).upper()

    if label not in GROUND_TRUTH_LABELS:
        raise ValueError(
            "Invalid Ground Truth label. "
            "Allowed labels: "
            + ", ".join(
                GROUND_TRUTH_LABELS
            )
        )

    return label


# ============================================================
# AUDIT HASHING
# ============================================================

def _last_audit_hash():

    ensure_ground_truth_audit_file()

    try:
        audit = pd.read_csv(
            GROUND_TRUTH_AUDIT_FILE
        )
    except Exception:
        return ""

    if (
        audit.empty
        or "event_hash" not in audit.columns
    ):
        return ""

    return safe_string(
        audit.iloc[-1][
            "event_hash"
        ]
    )


def append_ground_truth_audit(
    event_type,
    ground_truth_id="",
    reviewer_name="",
    details="",
):
    ensure_ground_truth_audit_file()

    previous_hash = _last_audit_hash()

    timestamp = datetime.now().isoformat()

    audit_id = (
        "GTA-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    payload = "|".join(
        [
            audit_id,
            timestamp,
            safe_string(event_type),
            safe_string(ground_truth_id),
            safe_string(reviewer_name),
            safe_string(details),
            previous_hash,
        ]
    )

    event_hash = hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()

    record = {
        "audit_id": audit_id,
        "timestamp": timestamp,
        "event_type": safe_string(
            event_type
        ),
        "ground_truth_id": safe_string(
            ground_truth_id
        ),
        "reviewer_name": safe_string(
            reviewer_name
        ),
        "details": safe_string(
            details
        ),
        "previous_hash": previous_hash,
        "event_hash": event_hash,
    }

    try:
        audit = pd.read_csv(
            GROUND_TRUTH_AUDIT_FILE
        )
    except Exception:
        audit = pd.DataFrame()

    audit = pd.concat(
        [
            audit,
            pd.DataFrame(
                [record]
            ),
        ],
        ignore_index=True,
    )

    audit.to_csv(
        GROUND_TRUTH_AUDIT_FILE,
        index=False,
    )

    return record


# ============================================================
# CREATE HUMAN GROUND TRUTH LABEL
# ============================================================

def create_ground_truth_label(
    row,
    reviewer_name,
    ground_truth_label,
    review_comments="",
    evidence_reference="",
    review_status="VALIDATED",
):
    """
    Save one human-reviewed Ground Truth label.

    IMPORTANT:
    The label is created only from the reviewer decision.
    The AI prediction is stored separately.
    """

    gt = load_ground_truth()

    material_a = safe_string(
        row.get(
            "material_id_a",
            "",
        )
    )

    material_b = safe_string(
        row.get(
            "material_id_b",
            "",
        )
    )

    if not material_a or not material_b:
        raise ValueError(
            "Material IDs are required."
        )

    if not safe_string(
        reviewer_name
    ):
        raise ValueError(
            "Reviewer name is required."
        )

    label = validate_ground_truth_label(
        ground_truth_label
    )

    status = safe_string(
        review_status
    ).upper()

    if status not in REVIEW_STATUSES:
        raise ValueError(
            "Invalid review status. "
            "Allowed values: "
            + ", ".join(
                REVIEW_STATUSES
            )
        )

    key = canonical_pair_key(
        material_a,
        material_b,
    )

    existing = set()

    for _, item in gt.iterrows():

        existing.add(
            canonical_pair_key(
                item[
                    "material_id_a"
                ],
                item[
                    "material_id_b"
                ],
            )
        )

    if key in existing:
        raise ValueError(
            "This material pair has already "
            "been labelled."
        )

    confidence = safe_float(
        row.get(
            "match_confidence",
            np.nan,
        )
    )

    if pd.isna(confidence):
        confidence = ""

    # --------------------------------------------------------
    # Stable sequential ID
    # --------------------------------------------------------

    existing_numbers = []

    for value in gt[
        "ground_truth_id"
    ].astype(str):

        if value.startswith(
            "GT-"
        ):
            try:
                existing_numbers.append(
                    int(
                        value.replace(
                            "GT-",
                            "",
                        )
                    )
                )
            except Exception:
                pass

    next_number = (
        max(
            existing_numbers,
            default=0,
        )
        + 1
    )

    ground_truth_id = (
        f"GT-{next_number:06d}"
    )

    # --------------------------------------------------------
    # Create record
    # --------------------------------------------------------

    record = {
        "ground_truth_id":
            ground_truth_id,

        "material_id_a":
            material_a,

        "material_id_b":
            material_b,

        "ai_prediction":
            safe_string(
                row.get(
                    "match_decision",
                    "",
                )
            ).upper(),

        "ai_confidence":
            confidence,

        "confidence_band":
            safe_string(
                row.get(
                    "confidence_band",
                    confidence_band(
                        confidence
                    ),
                )
            ).upper(),

        "candidate_rank":
            row.get(
                "candidate_rank",
                "",
            ),

        "confidence_gap":
            row.get(
                "confidence_gap",
                "",
            ),

        "technical_conflict_flag":
            row.get(
                "technical_conflict_flag",
                "",
            ),

        "technical_conflict_severity":
            safe_string(
                row.get(
                    "technical_conflict_severity",
                    "NONE",
                )
            ).upper(),

        "model_version":
            safe_string(
                row.get(
                    "model_version",
                    "",
                )
            ),

        "ground_truth_label":
            label,

        "reviewer_name":
            safe_string(
                reviewer_name
            ),

        "review_status":
            status,

        "review_date":
            datetime.now().isoformat(),

        "review_comments":
            safe_string(
                review_comments
            ),

        "evidence_reference":
            safe_string(
                evidence_reference
            ),

        "ground_truth_engine_version":
            GROUND_TRUTH_ENGINE_VERSION,
    }

    gt = pd.concat(
        [
            gt,
            pd.DataFrame(
                [record]
            ),
        ],
        ignore_index=True,
    )

    save_ground_truth(
        gt
    )

    append_ground_truth_audit(
        event_type="GROUND_TRUTH_LABEL_CREATED",
        ground_truth_id=ground_truth_id,
        reviewer_name=reviewer_name,
        details=(
            f"{material_a} <-> {material_b} | "
            f"label={label} | "
            f"status={status}"
        ),
    )

    return record


# ============================================================
# EVALUATION DATASET
# ============================================================

def build_evaluation_dataset():

    gt = load_ground_truth()

    matches = normalize_match_results(
        load_match_results()
    )

    if gt.empty or matches.empty:
        return pd.DataFrame()

    prediction_lookup = {}

    for _, row in matches.iterrows():

        key = canonical_pair_key(
            row.get(
                "material_id_a",
                "",
            ),
            row.get(
                "material_id_b",
                "",
            ),
        )

        prediction_lookup[key] = {
            "prediction":
                safe_string(
                    row.get(
                        "match_decision",
                        "",
                    )
                ).upper(),

            "confidence":
                safe_float(
                    row.get(
                        "match_confidence",
                        np.nan,
                    )
                ),

            "confidence_band":
                safe_string(
                    row.get(
                        "confidence_band",
                        "",
                    )
                ),

            "model_version":
                safe_string(
                    row.get(
                        "model_version",
                        "",
                    )
                ),
        }

    rows = []

    for _, item in gt.iterrows():

        # REVIEW_REQUIRED is a human-review state,
        # not a resolved truth class for model accuracy.
        actual = safe_string(
            item[
                "ground_truth_label"
            ]
        ).upper()

        if actual == "REVIEW_REQUIRED":
            continue

        key = canonical_pair_key(
            item[
                "material_id_a"
            ],
            item[
                "material_id_b"
            ],
        )

        prediction = prediction_lookup.get(
            key
        )

        if not prediction:
            continue

        rows.append(
            {
                "ground_truth_id":
                    item[
                        "ground_truth_id"
                    ],

                "material_id_a":
                    item[
                        "material_id_a"
                    ],

                "material_id_b":
                    item[
                        "material_id_b"
                    ],

                "actual":
                    actual,

                "prediction":
                    prediction[
                        "prediction"
                    ],

                "ai_confidence":
                    prediction[
                        "confidence"
                    ],

                "confidence_band":
                    prediction[
                        "confidence_band"
                    ],

                "model_version":
                    prediction[
                        "model_version"
                    ],

                "reviewer_name":
                    item[
                        "reviewer_name"
                    ],

                "review_date":
                    item[
                        "review_date"
                    ],
            }
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# PERFORMANCE METRICS
# ============================================================

def calculate_metrics():

    evaluation = (
        build_evaluation_dataset()
    )

    if evaluation.empty:

        return {
            "sample_size": 0,
            "accuracy": np.nan,
            "precision": np.nan,
            "recall": np.nan,
            "f1": np.nan,
            "true_positive": 0,
            "false_positive": 0,
            "false_negative": 0,
            "confusion_matrix":
                pd.DataFrame(),
        }

    actual = (
        evaluation[
            "actual"
        ]
    )

    prediction = (
        evaluation[
            "prediction"
        ]
    )

    accuracy = (
        actual == prediction
    ).mean()

    # --------------------------------------------------------
    # Binary MATCH metrics
    # --------------------------------------------------------

    actual_match = (
        actual == "MATCH"
    )

    predicted_match = (
        prediction == "MATCH"
    )

    true_positive = int(
        (
            actual_match
            & predicted_match
        ).sum()
    )

    false_positive = int(
        (
            ~actual_match
            & predicted_match
        ).sum()
    )

    false_negative = int(
        (
            actual_match
            & ~predicted_match
        ).sum()
    )

    precision = (
        true_positive
        /
        (
            true_positive
            + false_positive
        )
        if (
            true_positive
            + false_positive
        )
        else 0
    )

    recall = (
        true_positive
        /
        (
            true_positive
            + false_negative
        )
        if (
            true_positive
            + false_negative
        )
        else 0
    )

    f1 = (
        2
        * precision
        * recall
        /
        (
            precision
            + recall
        )
        if (
            precision
            + recall
        )
        else 0
    )

    labels = [
        "MATCH",
        "NO_MATCH",
        "REVIEW",
    ]

    confusion = pd.crosstab(
        actual,
        prediction,
        rownames=[
            "Ground Truth"
        ],
        colnames=[
            "AI Prediction"
        ],
    )

    confusion = confusion.reindex(
        index=labels,
        columns=labels,
        fill_value=0,
    )

    return {
        "sample_size":
            len(evaluation),

        "accuracy":
            accuracy,

        "precision":
            precision,

        "recall":
            recall,

        "f1":
            f1,

        "true_positive":
            true_positive,

        "false_positive":
            false_positive,

        "false_negative":
            false_negative,

        "confusion_matrix":
            confusion,
    }


# ============================================================
# CONFIDENCE VS ACTUAL PERFORMANCE
# ============================================================

def confidence_performance():

    evaluation = (
        build_evaluation_dataset()
    )

    if evaluation.empty:
        return pd.DataFrame()

    evaluation = evaluation.copy()

    evaluation[
        "correct"
    ] = (
        evaluation[
            "actual"
        ]
        ==
        evaluation[
            "prediction"
        ]
    )

    grouped = (
        evaluation
        .groupby(
            "confidence_band",
            dropna=False,
        )
        .agg(
            Samples=(
                "correct",
                "size",
            ),
            Correct=(
                "correct",
                "sum",
            ),
            Actual_Accuracy=(
                "correct",
                "mean",
            ),
        )
        .reset_index()
    )

    grouped[
        "Actual_Accuracy"
    ] = (
        grouped[
            "Actual_Accuracy"
        ]
        * 100
    )

    return grouped


# ============================================================
# MODEL EVALUATION BY VERSION
# ============================================================

def model_version_performance():

    evaluation = (
        build_evaluation_dataset()
    )

    if evaluation.empty:
        return pd.DataFrame()

    evaluation = evaluation.copy()

    evaluation[
        "correct"
    ] = (
        evaluation[
            "actual"
        ]
        ==
        evaluation[
            "prediction"
        ]
    )

    result = (
        evaluation
        .groupby(
            "model_version",
            dropna=False,
        )
        .agg(
            Samples=(
                "correct",
                "size",
            ),
            Correct=(
                "correct",
                "sum",
            ),
            Accuracy=(
                "correct",
                "mean",
            ),
        )
        .reset_index()
    )

    result[
        "Accuracy"
    ] *= 100

    return result


# ============================================================
# REVIEWER STATISTICS
# ============================================================

def reviewer_statistics():

    gt = load_ground_truth()

    if gt.empty:
        return pd.DataFrame()

    result = (
        gt
        .groupby(
            "reviewer_name",
            dropna=False,
        )
        .agg(
            Labels=(
                "ground_truth_id",
                "count",
            ),

            Identical_Labels=(
                "ground_truth_label",
                lambda x:
                    int(
                        (
                            x
                            .astype(str)
                            .str.upper()
                            ==
                            "IDENTICAL"
                        ).sum()
                    ),
            ),

            Duplicate_Labels=(
                "ground_truth_label",
                lambda x:
                    int(
                        (
                            x
                            .astype(str)
                            .str.upper()
                            ==
                            "DUPLICATE"
                        ).sum()
                    ),
            ),

            Near_Duplicate_Labels=(
                "ground_truth_label",
                lambda x:
                    int(
                        (
                            x
                            .astype(str)
                            .str.upper()
                            ==
                            "NEAR_DUPLICATE"
                        ).sum()
                    ),
            ),

            Functional_Equivalent_Labels=(
                "ground_truth_label",
                lambda x:
                    int(
                        (
                            x
                            .astype(str)
                            .str.upper()
                            ==
                            "FUNCTIONALLY_EQUIVALENT"
                        ).sum()
                    ),
            ),

            No_Match_Labels=(
                "ground_truth_label",
                lambda x:
                    int(
                        (
                            x
                            .astype(str)
                            .str.upper()
                            ==
                            "NO_MATCH"
                        ).sum()
                    ),
            ),

            Review_Required_Labels=(
                "ground_truth_label",
                lambda x:
                    int(
                        (
                            x
                            .astype(str)
                            .str.upper()
                            ==
                            "REVIEW_REQUIRED"
                        ).sum()
                    ),
            ),
        )
        .reset_index()
    )

    return result


# ============================================================
# GROUND TRUTH SUMMARY
# ============================================================

def ground_truth_summary():

    gt = load_ground_truth()

    if gt.empty:

        return {
            "total_labels": 0,
            "validated_labels": 0,
            "adjudication_required": 0,
            "label_distribution":
                pd.DataFrame(),
        }

    validated = (
        gt[
            "review_status"
        ]
        .astype(str)
        .str.upper()
        ==
        "VALIDATED"
    ).sum()

    adjudication = (
        gt[
            "review_status"
        ]
        .astype(str)
        .str.upper()
        ==
        "ADJUDICATION_REQUIRED"
    ).sum()

    distribution = (
        gt[
            "ground_truth_label"
        ]
        .astype(str)
        .str.upper()
        .value_counts()
        .rename_axis(
            "Ground_Truth_Label"
        )
        .reset_index(
            name="Count"
        )
    )

    return {
        "total_labels":
            len(gt),

        "validated_labels":
            int(validated),

        "adjudication_required":
            int(adjudication),

        "label_distribution":
            distribution,
    }


# ============================================================
# INITIALIZATION
# ============================================================

ensure_ground_truth_file()
ensure_ground_truth_audit_file()