"""EarthScape - Data Analytics, Reports, Profile and Settings pages.
app.py ke saath isi folder mein rakhein.  Sab data analytics.load(db) / MongoDB se aata hai.
"""
import datetime
import io
import zipfile

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from bson import ObjectId

import analytics

NUM_COLS = {"temperature": "Temperature °C", "co2": "CO₂ ppm", "aqi": "AQI",
            "humidity": "Humidity %", "rainfall": "Rainfall mm", "sea_level": "Sea level mm"}
RANGES = {"Last 12 Months": 12, "Last 5 Years": 60, "All data": 0}
DARK = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10))


# ------------------------------------------------------------------ helpers
def _kpi(cls, icon, title, value, sub):
    return (f'<div class="kpi {cls}"><div class="ico">{icon}</div><div><div class="lab">{title}</div>'
            f'<div class="val">{value}</div></div><div class="chg">{sub}</div></div>')


def _has(df, col):
    return col in df.columns and df[col].notna().any()


def _window(df, months):
    if months == 0 or df.empty:
        return df
    return df[df["date"] > df["date"].max() - pd.DateOffset(months=months)]


def _prev_window(df, months):
    if months == 0 or df.empty:
        return df.iloc[0:0]
    end = df["date"].max() - pd.DateOffset(months=months)
    return df[(df["date"] > end - pd.DateOffset(months=months)) & (df["date"] <= end)]


def _thresholds(db):
    d = db.thresholds.find_one({"_id": "global"})
    return (d or {}).get("values") or analytics.DEFAULT_TH


def _csv(df):
    return df.to_csv(index=False).encode("utf-8")


def _log_report(db, uid, kind):
    db.report_log.insert_one({"user": uid, "report": kind, "time": datetime.datetime.utcnow()})


# ------------------------------------------------------------------ data analytics
def analytics_page(db, user):
    top = st.columns([4, 1])
    top[0].title("📊 Climate Analytics")
    label = top[1].selectbox("Range", list(RANGES), label_visibility="collapsed")
    df = analytics.load(db)
    if df.empty:
        st.info("No climate data yet. Open **Data Upload** and upload a file first.")
        return
    months = RANGES[label]
    d, prev = _window(df, months), _prev_window(df, months)

    left, right = st.columns([2, 1])
    with left.container(border=True):
        st.subheader("🌡️ Temperature Trend")
        m = d.set_index("date")["temperature"].resample("MS").mean().dropna()
        if m.empty:
            st.caption("No temperature data in this range.")
        else:
            fig = go.Figure(go.Scatter(x=m.index, y=m.round(2), mode="lines+markers", name="Avg temperature",
                                       line=dict(color="#ff9a3d", width=3, shape="spline"),
                                       fill="tozeroy", fillcolor="rgba(255,154,61,.10)"))
            fig.update_layout(height=320, yaxis=dict(ticksuffix="°C"), **DARK)
            st.plotly_chart(fig, width="stretch")
    with right.container(border=True):
        st.subheader("🍩 Data Distribution")
        th = _thresholds(db)
        crit = pd.Series(False, index=d.index)
        mod = pd.Series(False, index=d.index)
        for f in ("temperature", "co2", "aqi", "rainfall"):
            mx = (th.get(f) or {}).get("max")
            if mx and _has(d, f):
                crit |= d[f] > mx
                if mx > 0:
                    mod |= d[f] > 0.8 * mx
        status = pd.Series(np.where(crit, "Critical", np.where(mod, "Moderate", "Safe")))
        counts = status.value_counts().reindex(["Safe", "Moderate", "Critical"]).fillna(0)
        pct = counts / max(counts.sum(), 1) * 100
        fig = go.Figure(go.Pie(labels=list(counts.index), values=list(counts.values), hole=0.65, sort=False,
                               marker=dict(colors=["#3ddc84", "#ffc53d", "#ff4d4f"]), textinfo="percent"))
        fig.update_layout(height=320, showlegend=True, legend=dict(orientation="h", y=-0.05),
                          annotations=[dict(text=f"{pct['Safe']:.0f}%<br>Safe", showarrow=False, font=dict(size=22))], **DARK)
        st.plotly_chart(fig, width="stretch")
        st.caption("Safe / Moderate (above 80% of an alert limit) / Critical (above the limit).")

    cards = []
    for col, cls, icon, title, unit in (("co2", "c", "☁️", "CO₂ Emissions", "ppm"), ("aqi", "a", "🍃", "Air Quality", "AQI"),
                                        ("sea_level", "s", "💧", "Sea Level", "mm"), ("temperature", "t", "🌡️", "Avg Temperature", "°C")):
        if _has(d, col):
            mean = d[col].mean()
            sub = "all data in this range"
            if months and _has(prev, col) and prev[col].mean():
                sub = f"{(mean - prev[col].mean()) / abs(prev[col].mean()) * 100:+.1f}% vs previous period"
            cards.append(_kpi(cls, icon, title, f"{mean:.1f} <small>{unit}</small>", sub))
        else:
            cards.append(_kpi(cls, icon, title, "–", "no data uploaded"))
    for column, c in zip(st.columns(4), cards):
        column.markdown(c, unsafe_allow_html=True)

    st.write("")
    a, b = st.columns(2)
    with a.container(border=True):
        st.subheader("🔗 Correlation")
        cols = [c for c in NUM_COLS if _has(d, c)]
        if len(cols) < 2:
            st.caption("Upload at least two measurements (for example temperature and CO₂) to see correlations.")
        else:
            corr = d[cols].corr()
            fig = go.Figure(go.Heatmap(z=corr.values, x=cols, y=cols, zmin=-1, zmax=1, colorscale="RdBu_r",
                                       text=corr.round(2).values, texttemplate="%{text}"))
            fig.update_layout(height=300, **DARK)
            st.plotly_chart(fig, width="stretch")
    with b.container(border=True):
        st.subheader("⚠️ Anomalies")
        if user["role"] == "viewer":
            st.caption("Available for admins and analysts.")
        else:
            try:
                an = analytics.anomalies(df)
            except Exception as e:
                an = []
                st.caption(f"Could not compute anomalies: {e}")
            st.dataframe(pd.DataFrame(an), width="stretch", hide_index=True, height=300) if an else st.caption("No anomalies found.")


