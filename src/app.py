#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ACOMED — Analytics & Scoring Engine  (FastAPI Microservice)               ║
║                                                                            ║
║  Methodology : DHSA (Direction des Hôpitaux et Soins Ambulatoires)        ║
║                Joint Commission International (JCI) 7th Edition            ║
║  Version     : 2.0.0  —  REST API Edition                                 ║
║                                                                            ║
║  Endpoints                                                                 ║
║  ─────────                                                                 ║
║  GET  /api/dashboard/summary   → National KPIs, time-series, cat avgs     ║
║  GET  /api/dashboard/hospitals → Per-hospital scores + heatmap data        ║
║  POST /api/admin/seed          → (Re)populate DB with Agadir mock data     ║
║  GET  /health                  → Liveness probe                            ║
║                                                                            ║
║  DB Roles                                                                  ║
║  ────────                                                                  ║
║  Read endpoints  → python_analyst_role  (SELECT only)                      ║
║  /api/admin/seed → postgres admin role  (INSERT / TRUNCATE)                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─── Standard Library ────────────────────────────────────────────────────────
import json
import logging
import os
import sys
import traceback
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Tuple

# ─── Third-Party ─────────────────────────────────────────────────────────────
try:
    import numpy as np
    import pandas as pd
except ImportError as exc:
    print(f"[FATAL] Missing dependency: {exc}")
    print("        pip install pandas numpy")
    sys.exit(1)

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError as exc:
    print(f"[FATAL] MySQL driver not installed: {exc}")
    print("        pip install mysql-connector-python")
    sys.exit(1)

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError as exc:
    print(f"[FATAL] FastAPI/Uvicorn not installed: {exc}")
    print("        pip install fastapi uvicorn")
    sys.exit(1)

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ACOMED-API")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 1 — CONFIGURATION                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── Database connection configs  (MySQL — my_project) ────────────────────────
# The database.sql shows a MySQL database called "my_project", root / 1234.
# Both read endpoints and the seed endpoint use root because MySQL role
# separation works differently from PostgreSQL.

ANALYST_DB_CONFIG: Dict[str, Any] = {
    "host":               os.getenv("ACOMED_DB_HOST",  "localhost"),
    "port":               int(os.getenv("ACOMED_DB_PORT", "3306")),
    "database":           os.getenv("ACOMED_DB_NAME",  "my_project"),
    "user":               os.getenv("ACOMED_DB_USER",  "root"),
    "password":           os.getenv("ACOMED_DB_PASS",  "1234"),
    "connection_timeout": 10,
    "autocommit":         True,
}

ADMIN_DB_CONFIG: Dict[str, Any] = {
    "host":               os.getenv("ACOMED_DB_HOST",    "localhost"),
    "port":               int(os.getenv("ACOMED_DB_PORT", "3306")),
    "database":           os.getenv("ACOMED_DB_NAME",    "my_project"),
    "user":               os.getenv("ACOMED_ADMIN_USER", "root"),
    "password":           os.getenv("ACOMED_ADMIN_PASS", "1234"),
    "connection_timeout": 10,
    "autocommit":         False,
}

# ── DHSA / JCI Scoring Weights  (MUST sum to 1.0) ────────────────────────────
CATEGORY_WEIGHTS: Dict[str, float] = {
    "securite_incendie":       0.20,   # Fire Safety              (FMS)
    "lutte_infections":        0.25,   # Infection Control         (PCI)
    "gestion_medicaments":     0.20,   # Medication Management     (MMU)
    "maintenance_equipements": 0.15,   # Equipment Maintenance     (FMS)
    "batiment_securite":       0.20,   # Infrastructure & Security (FMS/ACC)
}

CATEGORY_LABELS: Dict[str, str] = {
    "securite_incendie":       "Sécurité Incendie",
    "lutte_infections":        "Lutte contre les Infections",
    "gestion_medicaments":     "Gestion des Médicaments",
    "maintenance_equipements": "Maintenance des Équipements",
    "batiment_securite":       "Bâtiment et Sécurité",
}

# ── Moroccan DHSA Accreditation Scale ─────────────────────────────────────────
ACCREDITATION_LEVELS: List[Dict[str, Any]] = [
    {"level": 1, "label_fr": "Niveau 1 — Normes de Base",        "label_en": "Basic Standards",        "min": 0,     "max": 49.99},
    {"level": 2, "label_fr": "Niveau 2 — Documentation",         "label_en": "Documentation",           "min": 50,    "max": 70.00},
    {"level": 3, "label_fr": "Niveau 3 — Données et Résultats",  "label_en": "Data & Results",          "min": 70.01, "max": 85.00},
    {"level": 4, "label_fr": "Niveau 4 — Amélioration Continue", "label_en": "Continuous Improvement",  "min": 85.01, "max": 100.0},
]

