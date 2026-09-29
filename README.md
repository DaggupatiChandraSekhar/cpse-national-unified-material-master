# CPSE National Unified Material Master

### AI-Assisted Material Harmonization, Intelligent Matching, Governance & Migration Framework

> **One Nation – One Material Code**

An AI-assisted prototype for harmonizing material masters across Central Public Sector Enterprises (CPSEs), identifying identical, duplicate, near-duplicate and functionally equivalent materials, and creating a governed foundation for a National Unified Material Master.

---

# 1. Problem Statement

Large CPSE ecosystems across sectors such as:

* Oil & Gas
* Power
* Steel
* Mining
* Heavy Engineering
* Industrial Manufacturing

procure and maintain many materials that are identical or technically similar, but are represented differently across organizations.

The same or equivalent material may have:

* Different material codes
* Different descriptions
* Different abbreviations
* Different units of measure
* Different technical specifications
* Different attribute names
* Different classifications
* Different naming conventions
* Different ERP/SAP master-data structures

This creates a fragmented material-master environment.

## Key Challenges

### 1. Duplicate Material Masters

The same material may exist multiple times under different CPSE-specific codes.

### 2. Inconsistent Descriptions

Descriptions may use different word orders, abbreviations, units, symbols and terminology.

### 3. Hidden Technical Similarity

Two materials may be functionally equivalent even when their descriptions are substantially different.

### 4. Difficult Cross-CPSE Identification

Procurement teams may not easily discover that another CPSE already uses an identical or equivalent material.

### 5. Fragmented Procurement

Similar requirements are distributed across organizations instead of being visible as a unified demand opportunity.

### 6. Poor Migration Visibility

Legacy CPSE material codes need traceable mapping to standardized national identities.

### 7. Governance Challenges

Material-master changes require validation, approval, traceability and auditability.

---

# 2. Proposed Solution

The **CPSE National Unified Material Master Framework** provides an AI-assisted pipeline that converts heterogeneous material records into a governed common material-master structure.

The prototype combines:

* Data ingestion
* Data-quality validation
* Material understanding
* Standardization
* Intelligent matching
* Duplicate detection
* Technical conflict detection
* National material-code generation
* CPSE migration mapping
* Human review
* Ground Truth creation
* Accuracy measurement
* Audit and governance
* Taxonomy and attribute management
* Survivorship analysis
* Change-request management
* Procurement intelligence
* SAP/ERP integration readiness

The central principle is:

> **AI recommends. Humans validate. Governance controls. The National Master preserves traceability.**

---

# 3. Core Vision

The framework is designed around a common national material identity while preserving the original CPSE records.

Instead of replacing legacy material information, the platform creates a relationship:

```text
CPSE Legacy Material
        |
        v
Data Quality & Understanding
        |
        v
AI Matching / Similarity Analysis
        |
        v
Duplicate / Equivalence Intelligence
        |
        v
Human Validation
        |
        v
National Material Identity
        |
        +--------------------+
        |                    |
        v                    v
Migration Mapping     Procurement Intelligence
        |
        v
ERP / SAP Integration
```

---

# 4. Material Relationship Intelligence

The prototype distinguishes different types of material relationships.

## IDENTICAL

Materials represent the same material identity based on available evidence.

## DUPLICATE

Records appear to represent the same underlying material and may be candidates for consolidation.

## NEAR_DUPLICATE

Materials are highly similar but require technical validation before consolidation.

## FUNCTIONALLY_EQUIVALENT

Materials may serve the same or similar functional purpose but should not automatically receive the same National Material Code.

## NO_MATCH

Available evidence does not establish a sufficiently strong relationship.

## REVIEW_REQUIRED

Evidence is insufficient or conflicting and requires human assessment.

This distinction is important because:

> **Functional equivalence does not automatically mean common material identity.**

---

# 5. What Makes the Prototype Different

The prototype is not just a similarity-search application.

It connects **AI-assisted matching with enterprise master-data governance**.

## 5.1 AI + Human-in-the-Loop

AI produces candidate relationships and confidence information.

Human reviewers make the final Ground Truth decision.

This prevents AI confidence from being incorrectly treated as proven accuracy.

