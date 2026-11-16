import numpy as np
import pandas as pd
import streamlit as st

NUM_COLS = ["temperature", "co2", "humidity", "rainfall", "aqi"]


def processing_page(db, user):
    st.subheader("🌦️ Data Processing & Analytics")
    st.caption("Process the stored MongoDB data to find climate patterns and temperature trends.")

    if st.button("🔄 Generate Climate Patterns", type="primary", key="proc_generate_btn"):
        st.session_state["proc_ready"] = True
    if not st.session_state.get("proc_ready"):
        return

    try:
        df = pd.DataFrame(list(db.records.find({}, {"_id": 0})))
        if df.empty:
            st.warning("Database is empty. Please upload data first.")
            return

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date", "station"])
        for col in NUM_COLS:
            # NaN ko 0 nahi banate (is se averages kharab hote hain)
            df[col] = pd.to_numeric(df[col], errors="coerce") if col in df.columns else np.nan

        stations = sorted(df["station"].unique())
        c1, c2 = st.columns([3, 1])
        chosen = c1.multiselect("Stations", stations, default=stations, key="proc_stations")
        period = c2.radio("Trend by", ["Yearly", "Monthly"], horizontal=True, key="proc_period")
        df = df[df["station"].isin(chosen)]
        if df.empty:
            st.info("Select at least one station.")
            return

        patterns = df.groupby("station").agg(
            records=("temperature", "size"),
            avg_temperature=("temperature", "mean"),
            avg_co2=("co2", "mean"),
            avg_aqi=("aqi", "mean"),
            total_rainfall=("rainfall", lambda s: s.sum(min_count=1)),
            from_date=("date", "min"),
            to_date=("date", "max"),
        ).reset_index().round(2)

        st.success("✅ Data Processed Successfully!")
        st.markdown("#### 📊 Average Climate Patterns by Station")
        st.dataframe(patterns, width="stretch", hide_index=True)
        st.download_button("⬇️ Download patterns CSV", data=patterns.to_csv(index=False).encode("utf-8"),
                           file_name="climate_patterns.csv", mime="text/csv", key="proc_dl")

        st.markdown("#### 🌡️ Average Temperature by Station")
        st.bar_chart(patterns.set_index("station")["avg_temperature"])

        # ---------- temperature trend over time
        freq = "Y" if period == "Yearly" else "M"
        df["period"] = df["date"].dt.to_period(freq).dt.to_timestamp()
        trend = df.groupby(["period", "station"])["temperature"].mean().unstack("station")
        st.markdown(f"#### 📈 {period} Average Temperature Trend")
        st.line_chart(trend)

        # ---------- warming rate (yearly means, all chosen stations together)
        yearly = df.groupby(df["date"].dt.year)["temperature"].mean().dropna()
        if len(yearly) >= 3:
            slope = np.polyfit(yearly.index.values.astype(float), yearly.values, 1)[0]
            st.metric("Overall warming trend", f"{slope * 10:+.2f} °C / decade",
                      help="Linear fit on yearly average temperature of the selected stations.")
    except Exception as e:
        st.error(f"Error processing data: {e}")