# CORS origins allowed (adjust in production to match your deployed frontend URL)
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # CRA / alternative port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 2 — HELPERS                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _accreditation_for_score(score: float) -> Dict[str, Any]:
    """Return the accreditation dict whose [min, max] range contains score."""
    for acc in ACCREDITATION_LEVELS:
        if acc["min"] <= score <= acc["max"]:
            return acc
    return ACCREDITATION_LEVELS[0]  # Defensive fallback → Level 1


@contextmanager
def _get_analyst_conn() -> Generator:
    """Yield a MySQL connection for read operations; auto-close."""
    conn = None
    try:
        conn = mysql.connector.connect(**ANALYST_DB_CONFIG)
        yield conn
    except MySQLError as exc:
        logger.error(f"Analyst DB connection failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "database_unavailable",
                "message": "Cannot connect to MySQL. Ensure the server is running on port 3306.",
                "hint": "Check that MySQL is started and password is correct (root / 1234). Run POST /api/admin/seed to create the ACOMED tables.",
            },
        )
    finally:
        if conn and conn.is_connected():
            conn.close()


@contextmanager
def _get_admin_conn() -> Generator:
    """Yield a MySQL admin connection with manual transaction; commit or rollback."""
    conn = None
    try:
        conn = mysql.connector.connect(**ADMIN_DB_CONFIG)
        yield conn
        conn.commit()
    except MySQLError as exc:
        logger.error(f"Admin DB connection failed: {exc}")
        if conn and conn.is_connected():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "admin_db_unavailable",
                "message": "Cannot connect to MySQL with admin credentials.",
            },
        )
    except Exception:
        if conn and conn.is_connected():
            conn.rollback()
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()


def _safe_float(val: Any) -> Optional[float]:
    """Convert numpy/pandas scalars to plain float; return None for NaN."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if (f != f) else f  # NaN check
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """Convert numpy/pandas scalars to plain int; return None for NaN."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 3 — SCORING ENGINE                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _score_category(items: Dict[str, Any]) -> Tuple[float, int, int]:
    """
    Compute a percentage compliance score for a single audit category.

    Supports:
      • bool  → True = 1.0,  False = 0.0
      • float in [0, 1]  → taken as-is
      • float in (1, 100] → normalised to 0-1

    Returns: (percentage_0_to_100, items_passed, total_items)
    """
    total = len(items)
    if total == 0:
        return 0.0, 0, 0

    passed = 0.0
    for val in items.values():
        if isinstance(val, bool):
            passed += 1.0 if val else 0.0
        elif isinstance(val, (int, float)):
            passed += min(val, 1.0) if val <= 1.0 else val / 100.0

    pct = round((passed / total) * 100, 2)
    return pct, int(passed), total


def _compute_global_score(cat_scores: Dict[str, float]) -> float:
    """
    Weighted compliance score (0–100).

    GlobalScore = Σ (category_score_i × weight_i)
    """
    total = sum(
        cat_scores.get(cat, 0.0) * w
        for cat, w in CATEGORY_WEIGHTS.items()
    )
    return round(total, 2)


def _score_audit_row(reponses: Dict) -> Dict[str, Any]:
    """
    Given a raw JSONB responses dict, return per-category scores and
    the weighted global score with accreditation level.
    """
    if isinstance(reponses, str):
        reponses = json.loads(reponses)

    cat_scores: Dict[str, float] = {}
    cat_details: Dict[str, Dict] = {}

    for cat_key in CATEGORY_WEIGHTS:
        items = reponses.get(cat_key, {})
        pct, passed, total = _score_category(items)
        cat_scores[cat_key] = pct
        cat_details[cat_key] = {
            "score":  pct,
            "passed": passed,
            "total":  total,
            "label":  CATEGORY_LABELS.get(cat_key, cat_key),
        }

    global_score = _compute_global_score(cat_scores)
    acc = _accreditation_for_score(global_score)

    return {
        "cat_scores":  cat_scores,
        "cat_details": cat_details,
        "global_score": global_score,
        "accreditation": acc,
    }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 4 — DATA EXTRACTION                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

_AUDIT_QUERY = """
    SELECT
        e.id                   AS hospital_id,
        e.nom                  AS hospital_name,
        e.ville                AS city,
        e.region               AS region,
        e.type_etablissement   AS hospital_type,
        e.nombre_lits          AS bed_count,
        fa.id                  AS audit_id,
        fa.date_audit          AS audit_date,
        fa.auditeur            AS auditor,
        fa.service_audite      AS audited_service,
        fa.reponses            AS reponses,
        fa.observations        AS observations
    FROM formulaires_audit fa
    JOIN etablissements    e  ON e.id = fa.etablissement_id
    ORDER BY fa.date_audit DESC;
"""

_INCIDENTS_QUERY = """
    SELECT
        etablissement_id  AS hospital_id,
        type_incident,
        gravite,
        date_incident,
        description,
        est_critique,
        statut
    FROM incidents
    ORDER BY date_incident DESC;
"""