# ------------------------------------------------------------------ reports
def _summary(df):
    d = _window(df, 12)
    cols = [c for c in NUM_COLS if _has(d, c)]
    if d.empty or not cols:
        return pd.DataFrame()
    g = d.set_index("date")[cols].resample("MS").agg(["mean", "min", "max"])
    g.columns = [f"{c}_{s}" for c, s in g.columns]
    g = g.round(2).reset_index()
    g["date"] = g["date"].dt.strftime("%Y-%m")
    return g.rename(columns={"date": "month"})


def _regional(db, df):
    cols = [c for c in NUM_COLS if _has(df, c)]
    if df.empty or not cols:
        return pd.DataFrame()
    g = df.groupby("station")[cols].mean().round(2)
    g["records"] = df.groupby("station").size()
    g["first_date"] = df.groupby("station")["date"].min().dt.strftime("%Y-%m-%d")
    g["last_date"] = df.groupby("station")["date"].max().dt.strftime("%Y-%m-%d")
    cmap = {s["_id"]: s.get("country", "") for s in db.stations.find()}
    g.insert(0, "country", [cmap.get(str(s).strip().lower(), "") for s in g.index])
    return g.reset_index()


def _impact(df):
    cols = [c for c in NUM_COLS if _has(df, c)]
    if df.empty or not cols:
        return pd.DataFrame()
    y = df.groupby(df["date"].dt.year)[cols].mean().round(2)
    if "temperature" in y:
        y["temperature_change"] = y["temperature"].diff().round(2)
    y.index.name = "year"
    return y.reset_index()