## 5.2 Confidence Gap Awareness

The platform does not only look at the top match.

It also considers the difference between competing candidates.

A small confidence gap can indicate ambiguity and trigger additional review.

## 5.3 Technical Conflict Detection

Textual similarity alone can produce unsafe matches.

The framework therefore considers technical conflicts such as differences in important specifications and attributes.

```text
High textual similarity

        ≠

Automatically identical material
```

## 5.4 Ground Truth Instead of Artificial Accuracy

The prototype separates:

```text
AI Prediction

        from

Human-Validated Ground Truth
```

Accuracy, precision, recall and F1 are calculated from reviewer-resolved cases rather than simply treating AI predictions as truth.

## 5.5 Traceable National Identity

The National Material Master is designed to preserve relationships back to source records.

The objective is:

```text
National Material Code
        |
        +--- CPSE A legacy code
        +--- CPSE B legacy code
        +--- CPSE C legacy code
        +--- CPSE D legacy code
```

This provides a foundation for controlled migration rather than uncontrolled replacement.

## 5.6 Governance by Design

The prototype includes:

* Review workflow
* Approval concepts
* Ground Truth register
* Reviewer information
* Review comments
* Evidence references
* Audit records
* Change requests
* Exception handling
* Traceability

---

# 6. Prototype Architecture

```text
                  ┌─────────────────────────┐
                  │   CPSE Source Data      │
                  │ Codes / Descriptions    │
                  │ Specs / UOM / Attributes│
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ AI Ingestion &          │
                  │ Data Quality             │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Material Understanding  │
                  │ Normalization / NLP     │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Intelligent Matching    │
                  │ Similarity + Evidence   │
                  └────────────┬────────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
        ┌──────────────────┐      ┌──────────────────┐
        │ Duplicate        │      │ Technical        │
        │ Intelligence     │      │ Conflict Checks  │
        └────────┬─────────┘      └────────┬─────────┘
                 └──────────────┬──────────┘
                                ▼
                  ┌─────────────────────────┐
                  │ Human Review & Approval │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Ground Truth & Accuracy │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ National Material Master│
                  └────────────┬────────────┘
                               │
                ┌──────────────┼────────────────┐
                ▼              ▼                ▼
        ┌──────────────┐ ┌──────────────┐ ┌───────────────┐
        │ Migration    │ │ Procurement  │ │ Governance &  │
        │ Mapping      │ │ Intelligence │ │ Audit         │
        └──────────────┘ └──────────────┘ └───────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ SAP / ERP Integration   │
                  │ Readiness Layer         │
                  └─────────────────────────┘
```

---

# 7. Prototype Modules

The Streamlit prototype provides an enterprise-style control interface.

## 01 — Executive Dashboard

Provides a consolidated view of the material-harmonization pipeline.

Includes indicators for:

* National material master
* Match candidates
* Matching decisions
* Review cases
* Technical conflicts
* Ground Truth status
* Pipeline status

## 02 — AI Ingestion & Data Quality

Provides visibility into incoming material data and its quality.

The framework is designed to handle heterogeneous source structures and prepare records for downstream harmonization.

## 03 — AI Material Understanding

Supports interpretation and normalization of material information.

Key concepts include:

* Description normalization
* Attribute interpretation
* Units
* Technical parameters
* Material characteristics
* Controlled terminology

## 04 — AI Material Matching

Core intelligence layer for identifying candidate relationships between materials.

The matching framework considers available material information and produces:

* Candidate matches
* Match decisions
* Confidence information
* Candidate ranking
* Confidence gaps
* Technical evidence
* Model-version information

## 05 — Duplicate Intelligence

Identifies potential:

* Exact duplicates
* Duplicate candidates
* Near duplicates
* Similar material records
* Technical conflicts

The objective is to provide a structured consolidation-review pipeline.

## 06 — National Material Master

Provides the proposed common material-master view.

The master is intended to establish:

* National material identity
* Standardized material information
* Unified material codes
* Cross-CPSE relationships
* Source-record traceability

## 07 — CPSE Migration Mapping

Connects legacy CPSE material records to the proposed national material identity.

