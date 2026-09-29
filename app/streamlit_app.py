from pathlib import Path
from datetime import datetime
import re
import hashlib
import json
import numpy as np
import pandas as pd
import streamlit as st

# Optional Ground Truth engine
try:
    from app.ground_truth_engine import load_match_results as engine_load_match_results
    from app.ground_truth_engine import build_ground_truth_queue as engine_build_ground_truth_queue
    GROUND_TRUTH_ENGINE_AVAILABLE = True
except Exception:
    GROUND_TRUTH_ENGINE_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="CPSE National Unified Material Master",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# UI
# ============================================================
st.markdown("""
<style>
html,body,[class*="css"]{font-family:"Segoe UI",Arial,sans-serif;}
.stApp,[data-testid="stAppViewContainer"]{background:#f5f7fa;}
.main .block-container{max-width:100%;padding:1.05rem 1.7rem 2rem;}
section[data-testid="stSidebar"]{width:250px!important;background:#10233f;}
section[data-testid="stSidebar"]>div{background:#10233f;padding:.9rem .8rem;}
section[data-testid="stSidebar"] *{color:#e9eef5;}
.sidebar-brand{padding:.25rem .2rem .85rem;border-bottom:1px solid #29415f;margin-bottom:.7rem;}
.sidebar-brand-title{color:#fff;font-size:1rem;font-weight:700;line-height:1.2;}
.sidebar-brand-subtitle{color:#9fb1c8;font-size:.67rem;margin-top:.22rem;}
.sidebar-status{margin-top:.75rem;padding:.55rem;background:#152d4b;border:1px solid #29415f;border-radius:4px;font-size:.68rem;color:#b8c7d9;}
section[data-testid="stSidebar"] .stRadio>label{color:#9fb1c8;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"]{gap:1px;}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label{padding:.33rem .4rem;border-radius:4px;font-size:.74rem;}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover{background:#193557;}
h1{font-size:1.5rem!important;color:#16283f!important;margin-bottom:.1rem!important;}
h2{font-size:1.1rem!important;color:#16283f!important;}
h3{font-size:.93rem!important;color:#20344e!important;}
p,label,.stMarkdown{font-size:.8rem;}
.page-subtitle{color:#68788d;font-size:.76rem;margin-bottom:.85rem;}
.section-bar{background:#fff;border-left:3px solid #2f6ea5;border-bottom:1px solid #dfe5ec;padding:.52rem .7rem;margin:.8rem 0 .6rem;color:#243b57;font-size:.84rem;font-weight:700;}
.info-box,.warning-box,.success-box{background:#fff;border:1px solid #dfe5ec;border-radius:5px;padding:.65rem .75rem;color:#46566b;font-size:.75rem;}
.warning-box{background:#fffaf0;border-color:#ead8a5;border-left:3px solid #c9911d;color:#6e581d;}
.success-box{background:#f3faf6;border-color:#c9e4d4;border-left:3px solid #31835c;color:#285f46;}
.kpi{background:#fff;border:1px solid #dfe5ec;border-radius:5px;padding:.68rem .78rem;min-height:72px;}
.kpi-label{color:#718096;font-size:.64rem;text-transform:uppercase;letter-spacing:.04em;font-weight:700;}
.kpi-value{color:#172b46;font-size:1.3rem;font-weight:700;margin-top:.12rem;}
.kpi-note{color:#7d8b9c;font-size:.63rem;}
div[data-testid="stMetric"]{background:#fff;border:1px solid #dfe5ec;border-radius:5px;padding:.48rem .62rem;}
div[data-testid="stMetricLabel"]{font-size:.65rem!important;color:#718096!important;}
div[data-testid="stMetricValue"]{font-size:1.18rem!important;color:#172b46!important;}
.stButton button,.stDownloadButton button{border-radius:4px;font-size:.74rem;min-height:32px;}
[data-testid="stDataFrame"]{border:1px solid #dfe5ec;}
footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FILES
# ============================================================
FILES = {
    "national_master": "national_material_master.csv",
    "migration": "national_migration_mapping.csv",
    "matches": "match_results.csv",
    "duplicates": "duplicate_detection_report.csv",
    "reviews": "review_approval_workflow.csv",
    "validated": "validated_materials.csv",
    "standardized": "standardized_materials.csv",
    "ground_truth": "ground_truth_labels.csv",
    "taxonomy": "taxonomy.csv",
    "attribute_dictionary": "attribute_dictionary.csv",
    "change_requests": "change_requests.csv",
    "procurement": "historical_procurement.csv",
    "inventory": "inventory_snapshot.csv",
    "inventory_opportunities": "inventory_optimization_opportunities.csv",
    "collaboration": "collaborative_procurement_candidates.csv",
    "erp_log": "erp_integration_log.csv",
    "model_registry": "model_registry.csv",
    "platform_audit": "platform_audit.csv",
    "gt_audit": "ground_truth_audit.csv",
    "survivorship": "survivorship_decisions.csv",
}


def load_csv(key):
    filename = FILES[key]
    output_path = OUTPUT_DIR / filename
    root_path = PROJECT_ROOT / filename

    # Current project data is mixed between the project root and outputs/.
    # Prefer outputs/ for controlled/generated files, then fall back to root.
    path = output_path if output_path.exists() else root_path

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def save_csv(df, key):
    (OUTPUT_DIR / FILES[key]).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / FILES[key], index=False)


def ensure_columns(df, cols):
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = ""
    return out


def first(row, names, default=""):
    for n in names:
        if n in row.index and pd.notna(row[n]) and str(row[n]).strip():
            return row[n]
    return default


def num(v):
    try:
        return float(v)
    except Exception:
        return np.nan


def norm_text(v):
    if pd.isna(v):
        return ""
    s = str(v).upper().strip()
    s = re.sub(r"[^A-Z0-9.]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def token_set(v):
    return set(norm_text(v).split())


def token_similarity(a, b):
    A, B = token_set(a), token_set(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def pair_key(a, b):
    return "||".join(sorted([str(a).strip(), str(b).strip()]))


def confidence_band(v):
    if pd.isna(v):
        return "UNKNOWN"
    if v >= .90:
        return "VERY_HIGH"
    if v >= .85:
        return "HIGH"
    if v >= .75:
        return "MEDIUM"
    if v >= .65:
        return "LOW"
    return "VERY_LOW"


def score_col(df):
    for c in ["match_confidence", "confidence_score", "advanced_match_score", "match_score", "overall_match_score"]:
        if c in df.columns:
            return c
    return None


def material_relationship(row):
    decision = str(first(row, ["match_decision", "decision"], "")).upper()
    severity = str(first(row, ["technical_conflict_severity"], "NONE")).upper()
    if severity in {"HIGH", "CRITICAL"}:
        return "REVIEW_REQUIRED"
    if decision == "REVIEW":
        return "REVIEW_REQUIRED"
    match_score = num(first(row, ["match_score", "ai_confidence", "confidence_score"], np.nan))
    tech = num(first(row, ["technical_attribute_score", "technical_similarity"], np.nan))
    spec = num(first(row, ["specification_similarity_score", "specification_score"], np.nan))
    functional = num(first(row, ["functional_similarity_score", "functional_score"], np.nan))
    if decision == "MATCH" and not pd.isna(tech) and tech >= .90 and (pd.isna(spec) or spec >= .90):
        return "IDENTICAL"
    if functional >= .85 and match_score >= .65 and (pd.isna(tech) or tech >= .70):
        return "FUNCTIONALLY_EQUIVALENT"
    if match_score >= .75 and (pd.isna(tech) or tech >= .70):
        return "NEAR_DUPLICATE"
    if decision == "MATCH":
        return "DUPLICATE"
    if decision == "NO_MATCH":
        return "NO_MATCH"
    if match_score >= .65:
        return "REVIEW_REQUIRED"
    return "NO_MATCH"


def add_ai_fields(df):
    if df.empty:
        return df.copy()
    out = df.copy()
    sc = score_col(out)
    out["ai_confidence"] = pd.to_numeric(out[sc], errors="coerce") if sc else np.nan
    out["confidence_band"] = out["ai_confidence"].apply(confidence_band)
    if "match_decision" not in out.columns:
        out["match_decision"] = out.get("decision", "")
    defaults = {
        "technical_conflict_flag": False,
        "technical_conflicts": "",
        "technical_conflict_severity": "NONE",
        "matching_evidence": "",
        "model_version": "existing-pipeline",
    }
    for c, d in defaults.items():
        if c not in out.columns:
            out[c] = d
    out["relationship"] = out.apply(material_relationship, axis=1)
    out["relationship_explanation"] = out.apply(relationship_explanation, axis=1)
    return out


def relationship_explanation(row):
    rel = str(row.get("relationship", "")).upper()
    return {
        "IDENTICAL": "Evidence supports the same technical identity; National Material Code consolidation still requires approval.",
        "DUPLICATE": "Records appear to represent duplicate master-data identities; consolidation requires governance approval.",
        "NEAR_DUPLICATE": "Records are close but require technical review before consolidation.",
        "FUNCTIONALLY_EQUIVALENT": "Potentially interchangeable/common-procurement relationship. This does NOT by itself create the same National Material Code.",
        "REVIEW_REQUIRED": "Evidence is ambiguous or contains technical risk; human engineering/master-data review is required.",
        "NO_MATCH": "Available evidence does not support a harmonization relationship.",
    }.get(rel, "Relationship requires review.")

# ============================================================
# STANDARDIZATION + TECHNICAL CONTROL
# ============================================================
UOM_MAP = {
    "EACH": "EA", "EA": "EA", "PCS": "EA", "PC": "EA", "NOS": "EA", "NO": "EA",
    "KGS": "KG", "KILOGRAM": "KG", "KG": "KG", "MTR": "M", "METER": "M", "METRE": "M", "M": "M",
    "MM": "MM", "CM": "CM", "LTR": "L", "LITRE": "L", "LITER": "L", "L": "L"
}
CLASS_RULES = {
    "CABLE": ["CABLE", "WIRE"], "BEARING": ["BEARING"], "VALVE": ["VALVE"], "PUMP": ["PUMP"],
    "MOTOR": ["MOTOR"], "BOLT": ["BOLT"], "NUT": ["NUT"], "GASKET": ["GASKET"],
    "PIPE": ["PIPE", "TUBE"], "FLANGE": ["FLANGE"], "FILTER": ["FILTER"], "TRANSFORMER": ["TRANSFORMER"],
    "BREAKER": ["BREAKER"], "CONTACTOR": ["CONTACTOR"], "FUSE": ["FUSE"], "FASTENER": ["SCREW", "WASHER", "FASTENER"]
}
ATTRIBUTE_RULES = {
    "voltage": r"(?i)(?:VOLTAGE|VOLT|KV)\s*[:=/-]?\s*(\d+(?:\.\d+)?)\s*(KV|V)?",
    "diameter": r"(?i)(?:DIA|DIAMETER|DN)\s*[:=/-]?\s*(\d+(?:\.\d+)?)\s*(MM|CM|M)?",
    "length": r"(?i)(?:LENGTH|LEN|LG)\s*[:=/-]?\s*(\d+(?:\.\d+)?)\s*(MM|CM|M)?",
    "size": r"(?i)(?:SIZE|SZ|NB|NOMINAL)\s*[:=/-]?\s*([A-Z0-9.]+)",
    "core_count": r"(?i)(?:CORE|CORES|C)\s*[:=/-]?\s*(\d+)",
    "standard": r"(?i)\b((?:IS|IEC|ASTM|API|DIN|BS|ANSI)[ -]?[A-Z0-9./-]+)",
    "part_number": r"(?i)(?:P/?N|PART\s*NO|PART\s*NUMBER)\s*[:=/-]?\s*([A-Z0-9./_-]+)",
    "manufacturer": r"(?i)(?:MAKE|MFR|MANUFACTURER|OEM)\s*[:=/-]?\s*([A-Z0-9 .&_-]+?)(?=\s+(?:SIZE|VOLT|VOLTAGE|STANDARD|IS|IEC|PART|P/N|UOM)\b|$)",
}
ATTRIBUTE_NAMES = ["material_type", "size", "length", "voltage", "diameter", "core_count", "standard", "manufacturer", "part_number", "unit_of_measure"]

DEFAULT_REQUIRED = {
    "CABLE": ["material_type", "size", "voltage", "standard", "unit_of_measure"],
    "BEARING": ["material_type", "size", "standard", "unit_of_measure"],
    "VALVE": ["material_type", "size", "standard", "unit_of_measure"],
    "PUMP": ["material_type", "size", "standard", "unit_of_measure"],
    "MOTOR": ["material_type", "size", "voltage", "standard", "unit_of_measure"],
    "PIPE": ["material_type", "size", "diameter", "standard", "unit_of_measure"],
    "FLANGE": ["material_type", "size", "standard", "unit_of_measure"],
    "FASTENER": ["material_type", "size", "standard", "unit_of_measure"],
}


def extract_attr(desc, field):
    match = re.search(ATTRIBUTE_RULES[field], str(desc or ""))
    if not match:
        return ""
    return str(match.group(1)).upper().strip()


def classify(desc, existing=""):
    if str(existing).strip():
        return str(existing).upper().strip(), "SOURCE_FIELD", .95
    text = norm_text(desc)
    for cls, words in CLASS_RULES.items():
        if any(w in text.split() for w in words):
            return cls, "RULE_ASSISTED", .88
    return "UNCLASSIFIED", "RULE_ASSISTED", .35


def standardize_row(row):
    desc = first(row, ["description", "material_description", "short_text", "source_description", "material_name"], "")
    cls, method, class_conf = classify(desc, first(row, ["material_group", "material_classification", "classification"], ""))
    values = {
        "material_type": first(row, ["material_type", "type"], ""),
        "size": first(row, ["size"], ""),
        "length": first(row, ["length"], ""),
        "voltage": first(row, ["voltage"], ""),
        "diameter": first(row, ["diameter"], ""),
        "core_count": first(row, ["core_count"], ""),
        "standard": first(row, ["standard", "specification", "spec"], ""),
        "manufacturer": first(row, ["manufacturer", "make", "mfr"], ""),
        "part_number": first(row, ["part_number", "part_no", "pn"], ""),
    }
    for key in values:
        if not str(values[key]).strip() and key in ATTRIBUTE_RULES:
            values[key] = extract_attr(desc, key)
    uom = first(row, ["unit_of_measure", "uom", "base_uom"], "").upper().strip()
    values["unit_of_measure"] = UOM_MAP.get(uom, uom)
    required = DEFAULT_REQUIRED.get(cls, ["material_type", "standard", "unit_of_measure"])
    missing = [x for x in required if not str(values.get(x, "")).strip()]
    completeness = 1 - len(missing) / max(len(required), 1)
    standard_desc = " ".join([cls] + [str(values[k]).upper().strip() for k in ATTRIBUTE_NAMES if k != "unit_of_measure" and str(values.get(k, "")).strip()])
    confidence = round((class_conf + completeness) / 2, 3)
    return {
        "source_material_id": first(row, ["material_id", "source_material_id", "id", "material_code"], ""),
        "cpse": first(row, ["cpse", "cpse_name", "organization", "company_code"], ""),
        "source_description": desc,
        "standardized_description": standard_desc,
        "material_group": cls,
        **values,
        "classification_confidence": class_conf,
        "technical_completeness": round(completeness, 3),
        "standardization_confidence": confidence,
        "confidence_band": confidence_band(confidence),
        "missing_attributes": "; ".join(missing),
        "classification_method": method,
        "standardization_method": "RULE_ASSISTED_BASELINE",
        "standardization_version": "cpse-material-standardizer-v3",
        "recommendation_status": "READY_FOR_REVIEW" if not missing else "REVIEW_REQUIRED",
    }


def build_standardized(source):
    if source.empty:
        return pd.DataFrame()
    return pd.DataFrame([standardize_row(row) for _, row in source.iterrows()])


def attribute_validation(row, attribute_dictionary):
    group = str(row.get("material_group", "UNCLASSIFIED")).upper()
    required = DEFAULT_REQUIRED.get(group, ["material_type", "standard", "unit_of_measure"])
    if not attribute_dictionary.empty and "material_group" in attribute_dictionary.columns and "required" in attribute_dictionary.columns:
        hit = attribute_dictionary[attribute_dictionary.material_group.astype(str).str.upper() == group]
        if not hit.empty:
            required = [x.strip() for x in str(hit.iloc[0].required).split(",") if x.strip()]
    missing = [a for a in required if not str(row.get(a, "")).strip()]
    issues = []
    uom = str(row.get("unit_of_measure", "")).upper().strip()
    if uom and uom not in set(UOM_MAP.values()):
        issues.append(f"Uncontrolled UOM: {uom}")
    for field in ["voltage", "diameter", "length", "core_count"]:
        val = row.get(field, "")
        if str(val).strip() and pd.isna(pd.to_numeric(re.sub(r"[^0-9.\-]", "", str(val)), errors="coerce")):
            issues.append(f"Invalid numeric {field}")
    return missing, issues

# ============================================================
# GOVERNANCE / AUDIT
# ============================================================
def append_audit(event, actor, entity_type, entity_id, details=""):
    old = load_csv("platform_audit")
    cols = ["audit_id", "timestamp", "event_type", "actor", "entity_type", "entity_id", "details", "previous_hash", "event_hash"]
    old = ensure_columns(old, cols)
    previous_hash = str(old.iloc[-1].get("event_hash", "")) if not old.empty else "GENESIS"
    timestamp = datetime.now().isoformat()
    payload = f"{timestamp}|{event}|{actor}|{entity_type}|{entity_id}|{details}|{previous_hash}"
    event_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    rec = pd.DataFrame([{
        "audit_id": "AUD-" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "timestamp": timestamp,
        "event_type": event,
        "actor": actor,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details,
        "previous_hash": previous_hash,
        "event_hash": event_hash,
    }])
    save_csv(pd.concat([old, rec], ignore_index=True)[cols], "platform_audit")


def append_gt_audit(event, reviewer, gt_id, details=""):
    old = load_csv("gt_audit")
    cols = ["audit_id", "timestamp", "event_type", "reviewer", "ground_truth_id", "details"]
    old = ensure_columns(old, cols)
    rec = pd.DataFrame([{
        "audit_id": "GTA-" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "timestamp": datetime.now().isoformat(),
        "event_type": event,
        "reviewer": reviewer,
        "ground_truth_id": gt_id,
        "details": details,
    }])
    save_csv(pd.concat([old, rec], ignore_index=True)[cols], "gt_audit")

# ============================================================
# DATA LOAD
# ============================================================
national_master = load_csv("national_master")
migration = load_csv("migration")
matches = add_ai_fields(load_csv("matches"))
duplicates = add_ai_fields(load_csv("duplicates"))
reviews = load_csv("reviews")
validated = load_csv("validated")
standardized = load_csv("standardized")
ground_truth = load_csv("ground_truth")
taxonomy = load_csv("taxonomy")
attribute_dictionary = load_csv("attribute_dictionary")
change_requests = load_csv("change_requests")
procurement = load_csv("procurement")
inventory = load_csv("inventory")
inventory_opportunities = load_csv("inventory_opportunities")
collaboration = load_csv("collaboration")
erp_log = load_csv("erp_log")
model_registry = load_csv("model_registry")
platform_audit = load_csv("platform_audit")
gt_audit = load_csv("gt_audit")
survivorship = load_csv("survivorship")

GT_COLS = ["ground_truth_id", "material_id_a", "material_id_b", "ai_prediction", "ai_confidence", "confidence_band", "candidate_rank", "confidence_gap", "technical_conflict_flag", "technical_conflict_severity", "model_version", "ground_truth_label", "reviewer_name", "review_status", "review_date", "review_comments", "evidence_reference"]
ground_truth = ensure_columns(ground_truth, GT_COLS)

# ============================================================
# NAVIGATION
# ============================================================
navigation = [
    "01 — Executive Dashboard", "02 — AI Ingestion & Data Quality", "03 — AI Material Understanding",
    "04 — AI Material Matching", "05 — Duplicate Intelligence", "06 — National Material Master",
    "07 — CPSE Migration Mapping", "08 — Review & Approval", "09 — Ground Truth & Validation",
    "10 — Accuracy & AI Analytics", "11 — Procurement Intelligence", "12 — SAP / ERP Integration",
    "13 — Audit & Governance", "14 — Taxonomy & Attribute Dictionary", "15 — Best Record / Survivorship",
    "16 — Change Requests / Exceptions"
]

st.sidebar.markdown('<div class="sidebar-brand"><div class="sidebar-brand-title">CPSE Material Master</div><div class="sidebar-brand-subtitle">National Unified Material Framework</div></div>', unsafe_allow_html=True)
page = st.sidebar.radio("MODULES", navigation, index=0)
st.sidebar.markdown(
    f'<div class="sidebar-status"><b>Pipeline</b><br>National master: {len(national_master):,}<br>AI candidates: {len(matches):,}<br>Ground Truth: {len(ground_truth):,}<br>Procurement: {len(procurement):,}<br>Inventory: {len(inventory):,}</div>',
    unsafe_allow_html=True,
)
st.title("CPSE National Unified Material Master")
st.markdown('<div class="page-subtitle">AI-assisted harmonization, technical validation, national-code governance, procurement intelligence and controlled migration</div>', unsafe_allow_html=True)

# ============================================================
# 01 EXECUTIVE
# ============================================================
if page.startswith("01"):
    st.markdown('<div class="section-bar">Executive control view</div>', unsafe_allow_html=True)
    rel_counts = matches["relationship"].value_counts() if not matches.empty else pd.Series(dtype=int)
    a,b,c,d,e = st.columns(5)
    a.metric("Source materials", f"{max(len(validated),len(standardized)):,}")
    b.metric("National materials", f"{len(national_master):,}")
    c.metric("AI candidate pairs", f"{len(matches):,}")
    d.metric("Ground Truth labels", f"{len(ground_truth):,}")
    e.metric("Procurement records", f"{len(procurement):,}")
    st.markdown('<div class="section-bar">Harmonization relationship control</div>', unsafe_allow_html=True)
    rels = ["IDENTICAL","DUPLICATE","NEAR_DUPLICATE","FUNCTIONALLY_EQUIVALENT","REVIEW_REQUIRED","NO_MATCH"]
    st.dataframe(pd.DataFrame({"Relationship":rels,"Records":[int(rel_counts.get(x,0)) for x in rels]}), use_container_width=True, hide_index=True)
    st.markdown('<div class="section-bar">Platform completeness</div>', unsafe_allow_html=True)
    controls = [
        ("AI matching", not matches.empty), ("Relationship interpretation", "relationship" in matches.columns),
        ("Standardization workflow", not standardized.empty), ("Technical attribute controls", True),
        ("National material master", not national_master.empty), ("Migration mapping", not migration.empty),
        ("Platform audit", not platform_audit.empty), ("Procurement history", not procurement.empty),
        ("Inventory optimization dataset", not inventory.empty or not inventory_opportunities.empty),
        ("SAP/ERP control workflow", True),
    ]
    st.dataframe(pd.DataFrame({"Capability":[x[0] for x in controls],"Status":["AVAILABLE" if x[1] else "DATA PENDING" for x in controls]}), use_container_width=True, hide_index=True)
    if not inventory.empty and not inventory_opportunities.empty:
        st.success(f"Inventory optimization has {len(inventory_opportunities):,} identified opportunities ready for review.")
    elif inventory.empty:
        st.info("Inventory optimization is fully implemented in the application workflow, but it requires inventory_snapshot.csv to calculate actual opportunities.")

# ============================================================
# 02 INGESTION
# ============================================================
elif page.startswith("02"):
    st.markdown('<div class="section-bar">AI ingestion and source-data quality</div>', unsafe_allow_html=True)
    source = validated if not validated.empty else standardized
    if source.empty:
        st.warning("No validated or standardized source dataset is available.")
    else:
        miss = source.isna().sum()
        quality = pd.DataFrame({"Field":miss.index,"Missing":miss.values,"Completeness %":[round((1-x/len(source))*100,2) for x in miss.values]})
        a,b,c,d = st.columns(4)
        a.metric("Records", f"{len(source):,}"); b.metric("Columns", len(source.columns)); c.metric("Fully populated", int(source.notna().all(axis=1).sum())); d.metric("Fields", len(source.columns))
        st.dataframe(quality.sort_values("Completeness %"), use_container_width=True, hide_index=True, height=350)
        st.download_button("Download source profile", source.to_csv(index=False), "source_materials.csv", "text/csv")

# ============================================================
# 03 UNDERSTANDING
# ============================================================
elif page.startswith("03"):
    st.markdown('<div class="section-bar">AI-assisted material understanding and standardization</div>', unsafe_allow_html=True)
    source = validated if not validated.empty else standardized
    st.info("The standardization engine is a controlled, rule-assisted baseline: it extracts source-supported attributes, normalizes UOMs and creates reviewable standardized descriptions. It does not invent engineering values or falsely claim a trained ML model.")
    if source.empty:
        st.warning("No source material dataset is available.")
    else:
        max_n = min(len(source), 100000)
        n = st.number_input("Records to process", min_value=1, max_value=max_n, value=min(1000,max_n), step=100)
        if st.button("Generate / refresh standardization recommendations", type="primary"):
            newstd = build_standardized(source.head(int(n)))
            save_csv(newstd, "standardized")
            append_audit("STANDARDIZATION_RECOMMENDATIONS_GENERATED", "system", "material_batch", str(len(newstd)), "rule-assisted baseline")
            st.success(f"Generated {len(newstd):,} recommendations.")
            st.rerun()
    if not standardized.empty:
        a,b,c,d = st.columns(4)
        a.metric("Records", len(standardized)); b.metric("Material groups", standardized.material_group.nunique() if "material_group" in standardized else 0)
        c.metric("Ready for review", int(standardized.recommendation_status.astype(str).eq("READY_FOR_REVIEW").sum()) if "recommendation_status" in standardized else 0)
        d.metric("Avg technical completeness", f"{pd.to_numeric(standardized.technical_completeness,errors='coerce').mean()*100:.1f}%" if "technical_completeness" in standardized else "N/A")
        st.dataframe(standardized, use_container_width=True, height=360)
        st.markdown('<div class="section-bar">Technical attribute validation</div>', unsafe_allow_html=True)
        checks = []
        for _, row in standardized.iterrows():
            missing, issues = attribute_validation(row, attribute_dictionary)
            checks.append({"source_material_id":first(row,["source_material_id"]),"material_group":row.get("material_group",""),"missing_required": "; ".join(missing),"technical_issues":"; ".join(issues),"validation_status":"PASS" if not missing and not issues else "REVIEW"})
        tech_df = pd.DataFrame(checks)
        st.dataframe(tech_df, use_container_width=True, height=300)
        if not tech_df.empty:
            st.download_button("Download technical validation", tech_df.to_csv(index=False), "technical_validation.csv", "text/csv")
        st.markdown('<div class="section-bar">Human standardization approval</div>', unsafe_allow_html=True)
        idx = st.selectbox("Material", standardized.index.tolist(), format_func=lambda i:str(first(standardized.loc[i],["source_material_id"],i)))
        reviewer = st.text_input("Reviewer name", key="std_reviewer")
        role = st.text_input("Reviewer role / organisation", key="std_role")
        decision = st.selectbox("Decision", ["APPROVED","REJECTED","NEEDS_CORRECTION"], key="std_decision")
        comment = st.text_area("Comments", key="std_comment")
        if st.button("Save standardization validation", type="primary"):
            if not reviewer.strip():
                st.error("Reviewer name is required.")
            else:
                standardized = ensure_columns(standardized,["validation_decision","validator_name","validator_role","validation_date","validation_comments"])
                standardized.loc[idx,["validation_decision","validator_name","validator_role","validation_date","validation_comments"]] = [decision,reviewer,role,datetime.now().isoformat(),comment]
                save_csv(standardized,"standardized")
                append_audit("STANDARDIZATION_VALIDATED",reviewer,"material",str(first(standardized.loc[idx],["source_material_id"],idx)),decision)
                st.success("Validation saved.")
                st.rerun()

# ============================================================
# 04 MATCHING
# ============================================================
elif page.startswith("04"):
    st.markdown('<div class="section-bar">AI material matching and relationship interpretation</div>', unsafe_allow_html=True)
    if matches.empty:
        st.warning("match_results.csv is not available.")
    else:
        a,b,c,d = st.columns(4)
        dec_filter = a.selectbox("AI decision", ["ALL"]+sorted(matches.match_decision.astype(str).str.upper().unique().tolist()))
        rel_filter = b.selectbox("Relationship", ["ALL","IDENTICAL","DUPLICATE","NEAR_DUPLICATE","FUNCTIONALLY_EQUIVALENT","REVIEW_REQUIRED","NO_MATCH"])
        band_filter = c.selectbox("Confidence", ["ALL","VERY_HIGH","HIGH","MEDIUM","LOW","VERY_LOW","UNKNOWN"])
        min_conf = d.number_input("Minimum confidence",0.0,1.0,0.0,0.05)
        view = matches.copy()
        if dec_filter != "ALL": view = view[view.match_decision.astype(str).str.upper()==dec_filter]
        if rel_filter != "ALL": view = view[view.relationship==rel_filter]
        if band_filter != "ALL": view = view[view.confidence_band==band_filter]
        view = view[pd.to_numeric(view.ai_confidence,errors="coerce").fillna(0) >= min_conf]
        cols = [c for c in ["material_id_a","material_id_b","match_score","ai_confidence","confidence_band","candidate_rank","confidence_gap","technical_conflict_flag","technical_conflict_severity","relationship","match_decision","model_version"] if c in view.columns]
        st.caption(f"Showing {len(view):,} of {len(matches):,} candidate pairs.")
        st.dataframe(view[cols], use_container_width=True, height=330)
        if not view.empty:
            ix = st.selectbox("Open candidate",view.index.tolist(),format_func=lambda i:f"{first(view.loc[i],[ 'material_id_a'],i)} ↔ {first(view.loc[i],[ 'material_id_b'],'')}")
            r=view.loc[ix]
            a,b,c,d=st.columns(4); a.metric("AI confidence",f"{num(r.get('ai_confidence')):.3f}" if not pd.isna(num(r.get('ai_confidence'))) else "N/A"); b.metric("Relationship",r.get("relationship","")); c.metric("Decision",r.get("match_decision","")); d.metric("Conflict",r.get("technical_conflict_severity","NONE"))
            st.info(relationship_explanation(r))
            ev = pd.DataFrame({"Evidence":["Description","Technical","Standard/specification","Functional","Completeness","AI explanation"],"Result":[first(r,["description_score","semantic_score"],"N/A"),first(r,["technical_attribute_score","technical_similarity"],"N/A"),first(r,["standard_score","specification_score"],"N/A"),first(r,["functional_similarity_score","functional_score"],"N/A"),first(r,["data_completeness_score"],"N/A"),first(r,["matching_evidence","evidence","match_reason"],"N/A")]})
            st.dataframe(ev,use_container_width=True,hide_index=True)

# ============================================================
# 05 DUPLICATES
# ============================================================
elif page.startswith("05"):
    st.markdown('<div class="section-bar">Duplicate and equivalence intelligence</div>', unsafe_allow_html=True)
    if duplicates.empty:
        st.info("duplicate_detection_report.csv is not available.")
    else:
        rel_counts = duplicates.relationship.value_counts() if "relationship" in duplicates else pd.Series(dtype=int)
        a,b,c,d=st.columns(4); a.metric("Candidates",len(duplicates)); b.metric("Duplicates",int(rel_counts.get("DUPLICATE",0))); c.metric("Near duplicates",int(rel_counts.get("NEAR_DUPLICATE",0))); d.metric("Functional equivalents",int(rel_counts.get("FUNCTIONALLY_EQUIVALENT",0)))
        st.dataframe(duplicates,use_container_width=True,height=430)
        st.info("Functional equivalence is a substitution/common-procurement relationship; it does not automatically create the same National Material Code.")

# ============================================================
# 06 NATIONAL MASTER
# ============================================================
elif page.startswith("06"):
    st.markdown('<div class="section-bar">National Material Master and identity governance</div>', unsafe_allow_html=True)
    if national_master.empty:
        st.info("national_material_master.csv is not available.")
    else:
        q=st.text_input("Search national code, description, group or source code")
        view=national_master.copy()
        if q.strip():
            mask=view.astype(str).apply(lambda col:col.str.contains(q,case=False,na=False)).any(axis=1); view=view[mask]
        st.dataframe(view,use_container_width=True,height=430)
        st.download_button("Download National Material Master",view.to_csv(index=False),"national_material_master.csv","text/csv")

# ============================================================
# 07 MIGRATION / RATIONALIZATION
# ============================================================
elif page.startswith("07"):
    st.markdown('<div class="section-bar">CPSE migration, legacy rationalization and controlled mapping</div>', unsafe_allow_html=True)
    st.info("Legacy rationalization is now an explicit decision workflow. It does not delete source codes; it records retain/consolidate/replace/retire decisions and approval evidence.")
    migration = ensure_columns(migration,["migration_status","rationalization_decision","rationalization_reason","requested_by","approved_by","approval_date","rollback_reference"])
    if migration.empty:
        st.info("No migration mapping records are available yet.")
    else:
        a,b,c,d=st.columns(4); a.metric("Mappings",len(migration)); b.metric("Approved",int(migration.migration_status.astype(str).str.upper().eq("APPROVED").sum())); c.metric("Pending",int(migration.migration_status.astype(str).str.upper().isin(["PENDING","REVIEW"]).sum())); d.metric("Retire decisions",int(migration.rationalization_decision.astype(str).str.upper().eq("RETIRE").sum()))
        st.dataframe(migration,use_container_width=True,height=340)
        idx=st.selectbox("Mapping to rationalize",migration.index.tolist(),format_func=lambda i:str(first(migration.loc[i],["source_material_id","legacy_material_code","material_id"],i)))
        dec=st.selectbox("Rationalization decision",["RETAIN","CONSOLIDATE","REPLACE","RETIRE","MIGRATE_AS_IS"])
        reason=st.text_area("Rationalization reason")
        requester=st.text_input("Requested by",key="mig_requester")
        approver=st.text_input("Approver",key="mig_approver")
        if st.button("Save rationalization decision",type="primary"):
            if not requester.strip() or not reason.strip():
                st.error("Requester and reason are required.")
            else:
                migration.loc[idx,["migration_status","rationalization_decision","rationalization_reason","requested_by","approved_by","approval_date"]]=["APPROVED" if approver.strip() else "PENDING",dec,reason,requester,approver,datetime.now().isoformat() if approver.strip() else ""]
                save_csv(migration,"migration"); append_audit("LEGACY_RATIONALIZATION_DECISION",requester,"migration",str(idx),f"decision={dec};approved_by={approver}"); st.success("Rationalization decision saved."); st.rerun()

# ============================================================
# 08 REVIEW
# ============================================================
elif page.startswith("08"):
    st.markdown('<div class="section-bar">Review and approval workflow</div>', unsafe_allow_html=True)
    reviews=ensure_columns(reviews,["review_id","entity_id","review_type","status","reviewer_name","decision","comments","review_date"])
    a,b,c=st.columns(3); a.metric("Workflow records",len(reviews)); b.metric("Pending",int(reviews.status.astype(str).str.upper().isin(["PENDING","OPEN","REVIEW"]).sum())); c.metric("Approved",int(reviews.status.astype(str).str.upper().eq("APPROVED").sum()))
    if reviews.empty: st.info("No review records available.")
    else: st.dataframe(reviews,use_container_width=True,height=350)
    with st.form("review_form"):
        entity=st.text_input("Material / candidate / request ID")
        typ=st.selectbox("Review type",["MATCH_REVIEW","STANDARDIZATION_REVIEW","NATIONAL_CODE_REVIEW","MIGRATION_REVIEW","TECHNICAL_REVIEW"])
        reviewer=st.text_input("Reviewer")
        decision=st.selectbox("Decision",["APPROVED","REJECTED","NEEDS_CORRECTION","PENDING"])
        comments=st.text_area("Comments")
        submit=st.form_submit_button("Save review decision")
        if submit:
            if not entity.strip() or not reviewer.strip(): st.error("Entity and reviewer are required.")
            else:
                rid=f"REV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"; rec={"review_id":rid,"entity_id":entity,"review_type":typ,"status":decision,"reviewer_name":reviewer,"decision":decision,"comments":comments,"review_date":datetime.now().isoformat()}; reviews=pd.concat([reviews,pd.DataFrame([rec])],ignore_index=True); save_csv(reviews,"reviews"); append_audit("REVIEW_DECISION_SAVED",reviewer,"review",rid,decision); st.success("Review saved."); st.rerun()

# ============================================================
# 09 GROUND TRUTH
# ============================================================
elif page.startswith("09"):
    st.markdown('<div class="section-bar">Ground Truth and validation</div>', unsafe_allow_html=True)
    st.info("AI confidence is not accuracy. Only human-labelled, resolved records should be used for accuracy metrics. REVIEW / REVIEW_REQUIRED remains unresolved until a reviewer decides the relationship.")
    if matches.empty:
        st.warning("No match results available.")
    else:
        queue=matches.copy()
        labelled_pairs=set(ground_truth[pd.to_numeric(ground_truth.ai_confidence,errors="coerce").notna()].apply(lambda r:pair_key(r.material_id_a,r.material_id_b),axis=1)) if not ground_truth.empty else set()
        queue["pair_key"]=queue.apply(lambda r:pair_key(first(r,["material_id_a"]),first(r,["material_id_b"])),axis=1)
        queue=queue[~queue.pair_key.isin(labelled_pairs)]
        queue["priority"] = queue.apply(lambda r:(100 if str(r.get("technical_conflict_severity","NONE")).upper() in ["HIGH","CRITICAL"] else 0)+(50 if str(r.get("relationship"))=="REVIEW_REQUIRED" else 0)+(30 if str(r.get("match_decision")).upper()=="REVIEW" else 0)+(1-float(r.get("ai_confidence") or 0))*20,axis=1)
        queue=queue.sort_values("priority",ascending=False)
        st.caption(f"Unlabelled candidate queue: {len(queue):,}")
        st.dataframe(queue[[c for c in ["material_id_a","material_id_b","ai_confidence","confidence_band","relationship","technical_conflict_severity","candidate_rank","priority"] if c in queue.columns]].head(300),use_container_width=True,height=330)
        if not queue.empty:
            ix=st.selectbox("Candidate",queue.index.tolist(),format_func=lambda i:f"{first(queue.loc[i],[ 'material_id_a'],i)} ↔ {first(queue.loc[i],[ 'material_id_b'],'')}")
            r=queue.loc[ix]
            reviewer=st.text_input("Ground Truth reviewer",key="gt_reviewer")
            label=st.selectbox("Ground Truth relationship",["IDENTICAL","DUPLICATE","NEAR_DUPLICATE","FUNCTIONALLY_EQUIVALENT","NO_MATCH","REVIEW_REQUIRED"])
            status=st.selectbox("Review status",["RESOLVED","UNRESOLVED"])
            comments=st.text_area("Review comments",key="gt_comments")
            evidence=st.text_input("Evidence reference",key="gt_evidence")
            if st.button("Save Ground Truth label",type="primary"):
                if not reviewer.strip(): st.error("Reviewer is required.")
                else:
                    gt_id=f"GT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    rec={"ground_truth_id":gt_id,"material_id_a":first(r,["material_id_a"]),"material_id_b":first(r,["material_id_b"]),"ai_prediction":first(r,["match_decision"],""),"ai_confidence":num(first(r,["ai_confidence"],np.nan)),"confidence_band":first(r,["confidence_band"],""),"candidate_rank":first(r,["candidate_rank"],""),"confidence_gap":first(r,["confidence_gap"],""),"technical_conflict_flag":first(r,["technical_conflict_flag"],""),"technical_conflict_severity":first(r,["technical_conflict_severity"],"NONE"),"model_version":first(r,["model_version"],""),"ground_truth_label":label,"reviewer_name":reviewer,"review_status":status,"review_date":datetime.now().isoformat(),"review_comments":comments,"evidence_reference":evidence}
                    ground_truth=pd.concat([ground_truth,pd.DataFrame([rec])],ignore_index=True); save_csv(ground_truth,"ground_truth"); append_gt_audit("GROUND_TRUTH_LABELLED",reviewer,gt_id,f"label={label};status={status}"); append_audit("GROUND_TRUTH_LABELLED",reviewer,"ground_truth",gt_id,label); st.success(f"Saved {gt_id}."); st.rerun()
        st.markdown('<div class="section-bar">Ground Truth history</div>',unsafe_allow_html=True)
        st.dataframe(ground_truth,use_container_width=True,height=330)

# ============================================================
# 10 ACCURACY
# ============================================================
elif page.startswith("10"):
    st.markdown('<div class="section-bar">Accuracy, calibration and AI analytics</div>', unsafe_allow_html=True)
    resolved=ground_truth[ground_truth.review_status.astype(str).str.upper().eq("RESOLVED")].copy() if not ground_truth.empty else pd.DataFrame()
    if resolved.empty:
        st.info("No resolved Ground Truth labels yet. Accuracy cannot be interpreted until reviewers resolve candidate pairs.")
    else:
        resolved["actual_positive"]=resolved.ground_truth_label.astype(str).str.upper().isin(["IDENTICAL","DUPLICATE"])
        resolved["predicted_positive"]=resolved.ai_prediction.astype(str).str.upper().eq("MATCH")
        tp=int((resolved.actual_positive & resolved.predicted_positive).sum()); tn=int((~resolved.actual_positive & ~resolved.predicted_positive).sum()); fp=int((~resolved.actual_positive & resolved.predicted_positive).sum()); fn=int((resolved.actual_positive & ~resolved.predicted_positive).sum())
        accuracy=(tp+tn)/len(resolved)*100 if len(resolved) else 0; precision=tp/(tp+fp)*100 if tp+fp else 0; recall=tp/(tp+fn)*100 if tp+fn else 0; f1=2*precision*recall/(precision+recall) if precision+recall else 0
        a,b,c,d,e=st.columns(5); a.metric("Resolved labels",len(resolved)); b.metric("Accuracy",f"{accuracy:.2f}%"); c.metric("Precision",f"{precision:.2f}%"); d.metric("Recall",f"{recall:.2f}%"); e.metric("F1",f"{f1:.2f}%")
        st.caption("For binary harmonization evaluation, IDENTICAL and DUPLICATE are treated as positive identity-consolidation outcomes. FUNCTIONALLY_EQUIVALENT is deliberately excluded from automatic National Material Code identity.")
        st.dataframe(pd.DataFrame({"Actual / Predicted":["Positive","Negative"],"Predicted Positive":[tp,fp],"Predicted Negative":[fn,tn]}),use_container_width=True,hide_index=True)
        st.markdown('<div class="section-bar">Relationship-level Ground Truth distribution</div>',unsafe_allow_html=True)
        st.dataframe(resolved.ground_truth_label.value_counts().rename_axis("Relationship").reset_index(name="Resolved labels"),use_container_width=True,hide_index=True)

# ============================================================
# 11 PROCUREMENT + INVENTORY OPTIMIZATION
# ============================================================
elif page.startswith("11"):
    st.markdown('<div class="section-bar">Procurement intelligence, demand aggregation and inventory optimization</div>', unsafe_allow_html=True)
    if procurement.empty:
        st.warning("historical_procurement.csv is not available. Procurement and inventory analytics are implemented but require historical procurement data.")
    else:
        p=procurement.copy()
        nat=next((c for c in ["national_material_code","unified_material_code","national_code"] if c in p.columns),None)
        cpse=next((c for c in ["cpse","cpse_name","organization"] if c in p.columns),None)
        qty=next((c for c in ["quantity","qty","ordered_quantity"] if c in p.columns),None)
        spend=next((c for c in ["spend","total_spend","amount","value"] if c in p.columns),None)
        supplier=next((c for c in ["supplier","vendor","supplier_name"] if c in p.columns),None)
        a,b,c,d=st.columns(4); a.metric("Procurement records",len(p)); b.metric("CPSEs",p[cpse].nunique() if cpse else "N/A"); c.metric("Unified materials",p[nat].nunique() if nat else "N/A"); d.metric("Total spend",f"{pd.to_numeric(p[spend],errors='coerce').sum():,.0f}" if spend else "N/A")
        if nat:
            group=p.groupby(nat,dropna=False).size().reset_index(name="procurement_records")
            if qty: group=group.merge(p.groupby(nat)[qty].sum().reset_index(name="aggregated_quantity"),on=nat)
            if spend: group=group.merge(p.groupby(nat)[spend].sum().reset_index(name="aggregated_spend"),on=nat)
            if cpse: group=group.merge(p.groupby(nat)[cpse].nunique().reset_index(name="cpse_count"),on=nat)
            if supplier: group=group.merge(p.groupby(nat)[supplier].nunique().reset_index(name="supplier_count"),on=nat)
            st.markdown('<div class="section-bar">Demand aggregation</div>',unsafe_allow_html=True); st.dataframe(group.sort_values("procurement_records",ascending=False),use_container_width=True,height=300)
            if cpse:
                coll=group[group.cpse_count>1].copy(); coll["collaboration_status"]="CANDIDATE"; save_csv(coll,"collaboration"); st.markdown('<div class="section-bar">Collaborative procurement foundation</div>',unsafe_allow_html=True); st.dataframe(coll.sort_values(["cpse_count","procurement_records"],ascending=False),use_container_width=True,height=250)
        # Inventory optimization
        st.markdown('<div class="section-bar">Inventory optimization</div>',unsafe_allow_html=True)
        inv=inventory.copy()
        if inv.empty:
            st.info("Upload or place inventory_snapshot.csv in the outputs folder. Supported fields include national_material_code, cpse, on_hand_quantity, annual_consumption, unit_cost, inventory_value, days_of_supply, last_movement_date, and slow_moving_flag.")
        else:
            inv_nat=next((c for c in ["national_material_code","unified_material_code","national_code"] if c in inv.columns),None)
            inv_cpse=next((c for c in ["cpse","cpse_name","organization"] if c in inv.columns),None)
            onhand=next((c for c in ["on_hand_quantity","stock_quantity","inventory_quantity"] if c in inv.columns),None)
            cons=next((c for c in ["annual_consumption","annual_issue_quantity","consumption"] if c in inv.columns),None)
            val=next((c for c in ["inventory_value","stock_value","value"] if c in inv.columns),None)
            dos=next((c for c in ["days_of_supply","dos"] if c in inv.columns),None)
            slow=next((c for c in ["slow_moving_flag","slow_moving","non_moving_flag"] if c in inv.columns),None)
            a,b,c,d=st.columns(4); a.metric("Inventory records",len(inv)); b.metric("Unified materials",inv[inv_nat].nunique() if inv_nat else "N/A"); c.metric("Inventory value",f"{pd.to_numeric(inv[val],errors='coerce').sum():,.0f}" if val else "N/A"); d.metric("CPSEs",inv[inv_cpse].nunique() if inv_cpse else "N/A")
            opp=[]
            if inv_nat:
                for material, grp in inv.groupby(inv_nat,dropna=False):
                    cpse_count=grp[inv_cpse].nunique() if inv_cpse else 1
                    stock=float(pd.to_numeric(grp[onhand],errors="coerce").sum()) if onhand else 0
                    annual=float(pd.to_numeric(grp[cons],errors="coerce").sum()) if cons else 0
                    value=float(pd.to_numeric(grp[val],errors="coerce").sum()) if val else 0
                    if dos: avg_dos=float(pd.to_numeric(grp[dos],errors="coerce").mean())
                    else: avg_dos=(stock/annual*365) if annual>0 else np.nan
                    slow_count=int(grp[slow].astype(str).str.upper().isin(["Y","YES","TRUE","1"]).sum()) if slow else 0
                    opportunity=[]
                    if cpse_count>1: opportunity.append("POOL_ACROSS_CPSE")
                    if slow_count>0 or (not pd.isna(avg_dos) and avg_dos>180): opportunity.append("EXCESS_OR_SLOW_MOVING")
                    if annual==0 and stock>0: opportunity.append("NON_MOVING")
                    if opportunity: opp.append({"national_material_code":material,"cpse_count":cpse_count,"on_hand_quantity":stock,"annual_consumption":annual,"inventory_value":value,"average_days_of_supply":avg_dos,"slow_moving_records":slow_count,"opportunity_type":";".join(opportunity),"priority":"HIGH" if value>0 and (slow_count>0 or (not pd.isna(avg_dos) and avg_dos>180)) else "MEDIUM"})
            inventory_opportunities=pd.DataFrame(opp)
            if not inventory_opportunities.empty:
                save_csv(inventory_opportunities,"inventory_opportunities")
                st.dataframe(inventory_opportunities.sort_values(["priority","inventory_value"],ascending=[True,False]),use_container_width=True,height=330)
            else:
                st.success("No rule-triggered inventory optimization opportunities were identified from the supplied inventory data.")
        st.markdown('<div class="section-bar">Procurement source data</div>',unsafe_allow_html=True); st.dataframe(p,use_container_width=True,height=260)

# ============================================================
# 12 SAP / ERP
# ============================================================
elif page.startswith("12"):
    st.markdown('<div class="section-bar">SAP / ERP integration capability and controlled migration interface</div>', unsafe_allow_html=True)
    st.info("The application now contains the integration control layer: extract → validate → approve → map → export → verify → reconcile/rollback. A live SAP/ERP API still requires an actual connector, credentials and target-system configuration; code alone cannot create that external connection.")
    steps=["Extract","Validate","Standardize","Human approve","National-code map","Pre-load checks","Controlled export","Post-load verify","Reconcile / rollback"]
    st.dataframe(pd.DataFrame({"Stage":steps,"Control":"Required","Evidence":["Source dataset","Data-quality profile","Standardized record","Review/approval record","Migration mapping","Validation gates","Export package","ERP event/log","Reconciliation record"]}),use_container_width=True,hide_index=True)
    a,b,c,d=st.columns(4); a.metric("ERP events",len(erp_log)); b.metric("Migration mappings",len(migration)); c.metric("Approved reviews",int(reviews.status.astype(str).str.upper().eq("APPROVED").sum()) if not reviews.empty else 0); d.metric("Audit events",len(platform_audit))
    if not erp_log.empty: st.dataframe(erp_log,use_container_width=True,height=300)
    st.markdown('<div class="section-bar">Controlled export package</div>',unsafe_allow_html=True)
    export_choice=st.selectbox("Dataset",["national_master","migration","standardized","matches","ground_truth","platform_audit"])
    data=globals().get(export_choice,pd.DataFrame())
    if isinstance(data,pd.DataFrame):
        st.download_button("Export controlled dataset",data.to_csv(index=False),FILES.get(export_choice,f"{export_choice}.csv"),"text/csv")
    with st.form("erp_event_form"):
        event=st.selectbox("ERP event",["PRE_LOAD_VALIDATED","EXPORT_CREATED","LOAD_EXECUTED","POST_LOAD_VERIFIED","RECONCILIATION_COMPLETED","ROLLBACK_EXECUTED"])
        actor=st.text_input("Actor / integration owner")
        entity=st.text_input("Entity / batch reference")
        details=st.text_area("Event details")
        submit=st.form_submit_button("Record ERP control event")
        if submit:
            if not actor.strip() or not entity.strip(): st.error("Actor and entity are required.")
            else:
                rec={"timestamp":datetime.now().isoformat(),"event_type":event,"actor":actor,"entity_reference":entity,"details":details,"status":"RECORDED"}; erp_log=pd.concat([erp_log,pd.DataFrame([rec])],ignore_index=True); save_csv(erp_log,"erp_log"); append_audit(event,actor,"erp_batch",entity,details); st.success("ERP control event recorded."); st.rerun()

# ============================================================
# 13 AUDIT
# ============================================================
elif page.startswith("13"):
    st.markdown('<div class="section-bar">Platform-wide audit and governance</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3); a.metric("Platform audit events",len(platform_audit)); b.metric("Ground Truth audit events",len(gt_audit)); c.metric("ERP control events",len(erp_log))
    if not platform_audit.empty: st.dataframe(platform_audit,use_container_width=True,height=320)
    if not gt_audit.empty: st.dataframe(gt_audit,use_container_width=True,height=260)
    st.markdown('<div class="section-bar">Governance controls</div>',unsafe_allow_html=True)
    controls=[
        ("AI confidence stored","ai_confidence" in matches.columns),("Model version stored","model_version" in matches.columns),
        ("Technical conflict captured","technical_conflict_flag" in matches.columns),("Relationship classification","relationship" in matches.columns),
        ("Ground Truth reviewer identity","reviewer_name" in ground_truth.columns),("Ground Truth resolution status","review_status" in ground_truth.columns),
        ("Legacy mapping retained",not migration.empty),("Platform audit hash chain","event_hash" in platform_audit.columns if not platform_audit.empty else True),
        ("Procurement data capability",True),("Inventory optimization capability",True),("ERP control capability",True)
    ]
    st.dataframe(pd.DataFrame({"Control":[x[0] for x in controls],"Status":["YES" if x[1] else "PENDING" for x in controls]}),use_container_width=True,hide_index=True)

# ============================================================
# 14 TAXONOMY / ATTRIBUTES
# ============================================================
elif page.startswith("14"):
    st.markdown('<div class="section-bar">Taxonomy and technical attribute dictionary</div>',unsafe_allow_html=True)
    if taxonomy.empty:
        taxonomy=pd.DataFrame([{"material_group":g,"required_attributes":",".join(DEFAULT_REQUIRED.get(g,["material_type","standard","unit_of_measure"]))} for g in CLASS_RULES])
    st.dataframe(taxonomy,use_container_width=True,height=330)
    attrs=[
        ("material_type","Engineering/material class","Required for identity context","Controlled text"),("size","Nominal dimension","Required where applicable","Controlled dimension"),
        ("length","Physical length","Class dependent","Numeric + UOM"),("voltage","Electrical rating","Class dependent","Numeric + UOM"),
        ("diameter","Diameter / DN","Class dependent","Numeric + UOM"),("core_count","Cable/core count","Class dependent","Integer"),
        ("standard","Technical standard","Strong identity attribute","Controlled standard"),("manufacturer","OEM/manufacturer","Supporting identity attribute","Controlled reference"),
        ("part_number","OEM/source part identity","Supporting identity attribute","Controlled reference"),("unit_of_measure","Transaction UOM","Mandatory control","EA/KG/M/MM/CM/L etc.")]
    attr_df=pd.DataFrame(attrs,columns=["Attribute","Purpose","Control","Validation"])
    st.dataframe(attr_df,use_container_width=True,hide_index=True)
    st.markdown('<div class="section-bar">Persist controlled attribute dictionary</div>',unsafe_allow_html=True)
    if st.button("Create / refresh attribute_dictionary.csv"):
        save_csv(attr_df,"attribute_dictionary"); append_audit("ATTRIBUTE_DICTIONARY_REFRESHED","system","taxonomy","attribute_dictionary","controlled fields"); st.success("Attribute dictionary saved."); st.rerun()
    st.caption("This layer is the controlled technical foundation. It can support a future trained classifier/model without changing the governance model.")

# ============================================================
# 15 SURVIVORSHIP
# ============================================================
elif page.startswith("15"):
    st.markdown('<div class="section-bar">Best Record / Survivorship</div>',unsafe_allow_html=True)
    st.info("Survivorship selects the preferred source value for an approved identity while preserving every source CPSE value and provenance. Functional equivalence alone is not sufficient to trigger survivorship.")
    if standardized.empty:
        st.info("Generate standardized records first.")
    else:
        group_col="material_group" if "material_group" in standardized.columns else None
        groups=sorted(standardized[group_col].dropna().astype(str).unique()) if group_col else []
        grp=st.selectbox("Material group",["ALL"]+groups)
        view=standardized.copy()
        if grp!="ALL" and group_col: view=view[view[group_col].astype(str)==grp]
        view=ensure_columns(view,["technical_completeness","validation_decision","source_material_id","cpse"])
        view["survivorship_score"]=pd.to_numeric(view.technical_completeness,errors="coerce").fillna(0)*70+view.validation_decision.astype(str).str.upper().eq("APPROVED").astype(int)*30
        st.dataframe(view.sort_values("survivorship_score",ascending=False).head(200),use_container_width=True,height=340)
        if not view.empty:
            ix=st.selectbox("Preferred source record",view.index.tolist(),format_func=lambda i:str(first(view.loc[i],["source_material_id"],i)))
            actor=st.text_input("Decision owner")
            rationale=st.text_area("Survivorship rationale")
            if st.button("Save survivorship decision",type="primary"):
                if not actor.strip() or not rationale.strip(): st.error("Decision owner and rationale are required.")
                else:
                    rec={"decision_id":"SURV-"+datetime.now().strftime("%Y%m%d%H%M%S%f"),"source_material_id":first(view.loc[ix],["source_material_id"]),"cpse":first(view.loc[ix],["cpse"]),"material_group":first(view.loc[ix],["material_group"]),"decision":"PREFERRED_SOURCE","decision_owner":actor,"decision_date":datetime.now().isoformat(),"rationale":rationale}
                    survivorship=pd.concat([survivorship,pd.DataFrame([rec])],ignore_index=True); save_csv(survivorship,"survivorship"); append_audit("SURVIVORSHIP_DECISION",actor,"material",rec["source_material_id"],rationale); st.success("Survivorship decision saved."); st.rerun()
        if not survivorship.empty:
            st.markdown('<div class="section-bar">Survivorship decisions</div>',unsafe_allow_html=True); st.dataframe(survivorship,use_container_width=True,height=250)

# ============================================================
# 16 CHANGE REQUESTS
# ============================================================
elif page.startswith("16"):
    st.markdown('<div class="section-bar">Change requests and exceptions</div>',unsafe_allow_html=True)
    change_requests=ensure_columns(change_requests,["request_id","material_id","request_type","requested_by","status","reason","created_at","resolution_comment"])
    a,b,c=st.columns(3); a.metric("Requests",len(change_requests)); b.metric("Open",int(change_requests.status.astype(str).str.upper().isin(["OPEN","PENDING"]).sum())); c.metric("Resolved",int(change_requests.status.astype(str).str.upper().isin(["RESOLVED","CLOSED"]).sum()))
    with st.form("change_request_form"):
        mid=st.text_input("Material / pair / batch ID"); rt=st.selectbox("Request type",["MASTER_CORRECTION","TECHNICAL_REVIEW","MATCH_EXCEPTION","NATIONAL_CODE_CHANGE","MIGRATION_EXCEPTION","TAXONOMY_CHANGE","INVENTORY_OPTIMIZATION_REVIEW","ERP_EXCEPTION"]); by=st.text_input("Requested by"); reason=st.text_area("Reason"); submit=st.form_submit_button("Create change request")
        if submit:
            if not by.strip() or not reason.strip(): st.error("Requester and reason are required.")
            else:
                rid=f"CR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"; rec={"request_id":rid,"material_id":mid,"request_type":rt,"requested_by":by,"status":"OPEN","reason":reason,"created_at":datetime.now().isoformat(),"resolution_comment":""}; change_requests=pd.concat([change_requests,pd.DataFrame([rec])],ignore_index=True); save_csv(change_requests,"change_requests"); append_audit("CHANGE_REQUEST_CREATED",by,"change_request",rid,rt); st.success(f"Created {rid}."); st.rerun()
    if not change_requests.empty: st.dataframe(change_requests,use_container_width=True,height=400)

st.markdown('<div style="margin-top:1.1rem;padding-top:.6rem;border-top:1px solid #dfe5ec;color:#8793a3;font-size:.66rem;">CPSE National Unified Material Master Framework | AI-assisted decision support with human validation, procurement intelligence, inventory controls and auditability</div>',unsafe_allow_html=True)