def reports_page(db, user):
    df = analytics.load(db)
    top = st.columns([4, 1])
    top[0].title("📄 Reports")
    top[0].caption("Generate detailed climate reports and insights.")
    if df.empty:
        st.info("No climate data yet. Open **Data Upload** and upload a file first.")
        return

    reports = [
        ("Climate Summary", "📊", "Last 12 Months", "Monthly mean, min and max of every measurement.", _summary(df), "climate_summary.csv"),
        ("Regional Analysis", "🌐", "Global Regions", "Averages for every station / region, with country.", _regional(db, df), "regional_analysis.csv"),
        ("Environmental Impact", "🍃", "CO₂ and more", "Yearly averages and yearly temperature change.", _impact(df), "environmental_impact.csv"),
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for _, _, _, _, data, fname in reports:
            z.writestr(fname, data.to_csv(index=False))
    top[1].download_button("📤 Export Report", buf.getvalue(), "earthscape_reports.zip", "application/zip",
                           key="rep_zip", on_click=_log_report, args=(db, user["id"], "All reports (ZIP)"))

    cols = st.columns(4)
    for column, (title, icon, sub, desc, data, fname) in zip(cols, reports):
        with column.container(border=True):
            st.markdown(f"### {icon}")
            st.markdown(f"**{title}**")
            st.caption(f"{sub} · {len(data):,} rows")
            st.caption(desc)
            st.download_button("Download ⬇", _csv(data), fname, "text/csv", key=f"rep_{fname}", disabled=data.empty,
                               on_click=_log_report, args=(db, user["id"], title))
    with cols[3].container(border=True):
        st.markdown("### ⚙️")
        st.markdown("**Custom Report**")
        st.caption("By Filter")
        st.caption("Choose stations, dates and measurements below.")
        st.caption("↓ Scroll down")

    st.write("")
    with st.container(border=True):
        st.subheader("⚙️ Custom Report")
        f1, f2, f3 = st.columns(3)
        stations = f1.multiselect("Stations (empty = all)", sorted(df["station"].astype(str).unique()))
        dmin, dmax = df["date"].min().date(), df["date"].max().date()
        rng = f2.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
        measures = f3.multiselect("Measurements", [c for c in NUM_COLS if _has(df, c)], default=[c for c in NUM_COLS if _has(df, c)])
        c = df
        if stations:
            c = c[c["station"].astype(str).isin(stations)]
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            c = c[(c["date"].dt.date >= rng[0]) & (c["date"].dt.date <= rng[1])]
        c = c[["date", "station"] + measures].copy()
        c["date"] = c["date"].dt.strftime("%Y-%m-%d")
        st.caption(f"{len(c):,} rows match your filter.")
        st.dataframe(c.head(200), width="stretch", hide_index=True, height=260)
        st.download_button("Download custom report ⬇", _csv(c), "custom_report.csv", "text/csv", key="rep_custom",
                           disabled=c.empty, on_click=_log_report, args=(db, user["id"], "Custom report"))


# ------------------------------------------------------------------ profile
def profile_page(db, user):
    st.title("👤 My Profile")
    u = db.users.find_one({"_id": ObjectId(user["id"])}) or {}
    name, email = u.get("name", user["name"]), u.get("email", "")
    initials = "".join(p[0] for p in name.split()[:2]).upper() or "?"

    left, right = st.columns([1.3, 1])
    with left.container(border=True):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:18px;padding:6px 0 10px">'
            f'<div style="width:96px;height:96px;border-radius:50%;display:grid;place-items:center;font-size:34px;'
            f'font-weight:700;color:#06210f;background:linear-gradient(135deg,#58df57,#00bffb)">{initials}</div>'
            f'<div><div style="font-size:24px;font-weight:700">{name}</div>'
            f'<div style="color:#3ddc84;font-weight:600">{user["role"].title()}</div>'
            f'<div style="color:#8ea6bf">{email}</div></div></div>', unsafe_allow_html=True)
        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile"):
                new = st.text_input("Full name", value=name)
                st.caption("Email aur role yahan nahi badalte (role sirf admin badal sakta hai).")
                if st.form_submit_button("Save", type="primary"):
                    if new.strip():
                        db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"name": new.strip()}})
                        st.session_state["user"]["name"] = new.strip()
                        st.rerun()
                    else:
                        st.error("Name cannot be empty")
    with right.container(border=True):
        st.subheader("Account Stats")
        stats = (
            ("a", "📄", "Total Reports", db.report_log.count_documents({"user": user["id"]}), "downloaded by you"),
            ("c", "⬆️", "Data Uploads", db.uploads.count_documents({"user": user["id"]}), "files uploaded by you"),
            ("t", "🔔", "Active Alerts", db.alerts.count_documents({"read": False}), "unread alerts"),
        )
        for cls, icon, label, value, sub in stats:
            st.markdown(_kpi(cls, icon, label, f"{value}", sub), unsafe_allow_html=True)
            st.write("")


