import datetime

import pandas as pd
import streamlit as st


def _summary(db):
    pipe = [{"$group": {"_id": "$station", "records": {"$sum": 1},
                        "from_date": {"$min": "$date"}, "to_date": {"$max": "$date"}}},
            {"$sort": {"_id": 1}}]
    rows = list(db.records.aggregate(pipe))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.rename(columns={"_id": "station"})


def storage_page(db, user):
    st.subheader("💾 Data Storage Management")
    st.caption("View, export and manage the data stored in your MongoDB database.")

    if "storage_msg" in st.session_state:
        st.success(st.session_state.pop("storage_msg"))

    # ---------- status
    try:
        real = not type(db).__module__.startswith("mongomock")
        total = db.records.count_documents({})
        if real:
            st.success(f"🟢 MongoDB (Permanent) - Total Records: {total:,}")
        else:
            st.warning(f"🟡 In-memory (Temporary) - Records: {total:,}")
    except Exception as e:
        st.error(f"Could not connect to database: {e}")
        return

    # ---------- summary
    st.divider()
    st.markdown("#### 📈 Storage Summary (by station)")
    try:
        summ = _summary(db)
        if summ.empty:
            st.info("No data available in the database yet.")
        else:
            st.dataframe(summ, width="stretch", hide_index=True)
    except Exception as e:
        st.error(f"Error: {e}")
        summ = pd.DataFrame()

    # ---------- latest records
    st.divider()
    st.markdown("#### 📄 View Latest Records")
    limit = st.slider("Number of records to fetch", 5, 50, 10, key="stor_limit")
    if st.button("🔍 Fetch Records", key="stor_fetch_btn"):
        try:
            rows = list(db.records.find({}, {"_id": 0}).sort("date", -1).limit(limit))
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            else:
                st.info("No records found.")
        except Exception as e:
            st.error(f"Error: {e}")

    # ---------- export
    st.divider()
    st.markdown("#### ⬇️ Export")
    if st.button("Prepare CSV of all records", key="stor_prep_csv"):
        rows = list(db.records.find({}, {"_id": 0}))
        st.session_state["stor_csv"] = pd.DataFrame(rows).to_csv(index=False).encode("utf-8") if rows else b""
    if st.session_state.get("stor_csv"):
        st.download_button("Download earthscape_records.csv", data=st.session_state["stor_csv"],
                           file_name="earthscape_records.csv", mime="text/csv", key="stor_dl_csv")

    # ---------- delete tools: admin only
    if user["role"] != "admin":
        return
    st.divider()
    with st.expander("⚠️ Danger Zone (admin only)"):
        stations = sorted(s for s in db.records.distinct("station") if s)

        st.markdown("**Delete by station**")
        if stations:
            sel = st.selectbox("Station", stations, key="stor_del_station")
            ok1 = st.checkbox(f"I understand: all records of '{sel}' will be deleted", key="stor_ok1")
            if st.button("🗑️ Delete this station's data", key="stor_del_station_btn", disabled=not ok1):
                n = db.records.delete_many({"station": sel}).deleted_count
                st.session_state["storage_msg"] = f"Deleted {n:,} records of station '{sel}'."
                st.rerun()
        else:
            st.caption("No stations.")

        st.markdown("**Delete by date range**")
        today = datetime.date.today()
        rng = st.date_input("Date range", value=(today - datetime.timedelta(days=7), today), key="stor_del_range")
        ok2 = st.checkbox("I understand: records in this date range will be deleted", key="stor_ok2")
        if st.button("🗑️ Delete this date range", key="stor_del_range_btn",
                     disabled=not (ok2 and isinstance(rng, tuple) and len(rng) == 2)):
            start = datetime.datetime.combine(rng[0], datetime.time.min)
            end = datetime.datetime.combine(rng[1], datetime.time.max)
            n = db.records.delete_many({"date": {"$gte": start, "$lte": end}}).deleted_count
            st.session_state["storage_msg"] = f"Deleted {n:,} records from {rng[0]} to {rng[1]}."
            st.rerun()

        st.markdown("**Delete everything**")
        ok3 = st.checkbox("I understand: ALL records will be permanently deleted", key="stor_ok3")
        if st.button("🗑️ Delete ALL Data", key="stor_delete_btn", disabled=not ok3):
            n = db.records.delete_many({}).deleted_count
            st.session_state["storage_msg"] = f"Deleted {n:,} records from MongoDB!"
            st.rerun()