```text
Legacy CPSE Code
        ↓
National Material Code
        ↓
Migration / Mapping Decision
```

## 08 — Review & Approval

Provides a human-in-the-loop workflow.

Reviewers can examine AI recommendations and make governed decisions rather than allowing automatic consolidation of uncertain records.

## 09 — Ground Truth & Validation

One of the most important components of the prototype.

Reviewer-labelled cases are stored separately from AI predictions.

Ground Truth records can contain:

* Material pair
* AI prediction
* AI confidence
* Confidence band
* Candidate rank
* Confidence gap
* Technical conflict information
* Model version
* Human label
* Reviewer
* Review status
* Review date
* Comments
* Evidence reference

## 10 — Accuracy & AI Analytics

Uses reviewer-resolved Ground Truth to calculate observed AI performance.

The prototype supports:

* Accuracy
* Precision
* Recall
* F1
* Confusion matrix
* Confidence-band analysis
* Model-version performance
* Reviewer statistics

If no human-labelled Ground Truth exists, accuracy is explicitly treated as **not established** rather than being fabricated.

## 11 — Audit & Governance

Provides traceability for governed decisions.

The prototype includes audit information associated with Ground Truth and review activities.

The Ground Truth engine also supports audit hashing and chain-based integrity mechanisms.

## 12 — SAP / ERP Integration

Defines the integration boundary for future enterprise implementation.

Current prototype capabilities include export/readiness for:

* National material master
* Legacy CPSE mapping
* Ground Truth
* AI matching results
* Review decisions
* Audit information

The prototype does **not** claim live SAP connectivity.

Instead, it establishes a controlled integration boundary for future:

* ERP APIs
* SAP master-data integration
* Data import pipelines
* Master-data write-back
* Enterprise deployment

## 13 — Taxonomy & Attribute Dictionary

Provides the foundation for controlled classification and technical attributes.

The framework supports concepts such as:

* Material groups
* Attribute names
* Data types
* Units
* Mandatory attributes
* Standards/reference information

## 14 — Best Record / Survivorship

Supports source-record consolidation analysis.

Where multiple source records contribute to a common national identity, the framework provides visibility into source-record counts and survivorship relationships.

## 15 — Change Requests / Exceptions

Provides a controlled mechanism for post-harmonization changes.

Supported request concepts include:

* Code correction
* Merge
* Split
* Attribute correction
* Exception

This creates a governance pathway for changes after the initial harmonization process.

---

# 8. AI / Matching Methodology

The matching framework is designed around multiple evidence signals rather than a single string comparison.

Conceptually:

```text
Material Description
        +
Technical Specifications
        +
Normalized Attributes
        +
Units / Measurements
        +
Classification
        +
Candidate Ranking
        +
Technical Conflict Detection
        +
Confidence
        +
Confidence Gap
        ↓
Relationship Recommendation
```

The prototype uses a combination of data-processing, similarity and fuzzy-matching techniques to generate candidate relationships.

The resulting recommendation is then exposed to human review where required.

---

# 9. Human-in-the-Loop Decision Model

The system follows:

```text
AI Recommendation
        ↓
Evidence Review
        ↓
Technical Validation
        ↓
Human Decision
        ↓
Ground Truth
        ↓
Accuracy Measurement
```

This creates a feedback-oriented governance loop:

```text
AI
 ↓
Human Review
 ↓
Ground Truth
 ↓
Performance Measurement
 ↓
Model / Rule Improvement
```

---

# 10. Ground Truth Governance

A key design principle is:

> **AI confidence is evidence, not proof of accuracy.**

The prototype therefore keeps separate:

### AI Prediction

What the system predicted.

### Human Label

What the reviewer determined after examining the case.

### Ground Truth

The controlled dataset of reviewer-resolved cases used for evaluation.

This prevents a common problem in AI prototypes:

```text
AI predicted MATCH
        ↓
System assumes MATCH is correct
        ↓
"Accuracy" = artificially high
```

Instead:

```text
AI predicted MATCH
        ↓
Reviewer evaluates evidence
        ↓
Human label recorded
        ↓
AI prediction compared with Ground Truth
        ↓
Observed accuracy
```