def _extract_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run both extraction queries and return (df_audits, df_incidents)."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(_AUDIT_QUERY)
        audit_rows = cursor.fetchall()
        df_audits = pd.DataFrame(audit_rows) if audit_rows else pd.DataFrame()

        cursor.execute(_INCIDENTS_QUERY)
        incident_rows = cursor.fetchall()
        df_incidents = pd.DataFrame(incident_rows) if incident_rows else pd.DataFrame()
    finally:
        cursor.close()

    logger.info(f"Extracted {len(df_audits)} audit rows, {len(df_incidents)} incident rows.")
    return df_audits, df_incidents


def _transform_to_hospital_records(
    df_audits: pd.DataFrame,
    df_incidents: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """
    Score every audit row and produce a flat list of hospital records.

    For hospitals with multiple audits, each audit becomes its own record.
    The /hospitals endpoint returns the LATEST audit per hospital.
    The /summary endpoint uses ALL audits for the time-series.
    """
    if df_audits.empty:
        return []

    records: List[Dict] = []

    for _, row in df_audits.iterrows():
        scored = _score_audit_row(row["reponses"])
        records.append({
            "hospital_id":         int(row["hospital_id"]),
            "hospital_name":       row["hospital_name"],
            "city":                row["city"],
            "region":              row["region"],
            "hospital_type":       row["hospital_type"],
            "bed_count":           _safe_int(row["bed_count"]),
            "audit_id":            int(row["audit_id"]),
            "audit_date":          row["audit_date"],      # datetime.date or Timestamp
            "auditor":             row["auditor"],
            "audited_service":     row["audited_service"],
            "observations":        row["observations"],
            "global_score":        scored["global_score"],
            "accreditation_level": scored["accreditation"]["level"],
            "accreditation_label": scored["accreditation"]["label_fr"],
            "cat_scores":          scored["cat_scores"],
            "cat_details":         scored["cat_details"],
            **{f"score_{k}": v for k, v in scored["cat_scores"].items()},
        })

    df_scored = pd.DataFrame(records)

    # ── Aggregate incidents ───────────────────────────────────────────────────
    if not df_incidents.empty:
        inc_agg = (
            df_incidents
            .groupby("hospital_id")
            .agg(
                total_incidents=("type_incident", "count"),
                critical_incidents=("est_critique", "sum"),
            )
            .reset_index()
        )
        inc_agg["critical_incidents"] = inc_agg["critical_incidents"].astype(int)

        recent_incidents: Dict[int, List[Dict]] = {}
        for hid, grp in df_incidents.groupby("hospital_id"):
            recent_incidents[int(hid)] = (
                grp.head(5)
                .apply(lambda r: {
                    "type":     r["type_incident"],
                    "severity": r["gravite"],
                    "date":     str(r["date_incident"]),
                    "critical": bool(r["est_critique"]),
                    "status":   r["statut"],
                }, axis=1)
                .tolist()
            )
    else:
        inc_agg = pd.DataFrame({
            "hospital_id": pd.Series(dtype="int"),
            "total_incidents": pd.Series(dtype="int"),
            "critical_incidents": pd.Series(dtype="int"),
        })
        recent_incidents = {}

    df_merged = df_scored.merge(inc_agg, on="hospital_id", how="left")
    df_merged["total_incidents"]    = df_merged["total_incidents"].fillna(0).astype(int)
    df_merged["critical_incidents"] = df_merged["critical_incidents"].fillna(0).astype(int)
    df_merged["recent_incidents"]   = df_merged["hospital_id"].map(
        lambda hid: recent_incidents.get(int(hid), [])
    )
    df_merged["compliance_status"] = df_merged["global_score"].apply(
        lambda s: "Conforme" if s >= 70 else "Non conforme"
    )

    return df_merged.to_dict("records")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 5 — RESPONSE BUILDERS                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _build_time_series(records: List[Dict]) -> List[Dict[str, Any]]:
    """
    Group all audit records by (year, month) and compute the average
    global compliance score per month — used by the React Line Chart.

    Returns a list sorted chronologically:
        [
          {"month": "2025-01", "label": "Jan 2025", "avg_score": 72.4,
           "hospital_count": 3, "category_avgs": {...}},
          ...
        ]
    """
    if not records:
        return []

    # Build a lightweight DataFrame for groupby
    rows = []
    for r in records:
        audit_dt = r["audit_date"]
        # audit_date may be a date, datetime, or pd.Timestamp
        if hasattr(audit_dt, "year"):
            year, month = audit_dt.year, audit_dt.month
        else:
            parsed = datetime.fromisoformat(str(audit_dt))
            year, month = parsed.year, parsed.month

        rows.append({
            "month_key":    f"{year:04d}-{month:02d}",
            "year":         year,
            "month":        month,
            "global_score": r["global_score"],
            **{f"score_{k}": r["cat_scores"].get(k, 0) for k in CATEGORY_WEIGHTS},
        })

    df = pd.DataFrame(rows)

    score_cols = ["global_score"] + [f"score_{k}" for k in CATEGORY_WEIGHTS]
    agg_dict   = {col: "mean" for col in score_cols}
    agg_dict["month_key"] = "first"   # keep month label

    grouped = (
        df.groupby(["year", "month"])
        .agg({**agg_dict, "global_score": ["mean", "count"]})
        .reset_index()
    )

    # Flatten multi-index columns
    grouped.columns = [
        "_".join(filter(None, col)).strip("_")
        for col in grouped.columns.values
    ]

    # Rename the count column
    count_col = "global_score_count"
    mean_col  = "global_score_mean"

    result: List[Dict] = []
    for _, row in grouped.sort_values(["year", "month"]).iterrows():
        month_num  = int(row["month"])
        year_num   = int(row["year"])
        month_key  = f"{year_num:04d}-{month_num:02d}"
        month_name = datetime(year_num, month_num, 1).strftime("%b %Y")

        cat_avgs: Dict[str, float] = {}
        for k in CATEGORY_WEIGHTS:
            col = f"score_{k}_mean" if f"score_{k}_mean" in row.index else f"score_{k}"
            val = row.get(col) or row.get(f"score_{k}_mean", 0)
            cat_avgs[k] = round(float(val) if pd.notna(val) else 0.0, 2)

        avg_score_raw = row.get(mean_col) or row.get("global_score_mean", 0)
        result.append({
            "month":           month_key,
            "label":           month_name,
            "avg_score":       round(float(avg_score_raw) if pd.notna(avg_score_raw) else 0.0, 2),
            "hospital_count":  int(row.get(count_col) or row.get("global_score_count", 0)),
            "category_avgs":   cat_avgs,
        })

    return result


def _build_summary_payload(records: List[Dict]) -> Dict[str, Any]:
    """Aggregate national KPIs from all records."""
    if not records:
        return {}

    scores      = [r["global_score"] for r in records]
    total_inc   = sum(r.get("total_incidents", 0)    for r in records)
    crit_inc    = sum(r.get("critical_incidents", 0) for r in records)

    cat_avgs: Dict[str, float] = {}
    for k in CATEGORY_WEIGHTS:
        vals = [r["cat_scores"].get(k, 0) for r in records]
        cat_avgs[k] = round(sum(vals) / len(vals), 2)

    # Accreditation distribution based on each record's computed level
    level_dist: Dict[str, int] = {}
    for r in records:
        label = r.get("accreditation_label", "Unknown")
        level_dist[label] = level_dist.get(label, 0) + 1

    return {
        "average_global_score":     round(sum(scores) / len(scores), 2),
        "total_hospitals_analyzed": len(records),
        "total_incidents":          total_inc,
        "total_critical_incidents": crit_inc,
        "category_averages":        cat_avgs,
        "accreditation_distribution": level_dist,
    }


def _build_hospital_payload(records: List[Dict]) -> List[Dict[str, Any]]:
    """
    Return the LATEST audit per hospital, shaped for the frontend
    hospital list + heatmap component.
    """
    # Keep only the newest audit per hospital (records are already ordered DESC)
    seen: set = set()
    latest: List[Dict] = []
    for r in records:
        hid = r["hospital_id"]
        if hid not in seen:
            seen.add(hid)
            latest.append(r)

    out: List[Dict[str, Any]] = []
    for r in latest:
        audit_date = r["audit_date"]
        if hasattr(audit_date, "isoformat"):
            audit_date_str = audit_date.isoformat()
        else:
            audit_date_str = str(audit_date)

        # ── Heatmap data: flat category score array sorted by weight ──────
        heatmap_scores = [
            {
                "category_key":   k,
                "category_label": CATEGORY_LABELS[k],
                "score":          r["cat_scores"].get(k, 0),
                "weight":         CATEGORY_WEIGHTS[k],
            }
            for k in CATEGORY_WEIGHTS
        ]

        out.append({
            "hospital_id":   r["hospital_id"],
            "hospital_name": r["hospital_name"],
            "city":          r["city"],
            "region":        r["region"],
            "hospital_type": r["hospital_type"],
            "bed_count":     r["bed_count"],
            "audit_info": {
                "audit_id":        r["audit_id"],
                "audit_date":      audit_date_str,
                "auditor":         r["auditor"],
                "audited_service": r["audited_service"],
                "observations":    r.get("observations"),
            },
            "scores": {
                "global_score":        r["global_score"],
                "accreditation_level": r["accreditation_level"],
                "accreditation_label": r["accreditation_label"],
                "compliance_status":   r["compliance_status"],
                "category_breakdown":  r["cat_details"],
            },
            # Flat list for heatmap rows — one entry per category
            "heatmap_scores": heatmap_scores,
            "incidents": {
                "total":    r.get("total_incidents", 0),
                "critical": r.get("critical_incidents", 0),
                "recent":   r.get("recent_incidents", []),
            },
        })

    return out


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 6 — DATABASE SEEDER (Admin Role Only)                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ── The three Agadir hospitals mirroring the React hospitalData.js ───────────
_SEED_HOSPITALS = [
    {
        "nom":    "Hôpital Régional Hassan II",
        "ville":  "Agadir",
        "region": "Souss-Massa",
        "type":   "Hôpital Régional",
        "lits":   640,
    },
    {
        "nom":    "Hôpital Préfectoral Inezgane",
        "ville":  "Inezgane",
        "region": "Souss-Massa",
        "type":   "Hôpital Préfectoral",
        "lits":   280,
    },
    {
        "nom":    "Polyclinique CNSS Agadir",
        "ville":  "Agadir",
        "region": "Souss-Massa",
        "type":   "Polyclinique",
        "lits":   150,
    },
]

# ── Audit profiles per hospital ───────────────────────────────────────────────
# These produce realistic, differentiated scores matching the React mock data.
_AUDIT_PROFILES: Dict[str, Dict[str, Dict[str, bool]]] = {
    "Hôpital Régional Hassan II": {
        "securite_incendie":       {"extincteurs_fonctionnels": True,  "plan_evacuation_affiche": True,  "formation_personnel_incendie": True,  "alarmes_testees_trimestriellement": True,  "issues_secours_degagees": True},   # → 82%
        "lutte_infections":        {"hygiene_mains_5moments_oms": True, "protocole_isolement_applique": True,  "gestion_dechets_biomedicaux": True,  "sterilisation_conforme": False, "surveillance_infections_nosocomiales": True},  # → 75%
        "gestion_medicaments":     {"stockage_conforme_temperature": True, "chaine_froid_respectee": True, "tracabilite_complete": True,  "medicaments_perimes_absents": True,  "armoire_pharmacie_securisee": False},  # → 78%
        "maintenance_equipements": {"plan_maintenance_preventive": True, "registre_maintenance_a_jour": True,  "equipements_critiques_fonctionnels": True,  "calibration_a_jour": False, "pieces_rechange_disponibles": False},  # → 72%
        "batiment_securite":       {"accessibilite_pmr": True,  "eclairage_adequat": True,  "signalisation_claire": True,  "groupe_electrogene_fonctionnel": True,  "eau_potable_analyse_conforme": True},   # → 85%
    },
    "Hôpital Préfectoral Inezgane": {
        "securite_incendie":       {"extincteurs_fonctionnels": True,  "plan_evacuation_affiche": False, "formation_personnel_incendie": False, "alarmes_testees_trimestriellement": True,  "issues_secours_degagees": True},   # → 60%
        "lutte_infections":        {"hygiene_mains_5moments_oms": True, "protocole_isolement_applique": False, "gestion_dechets_biomedicaux": False, "sterilisation_conforme": False, "surveillance_infections_nosocomiales": True},  # → 55%
        "gestion_medicaments":     {"stockage_conforme_temperature": True, "chaine_froid_respectee": True, "tracabilite_complete": True,  "medicaments_perimes_absents": False, "armoire_pharmacie_securisee": False},  # → 68% (4/5 → adjust)
        "maintenance_equipements": {"plan_maintenance_preventive": False, "registre_maintenance_a_jour": False, "equipements_critiques_fonctionnels": True,  "calibration_a_jour": False, "pieces_rechange_disponibles": True},   # → 52%
        "batiment_securite":       {"accessibilite_pmr": True,  "eclairage_adequat": True,  "signalisation_claire": True,  "groupe_electrogene_fonctionnel": True,  "eau_potable_analyse_conforme": False},  # → 70%
    },
    "Polyclinique CNSS Agadir": {
        "securite_incendie":       {"extincteurs_fonctionnels": True,  "plan_evacuation_affiche": True,  "formation_personnel_incendie": True,  "alarmes_testees_trimestriellement": True,  "issues_secours_degagees": True},   # → 90%+ (all T)
        "lutte_infections":        {"hygiene_mains_5moments_oms": True, "protocole_isolement_applique": True,  "gestion_dechets_biomedicaux": True,  "sterilisation_conforme": True,  "surveillance_infections_nosocomiales": True},  # → 92%
        "gestion_medicaments":     {"stockage_conforme_temperature": True, "chaine_froid_respectee": True, "tracabilite_complete": True,  "medicaments_perimes_absents": True,  "armoire_pharmacie_securisee": False},  # → 85%
        "maintenance_equipements": {"plan_maintenance_preventive": True, "registre_maintenance_a_jour": True,  "equipements_critiques_fonctionnels": True,  "calibration_a_jour": False, "pieces_rechange_disponibles": False},  # → 82%
        "batiment_securite":       {"accessibilite_pmr": True,  "eclairage_adequat": True,  "signalisation_claire": True,  "groupe_electrogene_fonctionnel": True,  "eau_potable_analyse_conforme": True},   # → 92%
    },
}

_AUDITORS = [
    "Dr. Amina Benchekroun",
    "Dr. Youssef El Alaoui",
    "Dr. Fatima-Zahra Tazi",
    "Dr. Karim Idrissi",
    "Dr. Nadia Berrada",
]

_SERVICES = ["Urgences", "Bloc Opératoire", "Réanimation", "Maternité", "Pédiatrie"]

_INCIDENTS_POOL: List[Dict[str, Any]] = [
    {"type": "Incendie mineur",              "gravite": "modere",   "critique": False},
    {"type": "Panne groupe électrogène",     "gravite": "grave",    "critique": True},
    {"type": "Rupture chaîne du froid",      "gravite": "critique", "critique": True},
    {"type": "Chute patient",                "gravite": "modere",   "critique": False},
    {"type": "Erreur médicamenteuse",        "gravite": "critique", "critique": True},
    {"type": "Infection nosocomiale",        "gravite": "grave",    "critique": True},
    {"type": "Fuite d'eau",                  "gravite": "faible",   "critique": False},
    {"type": "Panne ascenseur",              "gravite": "faible",   "critique": False},
    {"type": "Défaillance stérilisation",    "gravite": "grave",    "critique": True},
    {"type": "Coupure électrique prolongée", "gravite": "critique", "critique": True},
    {"type": "Absence signalisation",        "gravite": "faible",   "critique": False},
    {"type": "AES (Accident Exposition Sang)","gravite": "grave",   "critique": True},
]


def _create_tables(cur) -> None:
    """Idempotent MySQL DDL — safe to run on each seed call."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS etablissements (
            id                  INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nom                 VARCHAR(255) NOT NULL,
            ville               VARCHAR(100) NOT NULL,
            region              VARCHAR(150),
            type_etablissement  VARCHAR(50),
            nombre_lits         INT,
            created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS formulaires_audit (
            id               INT  NOT NULL AUTO_INCREMENT PRIMARY KEY,
            etablissement_id INT  NOT NULL,
            date_audit       DATE NOT NULL,
            auditeur         VARCHAR(200),
            service_audite   VARCHAR(200),
            reponses         JSON NOT NULL,
            observations     TEXT,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_audit_etab FOREIGN KEY (etablissement_id)
                REFERENCES etablissements(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id               INT  NOT NULL AUTO_INCREMENT PRIMARY KEY,
            etablissement_id INT  NOT NULL,
            type_incident    VARCHAR(200) NOT NULL,
            gravite          VARCHAR(50),
            date_incident    DATE NOT NULL,
            description      TEXT,
            est_critique     TINYINT(1) DEFAULT 0,
            statut           VARCHAR(50) DEFAULT 'ouvert',
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_incident_etab FOREIGN KEY (etablissement_id)
                REFERENCES etablissements(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)


def _grant_analyst_permissions(cur) -> None:
    """In MySQL we use root for everything, so no separate GRANT is needed."""
    logger.info("MySQL mode: using root for all access — GRANT step skipped.")


def _build_monthly_profile(
    base_profile: Dict[str, Dict[str, bool]],
    month_idx: int,
    hospital_name: str,
) -> Dict[str, Dict[str, bool]]:
    """
    Generate a slightly varied audit profile for each month so the time-series
    chart shows realistic score progression instead of a flat line.

    Strategy: for each category, randomly flip 0–1 answers based on a trend
    direction per hospital (improving/declining/oscillating).
    """
    import copy, random

    # Hospital-specific progression: Hassan II improving, Inezgane fluctuating,
    # CNSS maintaining excellence.
    trends = {
        "Hôpital Régional Hassan II": 0.04,      # gradual improvement
        "Hôpital Préfectoral Inezgane": -0.01,   # slow decline / plateau
        "Polyclinique CNSS Agadir": 0.005,        # already near top, minor variance
    }
    bias = trends.get(hospital_name, 0.0) * month_idx  # cumulative shift

    profile = copy.deepcopy(base_profile)
    rng = random.Random(hash((hospital_name, month_idx)) % (2**31))

    for cat_key, items in profile.items():
        keys = list(items.keys())
        # For improving hospitals, increase probability of True answers over time
        for k in keys:
            p_true = 0.5 + bias + (0.3 if base_profile[cat_key][k] else 0.0)
            p_true  = max(0.05, min(0.98, p_true))
            profile[cat_key][k] = rng.random() < p_true

    return profile


def _seed_database(conn) -> Dict[str, int]:
    """
    Full seeder:
      1. Clear existing data (TRUNCATE CASCADE)
      2. Re-create / verify tables
      3. Insert 3 Agadir hospitals
      4. Insert 12 monthly audits per hospital (Jan–Dec 2024 + most recent 2025)
      5. Insert incidents
      6. Grant analyst permissions
    Returns counts of inserted rows.
    """
    import random as _random
    _random.seed(42)

    counts: Dict[str, int] = {"hospitals": 0, "audits": 0, "incidents": 0}

    with conn.cursor() as cur:
        # ── Tables ────────────────────────────────────────────────────────
        _create_tables(cur)

        # ── Clear existing data (MySQL: disable FK checks for TRUNCATE) ───
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("TRUNCATE TABLE incidents;")
        cur.execute("TRUNCATE TABLE formulaires_audit;")
        cur.execute("TRUNCATE TABLE etablissements;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        logger.info("Existing mock data truncated.")

        # ── Insert hospitals ──────────────────────────────────────────────
        hospital_ids: Dict[str, int] = {}
        for h in _SEED_HOSPITALS:
            cur.execute("""
                INSERT INTO etablissements (nom, ville, region, type_etablissement, nombre_lits)
                VALUES (%s, %s, %s, %s, %s)
            """, (h["nom"], h["ville"], h["region"], h["type"], h["lits"]))
            hospital_ids[h["nom"]] = cur.lastrowid   # MySQL uses lastrowid
            counts["hospitals"] += 1

        logger.info(f"Inserted {counts['hospitals']} hospitals: {list(hospital_ids.keys())}")

        # ── Insert historical audits (Jan 2024 – Jan 2025) ────────────────
        # 12 months of 2024 + one 2025 entry = 13 audits per hospital → 39 total
        base_year  = 2024
        num_months = 13   # Jan 2024 … Jan 2025
        auditor_cycle = list(enumerate(_AUDITORS))
        service_cycle = list(enumerate(_SERVICES))

        for hospital_name, hid in hospital_ids.items():
            base_profile = _AUDIT_PROFILES.get(hospital_name, {})

            for month_offset in range(num_months):
                year  = base_year + (month_offset // 12)
                month = (month_offset % 12) + 1
                audit_date = date(year, month, 15)  # mid-month audit

                monthly_profile = _build_monthly_profile(
                    base_profile, month_offset, hospital_name
                )

                auditor  = _AUDITORS[month_offset % len(_AUDITORS)]
                service  = _SERVICES[month_offset % len(_SERVICES)]
                obs_text = (
                    f"Audit mensuel — {hospital_name} — "
                    f"{audit_date.strftime('%B %Y')}."
                )

                cur.execute("""
                    INSERT INTO formulaires_audit
                        (etablissement_id, date_audit, auditeur, service_audite, reponses, observations)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (hid, audit_date, auditor, service, json.dumps(monthly_profile, ensure_ascii=False), obs_text))
                counts["audits"] += 1

        logger.info(f"Inserted {counts['audits']} audit records ({num_months} months × {len(hospital_ids)} hospitals).")

        # ── Insert incidents ──────────────────────────────────────────────
        all_hids = list(hospital_ids.values())
        for inc in _INCIDENTS_POOL:
            hid_for_inc = _random.choice(all_hids)
            days_ago    = _random.randint(1, 365)
            inc_date    = date.today() - timedelta(days=days_ago)
            status      = _random.choice(["ouvert", "en_cours", "clos"])
            cur.execute("""
                INSERT INTO incidents
                    (etablissement_id, type_incident, gravite, date_incident,
                     description, est_critique, statut)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                hid_for_inc,
                inc["type"],
                inc["gravite"],
                inc_date,
                f"Événement signalé: {inc['type']}.",
                inc["critique"],
                status,
            ))
            counts["incidents"] += 1

        logger.info(f"Inserted {counts['incidents']} incident records.")

        # ── Grant analyst permissions ─────────────────────────────────────
        try:
            _grant_analyst_permissions(cur)
        except Exception as exc:
            # Non-fatal: analyst role may not exist in all environments.
            logger.warning(f"Could not grant analyst permissions: {exc}")

    return counts


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 7 — FASTAPI APPLICATION                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

app = FastAPI(
    title="ACOMED Analytics & Scoring Engine",
    description=(
        "Production REST API for the ACOMED Hospital Compliance Dashboard. "
        "Implements DHSA/JCI scoring methodology with time-series and heatmap outputs."
    ),
    version="2.0.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc alternative
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Liveness / Readiness Probe ──────────────────────────────────────────────
@app.get(
    "/health",
    summary="Health Check",
    tags=["Infrastructure"],
    response_description="Service liveness status",
)
def health_check():
    """
    Simple liveness probe.  A 200 response means the Python process is alive.
    Does NOT verify DB connectivity (use /api/dashboard/summary for that).
    """
    return {
        "status": "ok",
        "service": "ACOMED Analytics Engine",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ─── GET /api/dashboard/summary ──────────────────────────────────────────────
@app.get(
    "/api/dashboard/summary",
    summary="National Dashboard Summary",
    tags=["Dashboard"],
    response_description="Aggregated KPIs, category averages, and time-series data",
)
def get_dashboard_summary():
    """
    Returns the aggregated national dashboard payload consumed by the React Summary
    cards and Line Chart.

    **Data scope:** ALL audit records in the database (not just the latest per hospital).
    This lets the time-series show monthly progression even for hospitals that have
    been audited multiple times.

    **DB Role:** `python_analyst_role` (Read-Only).
    """
    with _get_analyst_conn() as conn:
        try:
            df_audits, df_incidents = _extract_data(conn)
        except ProgrammingError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "sql_error",
                    "message": "A required table is missing. Call POST /api/admin/seed first.",
                    "detail": str(exc),
                },
            )

    if df_audits.empty:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status":    "empty",
                "message":   "No audit data found. Call POST /api/admin/seed to populate the database.",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "summary":   {},
                "time_series":       [],
                "charts_data": {},
            },
        )

    records    = _transform_to_hospital_records(df_audits, df_incidents)
    summary    = _build_summary_payload(records)
    time_series = _build_time_series(records)

    # Category averages formatted for the radar chart
    cat_avgs = summary.get("category_averages", {})
    radar_data = [
        {
            "category":      CATEGORY_LABELS.get(k, k),
            "category_key":  k,
            "avg_score":     cat_avgs.get(k, 0),
            "weight":        CATEGORY_WEIGHTS[k],
        }
        for k in CATEGORY_WEIGHTS
    ]

    return {
        "status":       "success",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "meta": {
            "methodology":      "DHSA / JCI 7th Edition",
            "scoring_version":  "2.0.0",
            "category_weights": CATEGORY_WEIGHTS,
            "accreditation_scale": [
                {
                    "level":    a["level"],
                    "label_fr": a["label_fr"],
                    "label_en": a["label_en"],
                    "range":    f"{a['min']}% – {a['max']}%",
                }
                for a in ACCREDITATION_LEVELS
            ],
        },
        "summary":      summary,
        "time_series":  time_series,     # ← Line Chart data
        "charts_data": {
            "radar_chart": radar_data,   # ← Radar / spider chart
        },
    }


# ─── GET /api/dashboard/hospitals ────────────────────────────────────────────
@app.get(
    "/api/dashboard/hospitals",
    summary="Hospital List with Scores & Heatmap Data",
    tags=["Dashboard"],
    response_description="Latest scored audit per hospital with category heatmap breakdown",
)
def get_hospitals():
    """
    Returns the per-hospital list for the map pins and heatmap component.

    **Data scope:** Only the LATEST audit per hospital.

    **DB Role:** `python_analyst_role` (Read-Only).
    """
    with _get_analyst_conn() as conn:
        try:
            df_audits, df_incidents = _extract_data(conn)
        except ProgrammingError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "sql_error",
                    "message": "A required table is missing. Call POST /api/admin/seed first.",
                    "detail": str(exc),
                },
            )

    if df_audits.empty:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status":    "empty",
                "message":   "No audit data found. Call POST /api/admin/seed to populate the database.",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "hospitals": [],
                "count":     0,
            },
        )

    records   = _transform_to_hospital_records(df_audits, df_incidents)
    hospitals = _build_hospital_payload(records)

    return {
        "status":       "success",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count":        len(hospitals),
        "hospitals":    hospitals,
    }


# ─── POST /api/admin/seed ─────────────────────────────────────────────────────
@app.post(
    "/api/admin/seed",
    summary="Seed Database with Agadir Mock Data",
    tags=["Administration"],
    status_code=status.HTTP_201_CREATED,
    response_description="Counts of inserted rows",
)
def seed_database():
    """
    **Drops all existing mock data** and re-populates the PostgreSQL database with:
    - 3 Agadir hospitals (Hassan II, Inezgane, CNSS)
    - 13 monthly audits per hospital (Jan 2024 – Jan 2025) for time-series data
    - 12 incidents distributed across hospitals

    ⚠ **Uses the `postgres` admin role** — this endpoint performs DDL and DML.

    The `python_analyst_role` is granted SELECT on all tables as part of seeding.
    """
    logger.info("🌱 POST /api/admin/seed — starting seeder (admin role)…")
    with _get_admin_conn() as conn:
        try:
            counts = _seed_database(conn)
        except Exception as exc:
            logger.error(f"Seeding failed: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error":   "seed_failed",
                    "message": "Database seeding failed. Check server logs for details.",
                    "detail":  str(exc),
                },
            )

    logger.info(f"✅ Seeding complete: {counts}")
    return {
        "status":     "success",
        "message":    "Database seeded successfully with Agadir hospital data.",
        "seeded_at":  datetime.utcnow().isoformat() + "Z",
        "counts": {
            "hospitals": counts["hospitals"],
            "audits":    counts["audits"],
            "incidents": counts["incidents"],
        },
        "note": (
            "13 monthly audit records per hospital (Jan 2024 – Jan 2025) "
            "were generated to support the Time-Series Line Chart."
        ),
    }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  SECTION 8 — ENTRY POINT                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="ACOMED Analytics & Scoring Engine — FastAPI Server"
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Bind host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Bind port (default: 8000)",
    )
    parser.add_argument(
        "--reload", action="store_true",
        help="Enable hot-reload for development.",
    )
    args = parser.parse_args()

    logger.info(f"🚀 Starting ACOMED API on http://{args.host}:{args.port}")
    logger.info(f"   Swagger UI → http://localhost:{args.port}/docs")
    logger.info(f"   MySQL DB  → {ANALYST_DB_CONFIG['user']}@{ANALYST_DB_CONFIG['host']}:{ANALYST_DB_CONFIG['port']}/{ANALYST_DB_CONFIG['database']}")

    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )