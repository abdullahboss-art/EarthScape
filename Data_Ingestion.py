"""Data Management -> Ingestion tab.

Rules (circular import / error se bachne ke liye):
- Is file me `from Data_Ingestion import ...` kabhi mat likhna.
- Is file me st.set_page_config, sidebar ya page CSS mat likhna (app.py ye sab karta hai).
- Sirf `analytics` import karo, `app` nahi.
"""
import datetime

import pandas as pd
import streamlit as st

import analytics

ALIASES = {
    "dt": "date", "timestamp": "date", "datetime": "date", "time": "date",
    "location": "station", "city": "station", "country": "station", "site": "station",
    "temperature_c": "temperature", "temp": "temperature",
    "landaveragetemperature": "temperature",          # Berkeley Earth GlobalTemperatures.csv
    "humidity_pct": "humidity", "rainfall_mm": "rainfall",
}
KEEP = ["date", "station", "temperature", "co2", "humidity", "rainfall", "sea_level", "aqi"]
REQUIRED = ["date", "station", "temperature"]
TEMPLATE = ("date,station,temperature,co2,humidity,rainfall,sea_level,aqi\n"
            "2024-01-01,Karachi,19.5,421,55,0.0,3.1,95\n"
            "2024-02-01,Karachi,21.2,422,52,1.2,3.1,102\n")


def _get_thresholds(db):
    d = db.thresholds.find_one({"_id": "global"})
    return d["values"] if d else analytics.DEFAULT_TH


def _read_file(f):
    f.seek(0)
    name = f.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(f)
    if name.endswith(".xlsx"):
        return pd.read_excel(f)
    if name.endswith(".json"):
        return pd.read_json(f)
    raise ValueError("Unsupported file type")


def _prepare(f):
    """File padho, columns theek karo, clean karo. Returns (df, total_rows, dropped_rows)."""
    raw = _read_file(f)
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    raw = raw.rename(columns={k: v for k, v in ALIASES.items() if k in raw.columns})

    # global dataset (station column nahi) -> "Global"
    if "station" not in raw.columns and "date" in raw.columns and "temperature" in raw.columns:
        raw["station"] = "Global"

    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {list(raw.columns)}")

    raw = raw[[c for c in KEEP if c in raw.columns]].copy()
    total = len(raw)
    raw["temperature"] = pd.to_numeric(raw["temperature"], errors="coerce")
    raw = raw.dropna(subset=["temperature"])
    dropped = total - len(raw)
    if raw.empty:
        raise ValueError("No valid temperature values found in this file.")

    df = analytics.clean(raw)
    return df, total, dropped


def _split_new(db, df):
    """Wo rows alag karo jo (station, date) ke hisaab se DB me pehle se nahi hain."""
    stations = [s for s in df["station"].dropna().unique()]
    existing = set()
    for r in db.records.find({"station": {"$in": stations}}, {"_id": 0, "station": 1, "date": 1}):
        existing.add((r["station"], pd.Timestamp(r["date"])))
    dates = pd.to_datetime(df["date"])
    mask = pd.Series([(s, d) not in existing for s, d in zip(df["station"], dates)], index=df.index)
    return df[mask], int((~mask).sum())


def ingestion_page(db, user):
    st.subheader("📤 Data Ingestion Portal")
    st.caption("Upload your climate dataset (CSV, JSON or Excel). Data is checked, previewed and then saved to MongoDB.")

    # ---------- MongoDB status
    count = 0
    try:
        count = db.records.count_documents({})
        real = not type(db).__module__.startswith("mongomock")
        if real:
            st.success(f"🟢 MongoDB Connected - {count:,} records stored")
        else:
            st.warning(f"🟡 In-memory (Temporary) storage - {count:,} records")
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    # ---------- viewer: read-only
    if user["role"] == "viewer":
        st.warning("Your account is read-only (viewer). Ask an administrator for the analyst role to upload data.")
    else:
        if "ing_uploader_key" not in st.session_state:
            st.session_state["ing_uploader_key"] = 0
        if "ing_upload_success" in st.session_state:
            st.success(st.session_state.pop("ing_upload_success"))

        st.download_button("⬇️ Download CSV template", data=TEMPLATE,
                           file_name="climate_template.csv", mime="text/csv", key="ing_template_btn")

        uploaded_file = st.file_uploader(
            "Choose your climate data file",
            type=["csv", "json", "xlsx"],
            key=f"ing_file_{st.session_state['ing_uploader_key']}",
        )

        if uploaded_file is not None:
            try:
                df, total, dropped = _prepare(uploaded_file)
                new_df, dup = _split_new(db, df)
            except Exception as e:
                st.error(f"Error: {e}")
                df = None

            if df is not None:
                st.markdown("#### 🔎 Preview before saving")
                m = st.columns(4)
                m[0].metric("Rows in file", f"{total:,}")
                m[1].metric("Invalid (no temperature)", f"{dropped:,}")
                m[2].metric("Already in database", f"{dup:,}")
                m[3].metric("New rows to save", f"{len(new_df):,}")
                d = pd.to_datetime(df["date"])
                st.caption(f"Stations: {', '.join(map(str, df['station'].unique()[:8]))} · "
                           f"Date range: {d.min():%Y-%m-%d} → {d.max():%Y-%m-%d}")
                st.dataframe(df.head(10), width="stretch", hide_index=True)

                if new_df.empty:
                    st.info("Nothing new to save: all rows of this file are already in the database.")
                elif st.button(f"✅ Confirm & Save {len(new_df):,} new rows", type="primary", key="ing_upload_btn"):
                    with st.spinner("Saving data, please wait..."):
                        try:
                            n = analytics.save(db, new_df)
                            na = analytics.scan(db, new_df, _get_thresholds(db))
                            db.uploads.insert_one({
                                "user": user["id"], "name": uploaded_file.name,
                                "size": uploaded_file.size, "rows": n,
                                "time": datetime.datetime.utcnow(),
                            })
                            st.session_state["ing_upload_success"] = (
                                f"✅ Success! {n:,} new records saved ({dup:,} duplicates skipped). "
                                f"{na} new alert(s) created.")
                            st.session_state["ing_uploader_key"] += 1
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error while saving: {e}")

    # ---------- upload history
    st.divider()
    st.markdown("#### 🗂️ Upload history")
    try:
        ups = list(db.uploads.find({}, {"_id": 0}).sort("time", -1).limit(5))
        if ups:
            hist = pd.DataFrame(ups)
            hist = hist[[c for c in ["time", "name", "rows", "size"] if c in hist.columns]]
            st.dataframe(hist, width="stretch", hide_index=True)
        else:
            st.caption("No uploads yet.")
    except Exception as e:
        st.error(f"Could not load history: {e}")

    # ---------- preview of last saved rows
    if count > 0:
        if st.button("📊 View Last Uploaded Data", key="ing_preview_btn"):
            st.session_state["ing_show_preview"] = not st.session_state.get("ing_show_preview", False)
    if st.session_state.get("ing_show_preview", False):
        st.markdown("#### 📊 Recently saved records")
        try:
            rows = list(db.records.find({}, {"_id": 0}).sort("_id", -1).limit(10))
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            else:
                st.info("No records found.")
        except Exception as e:
            st.error(f"Could not load preview: {e}")