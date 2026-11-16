"""Shared data, storage and helpers for the Support, Reports and Performance pages."""
import io
import time
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# Optional MongoDB. If MongoDB is not running, in-memory lists are used instead.
# ---------------------------------------------------------------------------


@st.cache_resource
def get_db():
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=800)
        client.server_info()
        return client["earthscape"]
    except Exception:
        return None


@st.cache_resource
def get_store() -> dict:
    """Process-wide in-memory state (shared across reruns and sessions)."""
    return {"feedback": [], "job_times": [], "query_times": [], "report_log": []}


FAQS = [
    ("How to upload data?",
     "Go to Data Upload, drag & drop your CSV / Excel / JSON / NetCDF file, then click Submit."),
    ("What data formats are supported?",
     "CSV, Excel (.xlsx), JSON and NetCDF are supported."),
    ("How to set up alerts?",
     "Open Alerts, set thresholds for Temperature, AQI and CO2, then click Update Thresholds."),
    ("Is my data secure?",
     "Yes. Passwords are stored hashed, access is limited by role, and database backups are encrypted."),
]

REPORT_TYPES = [
    {"key": "climate", "title": "Climate Summary", "sub": "Overview & Insights", "icon": "📄"},
    {"key": "regional", "title": "Regional Analysis", "sub": "By Region", "icon": "🗺️"},
    {"key": "environmental", "title": "Environmental Impact", "sub": "Carbon & Emissions", "icon": "🌱"},
    {"key": "custom", "title": "Custom Report", "sub": "Select Parameters", "icon": "⚙️"},
]

REGIONS = ["Europe", "Asia", "Africa", "North America", "South America", "Oceania"]

# Demo data: replace with your real MongoDB collections / uploaded data.
SAMPLE_ROWS = [
    {"region": "Europe", "temperature_c": 1.31, "co2_ppm": 421, "aqi": 55},
    {"region": "Asia", "temperature_c": 1.45, "co2_ppm": 428, "aqi": 120},
    {"region": "Africa", "temperature_c": 1.20, "co2_ppm": 417, "aqi": 64},
    {"region": "North America", "temperature_c": 1.28, "co2_ppm": 424, "aqi": 48},
    {"region": "South America", "temperature_c": 1.10, "co2_ppm": 415, "aqi": 52},
    {"region": "Oceania", "temperature_c": 1.05, "co2_ppm": 413, "aqi": 30},
]


def timed_query(fn):
    """Run fn and record its duration (ms) for the Performance Monitor."""
    start = time.perf_counter()
    result = fn()
    q = get_store()["query_times"]
    q.append((time.perf_counter() - start) * 1000)
    del q[:-30]
    return result


def build_rows(report_key: str, region: str | None = None) -> list[dict]:
    rows = timed_query(lambda: list(SAMPLE_ROWS))
    if region and region != "all":
        rows = [r for r in rows if r["region"].lower() == region.lower()]
    if report_key == "environmental":
        rows = [{"region": r["region"], "co2_ppm": r["co2_ppm"], "aqi": r["aqi"]} for r in rows]
    elif report_key == "regional":
        rows = sorted(rows, key=lambda r: r["region"])
    return rows


def make_report(key: str, fmt: str, region: str):
    """Return (bytes, mime, filename) or None if there is no data. Logs timing and history."""
    start = time.perf_counter()
    rows = build_rows(key, region)
    if not rows:
        return None
    filename = f"earthscape_{key}_{datetime.now():%Y%m%d_%H%M}"

    if fmt == "pdf":
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        title = next((r["title"] for r in REPORT_TYPES if r["key"] == key), "Full Climate Report")
        data = [list(rows[0].keys())] + [list(r.values()) for r in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d9f6e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        doc.build([Paragraph(f"EarthScape - {title}", styles["Title"]),
                   Paragraph(f"Generated {datetime.now():%Y-%m-%d %H:%M}", styles["Normal"]),
                   Spacer(1, 16), table])
        payload, mime, ext = buf.getvalue(), "application/pdf", "pdf"
    else:
        import csv
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        payload, mime, ext = out.getvalue().encode(), "text/csv", "csv"

    store = get_store()
    store["job_times"].append(time.perf_counter() - start)
    del store["job_times"][:-30]
    return payload, mime, f"{filename}.{ext}"


# Styling lives in theme.py (kept here so existing imports keep working)
from theme import inject_css  # noqa: E402,F401