# ------------------------------------------------------------------ settings
TIMEZONES = ["UTC", "Asia/Karachi", "Asia/Dubai", "Asia/Kolkata", "Europe/London", "Europe/Berlin",
             "America/New_York", "America/Los_Angeles", "Asia/Tokyo", "Australia/Sydney"]
LANGUAGES = ["English", "Urdu", "Hindi", "Arabic"]


def _pick(options, value):
    return options.index(value) if value in options else 0


def _save_prefs(db, uid, values):
    db.settings.update_one({"_id": uid}, {"$set": values}, upsert=True)
    st.success("Saved")


def settings_page(db, user):
    st.title("⚙️ Settings")
    s = db.settings.find_one({"_id": user["id"]}) or {}
    t_general, t_notif, t_look, t_sec, t_int = st.tabs(["General", "Notifications", "Appearance", "Security", "Integrations"])

    with t_general:
        with st.form("set_general"):
            c = st.columns(2)
            lang = c[0].selectbox("Language", LANGUAGES, index=_pick(LANGUAGES, s.get("language")))
            tz = c[1].selectbox("Time zone", TIMEZONES, index=_pick(TIMEZONES, s.get("timezone")))
            notif = st.toggle("Enable Notifications", value=s.get("notifications", True))
            auto = st.toggle("Auto-Update Data", value=s.get("auto_update", True))
            if st.form_submit_button("Save changes", type="primary"):
                _save_prefs(db, user["id"], {"language": lang, "timezone": tz, "notifications": notif, "auto_update": auto})
                st.rerun()
        st.caption("Notifications switch controls the red alert badge in the menu. "
                   "Language and time zone are saved as your preferences (the app text is English).")

    with t_notif:
        with st.form("set_notif"):
            badge = st.toggle("Show unread alerts badge in the menu", value=s.get("notifications", True))
            mail = st.toggle("Email me on critical alerts", value=s.get("email_alerts", False))
            if st.form_submit_button("Save changes", type="primary"):
                _save_prefs(db, user["id"], {"notifications": badge, "email_alerts": mail})
                st.rerun()
        st.caption("Email delivery needs an SMTP server, which is not configured, so this switch is only stored for now.")

    with t_look:
        with st.form("set_look"):
            banner = st.toggle("Show 'Together for a Greener Planet' banner in the menu", value=s.get("show_banner", True))
            st.caption("Theme: Dark (EarthScape).")
            if st.form_submit_button("Save changes", type="primary"):
                _save_prefs(db, user["id"], {"show_banner": banner})
                st.rerun()

    with t_sec:
        st.markdown(f"**Signed in as:** {user['name']}  \n**Role:** {user['role']}")
        st.caption("Passwords are stored hashed. Role changes are made by an administrator in Manage Users.")
        if st.button("Sign out of this device", key="sec_logout"):
            for k in [k for k in st.session_state if k != "splash_done"]:
                del st.session_state[k]
            st.rerun()

    with t_int:
        rows = []
        try:
            db.command("ping")
            rows.append(("MongoDB", "✅ connected"))
        except Exception as e:
            rows.append(("MongoDB", f"❌ {e}"))
        for label, coll in (("Climate records", "records"), ("Stations with location", "stations"), ("Alerts", "alerts")):
            try:
                rows.append((label, f"{db[coll].count_documents({}):,}"))
            except Exception:
                pass
        import bigdata_pages
        _h = bigdata_pages._hdfs_stats()
        rows.append(("HDFS / Hadoop", "⚪ not configured" if _h is None else ("✅ connected" if "error" not in _h else "❌ not reachable")))
        st.table(pd.DataFrame(rows, columns=["Integration", "Status"]).set_index("Integration"))
        if st.button("Test live data (Open-Meteo)", key="test_om"):
            try:
                r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
                    "latitude": 24.86, "longitude": 67.01, "current": "temperature_2m"})
                r.raise_for_status()
                st.success(f"Open-Meteo works. Karachi right now: {r.json()['current']['temperature_2m']} °C")
            except Exception as e:
                st.error(f"Open-Meteo not reachable: {e}")