---

# 11. Data Outputs

The prototype works with structured datasets representing different stages of the pipeline, including datasets for:

* Candidate pairs
* Match results
* Matching evidence
* Evaluated matches
* National material master
* National migration mapping
* Migration summaries
* Duplicate detection
* Validation
* Standardization
* Review workflow
* Review queue
* Ground Truth
* Evaluation KPIs
* Confidence analysis
* Technical conflicts
* Risk summaries
* Audit information

This makes the prototype data-driven rather than a static UI demonstration.

---

# 12. Technology Stack

## Programming

* Python

## Application

* Streamlit

## Data Processing

* Pandas
* NumPy

## Machine Learning / Similarity

* Scikit-learn
* RapidFuzz

## Data / Enterprise Files

* CSV
* Excel / XLSX via OpenPyXL

## Visualization

* Streamlit visual components
* Plotly

## Version Control

* Git
* GitHub

## Deployment Target

* Streamlit Community Cloud

---

# 13. Project Structure

```text
material-harmonization/
│
├── app/
│   ├── streamlit_app.py
│   ├── ground_truth_engine.py
│   └── __init__.py
│
├── data/
│   └── synthetic_cpse_materials.csv
│
├── outputs/
│   ├── analytics/
│   ├── audit/
│   ├── ground_truth_labels.csv
│   ├── match_results.csv
│   ├── national_material_master.csv
│   ├── migration_mapping.csv
│   ├── review_queue.csv
│   └── ...
│
├── src/
│   ├── __init__.py
│   ├── analytics_engine.py
│   ├── attribute_extraction.py
│   ├── audit.py
│   ├── audit_trail.py
│   ├── candidate_generation.py
│   ├── config.py
│   ├── data_validation.py
│   ├── duplicate_detection.py
│   ├── evaluation.py
│   ├── harmonization.py
│   ├── matching_engine.py
│   ├── migration_mapping.py
│   ├── national_code_generation.py
│   ├── national_migration_mapping.py
│   ├── preprocessing.py
│   ├── review_approval_workflow.py
│   ├── review_queue.py
│   ├── run_pipeline.py
│   └── standardization.py
│
├── generate_data.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 14. End-to-End Prototype Flow

```text
SOURCE MATERIAL DATA
        │
        ▼
┌─────────────────────┐
│ Data Ingestion      │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Validation / Quality│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Standardization     │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Material            │
│ Understanding       │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Candidate Generation│
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ AI Matching         │
└──────────┬──────────┘
           ▼
     ┌─────┼─────────────┐
     ▼     ▼             ▼
 IDENTICAL DUPLICATE NEAR-DUPLICATE
     │     │             │
     └─────┼─────────────┘
           ▼
┌─────────────────────┐
│ Technical Conflict  │
│ Analysis            │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Human Review        │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Ground Truth        │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ Accuracy Analytics  │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ National Material   │
│ Master              │
└──────────┬──────────┘
           ▼
    ┌──────┼──────────────┐
    ▼      ▼              ▼
Migration Procurement Governance
Mapping   Intelligence   & Audit
    │      │              │
    └──────┼──────────────┘
           ▼
      SAP / ERP READY
```

---

# 15. Business Impact

A national material harmonization framework can provide a foundation for:

## Material Master Quality

* Reduced duplicate records
* More consistent descriptions
* Better technical attribute completeness
* Standardized material representation

## Procurement

* Better visibility of equivalent requirements
* Cross-CPSE material discovery
* Potential demand aggregation
* Better procurement intelligence

## Inventory

* Improved visibility of similar material holdings
* Potential reduction of unnecessary duplication
* Better understanding of common material identities

## Operations

* Faster material identification
* Easier specification comparison
* Improved master-data governance
* More consistent downstream processes

## Collaboration

CPSEs can potentially discover common or equivalent material requirements across organizational boundaries.

---

# 16. Enterprise Governance Model

The intended governance model is:

```text
SOURCE DATA
    │
    ▼
AI PROCESSING
    │
    ▼
AI RECOMMENDATION
    │
    ▼
TECHNICAL REVIEW
    │
    ▼
HUMAN APPROVAL
    │
    ▼
NATIONAL MASTER
    │
    ▼
CONTROLLED MIGRATION
    │
    ▼
ERP / SAP
```

Every important decision should remain traceable to:

* Source records
* AI recommendation
* Evidence
* Reviewer
* Review date
* Decision
* Comments
* Audit information

---

# 17. Prototype vs Production

This repository represents a **working prototype / proof of concept**, not a production national master-data platform.

## Implemented in the Prototype

* AI-assisted material matching
* Similarity analysis
* Duplicate intelligence
* Technical conflict analysis
* Standardization workflow
* National material-master structure
* CPSE migration mapping
* Review workflow
* Ground Truth workflow
* Accuracy analytics
* Audit/governance concepts
* Taxonomy/attribute dictionary
* Survivorship analysis
* Change requests
* Procurement intelligence concepts
* ERP/SAP integration readiness
* Streamlit operational dashboard

## Future Production Work

A production deployment would require additional enterprise engineering, including:

* Secure CPSE data ingestion
* Authentication and authorization
* Enterprise database
* Production ML lifecycle
* Model registry
* MLOps
* Real-time or scheduled ERP integration
* SAP APIs/connectors
* Data lineage infrastructure
* Role-based approval controls
* Enterprise security
* Encryption
* Centralized logging
* High availability
* Disaster recovery
* Performance scaling
* Production data governance
* Formal national taxonomy governance

---

# 18. Important Design Principle

The platform is intentionally designed so that:

> **AI does not unilaterally redefine the enterprise material master.**

AI assists with:

* Discovery
* Similarity
* Candidate generation
* Ranking
* Evidence organization
* Risk identification

Humans remain responsible for:

* Technical validation
* Ground Truth
* Approval
* Exception decisions
* Governance

The National Material Master becomes the governed output of that process.

---

# 19. Why This Matters

The long-term objective is not merely to build another material-search tool.

The larger vision is a common material-data foundation across CPSEs:

```text
Many CPSEs
    ↓
Many legacy codes
    ↓
Many descriptions
    ↓
Many classifications
    ↓
AI-assisted harmonization
    ↓
Human validation
    ↓
Common national material identity
    ↓
Cross-CPSE visibility
    ↓
Better procurement intelligence
    ↓
Controlled migration
    ↓
National material-data foundation
```

This provides a technical foundation for the broader concept of:

# One Nation – One Material Code

while preserving the source-system traceability required by enterprise master-data governance.

---

# 20. Current Prototype Status

**Prototype status:** Working Streamlit application

**Primary application:** `app/streamlit_app.py`

**Ground Truth engine:** `app/ground_truth_engine.py`

**Data layer:** CSV-based prototype datasets

**Interface:** Streamlit

**Deployment target:** Streamlit Community Cloud

**Version control:** GitHub

**Human validation:** Supported

**Ground Truth:** Supported

**Auditability:** Supported

**SAP connectivity:** Integration-ready architecture; live SAP connection not claimed

---

# 21. Getting Started

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
streamlit run app/streamlit_app.py
```

The application opens as a Streamlit web application.

---

# 22. Prototype Objective

The prototype demonstrates how fragmented CPSE material masters can be transformed into a governed, AI-assisted national harmonization workflow.

The intended journey is:

**Fragmented Material Data → AI Understanding → Intelligent Matching → Human Validation → Ground Truth → National Material Master → Migration → Procurement Intelligence → Enterprise Integration**

---

# Final Vision

### From fragmented material masters

```text
CPSE A → MAT-1001
CPSE B → X-4587
CPSE C → M-00982
CPSE D → PUMP-445
```

### To a common national identity

```text
NATIONAL MATERIAL CODE
        │
        ├── CPSE A : MAT-1001
        ├── CPSE B : X-4587
        ├── CPSE C : M-00982
        └── CPSE D : PUMP-445
```

with:

**AI intelligence + technical evidence + human validation + governance + traceability**

forming the foundation for a National Unified Material Master.

---

## Built as a CPSE Material Harmonization Prototype

### One Nation – One Material Code

*AI-assisted decision support with human validation, traceability and governance.*
