"""EarthScape - Big Data pages (app.py ke saath isi folder mein rakhein).

Pages: Pipeline Monitor, Live Stream, Satellite Imagery, Roles & Permissions, Alert Rules, Tableau.
MongoDB collections jo ye file khud banati hai: pipeline_jobs, pipeline_results, satellite_images,
permissions, alert_rules.   Optional secret (.streamlit/secrets.toml):  HDFS_URL = "http://localhost:9870"
"""
import copy
import datetime
import random
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

import analytics

DARK = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10))
METRICS = {"temperature": "Temperature °C", "co2": "CO₂ ppm", "aqi": "AQI",
           "humidity": "Humidity %", "rainfall": "Rainfall mm", "sea_level": "Sea level mm"}
STATIONS = ["Karachi", "Lahore", "London", "Delhi", "Dubai"]
IMG_DIR = Path(__file__).resolve().parent / "data" / "satellite"

# ------------------------------------------------------------------ permissions (Roles & Permissions page)
PERMS = {"view_dashboard": "View Dashboard", "upload_data": "Upload Data", "manage_users": "Manage Users",
         "edit_alerts": "Edit Alerts", "export_reports": "Export Reports"}
DEFAULT_PERMS = {
    "analyst": {"view_dashboard": True, "upload_data": True, "manage_users": False, "edit_alerts": True, "export_reports": True},
    "viewer": {"view_dashboard": True, "upload_data": False, "manage_users": False, "edit_alerts": False, "export_reports": False},
}
# kaunsa page kis permission se khulta hai (Manage Users / Roles sirf admin ke liye app.py mein hain)
PAGE_PERM = {"Dashboard": "view_dashboard", "Data Upload": "upload_data", "Data Management": "upload_data",
             "Satellite Imagery": "upload_data", "Pipeline Monitor": "upload_data",
             "Reports": "export_reports", "Alert Rules": "edit_alerts"}


def _matrix(db):
    d = db.permissions.find_one({"_id": "matrix"})
    saved = (d or {}).get("values") or {}
    return {r: {**DEFAULT_PERMS[r], **saved.get(r, {})} for r in DEFAULT_PERMS}


def permissions_for(db, role):
    """app.py is se pages filter karta hai.  Admin ko hamesha sab kuch milta hai."""
    if role == "admin":
        return {p: True for p in PERMS}
    return _matrix(db).get(role, {})


# ------------------------------------------------------------------ small helpers
def _card(cls, icon, label, value, sub=""):
    return (f'<div class="kpi {cls}"><div class="ico">{icon}</div><div><div class="lab">{label}</div>'
            f'<div class="val">{value}</div></div><div class="chg">{sub}</div></div>')


def _send_email(subject, body):
    """Gmail/SMTP settings secrets.toml ke [smtp] section se aati hain."""
    try:
        import smtplib
        import ssl
        from email.message import EmailMessage
        c = st.secrets["smtp"]
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = subject, c["user"], c.get("to", c["user"])
        msg.set_content(body)
        with smtplib.SMTP_SSL(c["host"], int(c["port"]), context=ssl.create_default_context(), timeout=15) as s:
            s.login(c["user"], c["password"])
            s.send_message(msg)
        return True, ""
    except Exception as e:
        return False, str(e)


def _th(db):
    d = db.thresholds.find_one({"_id": "global"})
    return (d or {}).get("values") or copy.deepcopy(analytics.DEFAULT_TH)


def _fmt_bytes(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:,.1f} {u}"
        n /= 1024


def _num(r, f):
    v = r.get(f)
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def _month(r):
    d = r.get("date")
    return d.strftime("%Y-%m") if hasattr(d, "strftime") else (str(d)[:7] if d else None)


# ================================================================== 1. PIPELINE MONITOR
def _hdfs_url():
    try:
        return (st.secrets.get("HDFS_URL") or "").rstrip("/")
    except Exception:
        return ""


def _hdfs_stats():
    url = _hdfs_url()
    if not url:
        return None
    try:
        cs = requests.get(f"{url}/webhdfs/v1/?op=GETCONTENTSUMMARY", timeout=4).json()["ContentSummary"]
        nodes = requests.get(f"{url}/jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState", timeout=4
                             ).json()["beans"][0]["NumLiveDataNodes"]
        return {"used": cs["spaceConsumed"], "files": cs["fileCount"], "nodes": nodes}
    except Exception as e:
        return {"error": str(e)}


# har job = (mapper, reducer).  mapper(record, thresholds) -> (key, value) pairs;  reducer(values) -> result
def _m_temp(r, th):
    t, m = _num(r, "temperature"), _month(r)
    return [(f"{r.get('station')} | {m}", t)] if t is not None and m else []


def _m_co2(r, th):
    v = _num(r, "co2")
    return [(str(r.get("station")), v)] if v is not None else []


def _m_breach(r, th):
    out = []
    for f in ("temperature", "co2", "aqi"):
        mx, v = (th.get(f) or {}).get("max"), _num(r, f)
        if mx is not None and v is not None and v > mx:
            out.append((f"{r.get('station')} | {f}", 1))
    return out


_avg = lambda vs: round(sum(vs) / len(vs), 2)
JOBS = {"Monthly average temperature per station": (_m_temp, _avg),
        "Average CO₂ per station": (_m_co2, _avg),
        "Threshold breaches per station": (_m_breach, sum)}


def _run_job(db, name, user):
    """Local MapReduce: map -> shuffle/sort -> reduce, result MongoDB mein."""
    t0, status, n, err = time.time(), "Completed", 0, ""
    try:
        mapper, reducer = JOBS[name]
        th, groups = _th(db), defaultdict(list)
        for r in db.records.find({}, {"_id": 0}):
            n += 1
            for k, v in mapper(r, th):
                groups[k].append(v)
        out = [{"job": name, "key": k, "value": reducer(vs)} for k, vs in sorted(groups.items())]
        db.pipeline_results.delete_many({"job": name})
        if out:
            db.pipeline_results.insert_many(out)
    except Exception as e:
        status, err = "Failed", str(e)
    db.pipeline_jobs.insert_one({"name": name, "status": status, "seconds": round(time.time() - t0, 2),
                                 "records": n, "error": err, "user": user["id"], "engine": "local",
                                 "time": datetime.datetime.utcnow()})
    return status, err


def pipeline_page(db, user):
    st.title("🐘 Hadoop Pipeline Monitor")
    h = _hdfs_stats()
    ok = bool(h) and "error" not in h
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    sub = "HDFS_URL not set in secrets" if h is None else ("WebHDFS connected" if ok else "HDFS not reachable")
    c = st.columns(4)
    c[0].markdown(_card("c", "💾", "HDFS Used", _fmt_bytes(h["used"]) if ok else "–", sub), unsafe_allow_html=True)
    c[1].markdown(_card("a", "🖥️", "Active Nodes", h["nodes"] if ok else "–", "live DataNodes"), unsafe_allow_html=True)
    c[2].markdown(_card("s", "⚙️", "Jobs Today", db.pipeline_jobs.count_documents({"time": {"$gte": today}}), "MapReduce runs"), unsafe_allow_html=True)
    c[3].markdown(_card("t", "🗃️", "Records in MongoDB", f"{db.records.estimated_document_count():,}", "climate records"), unsafe_allow_html=True)

    stages = [("📡", "Data Sources", True), ("🗄️", "HDFS Storage", ok), ("⚙️", "MapReduce Jobs", True), ("🍃", "MongoDB Results", True)]
    boxes = []
    for icon, label, on in stages:
        border = "#3ddc84" if on else "#44566b"
        boxes.append(f'<div style="flex:1;min-width:140px;text-align:center;padding:14px;border-radius:14px;'
                     f'border:1px solid {border};background:#0b2036"><div style="font-size:28px">{icon}</div><b>{label}</b></div>')
    st.write("")
    st.markdown('<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
                + '<span style="font-size:24px;color:#3ddc84">→</span>'.join(boxes) + "</div>", unsafe_allow_html=True)
    if not ok:
        st.caption("HDFS abhi connected nahi hai, isliye jobs Python ke local MapReduce engine par chal rahe hain. "
                   "Hadoop chalane ke baad secrets.toml mein HDFS_URL daal dein.")
    elif ok:
        with st.expander("HDFS root listing"):
            try:
                items = requests.get(f"{_hdfs_url()}/webhdfs/v1/?op=LISTSTATUS", timeout=4).json()["FileStatuses"]["FileStatus"]
                st.dataframe(pd.DataFrame(items)[["pathSuffix", "type", "length"]], hide_index=True)
            except Exception as e:
                st.caption(f"Could not list HDFS: {e}")

    with st.container(border=True):
        st.subheader("▶ Run a MapReduce job")
        name = st.selectbox("Job", list(JOBS))
        if st.button("Run job", type="primary"):
            status, err = _run_job(db, name, user)
            st.success("Job completed.") if status == "Completed" else st.error(err)
    with st.container(border=True):
        st.subheader("Job history")
        jobs = list(db.pipeline_jobs.find({}, {"_id": 0}).sort("time", -1).limit(10))
        if jobs:
            icons = {"Completed": "✅ Completed", "Failed": "❌ Failed"}
            st.dataframe(pd.DataFrame([{"Job": j["name"], "Status": icons.get(j["status"], j["status"]),
                                        "Duration (s)": j["seconds"], "Records": j["records"], "Engine": j.get("engine", ""),
                                        "Time": j["time"].strftime("%d %b %H:%M")} for j in jobs]),
                         width="stretch", hide_index=True)
        else:
            st.caption("No jobs yet.")
    names = db.pipeline_results.distinct("job")
    if names:
        with st.container(border=True):
            st.subheader("Job output (saved in MongoDB)")
            sel = st.selectbox("Show output of", names)
            st.dataframe(pd.DataFrame(list(db.pipeline_results.find({"job": sel}, {"_id": 0, "job": 0}))),
                         width="stretch", hide_index=True, height=260)


# ================================================================== 2. LIVE STREAM
def stream_page(db, user):
    st.title("📡 Live Data Stream")
    sim = st.toggle("Simulate sensor feed (demo)", key="sim_on", disabled=user["role"] == "viewer",
                    help="Har 3 second mein ek nayi reading MongoDB mein save hoti hai aur alert rules check hote hain.")
    if user["role"] != "viewer" and st.button("Delete simulated readings"):
        n = db.records.delete_many({"source": "simulator"}).deleted_count
        st.success(f"{n} simulated readings removed.")
    _stream_view(db, sim)


def _simulate(db):
    rec = {"date": datetime.datetime.utcnow(), "station": random.choice(STATIONS), "source": "simulator",
           "temperature": round(random.gauss(30, 6), 1), "co2": round(random.gauss(420, 25), 1),
           "aqi": round(abs(random.gauss(60, 35))), "humidity": None, "rainfall": None, "sea_level": None}
    db.records.insert_one(dict(rec))
    al = analytics.alert_docs(rec, _th(db))
    if al:
        db.alerts.insert_many(al)


@st.fragment(run_every=3)
def _stream_view(db, sim):
    if sim:
        _simulate(db)
    now = datetime.datetime.utcnow()
    t = time.perf_counter()
    db.command("ping")
    lat = (time.perf_counter() - t) * 1000
    per_sec = db.records.count_documents({"date": {"$gte": now - datetime.timedelta(seconds=60)}}) / 60
    last = db.records.find_one({}, {"date": 1}, sort=[("date", -1)])
    live = bool(last) and hasattr(last["date"], "year") and (now - last["date"]).total_seconds() < 30
    c = st.columns(3)
    c[0].markdown(_card("c", "📨", "Messages / sec", f"{per_sec:.2f}", "last 60 seconds"), unsafe_allow_html=True)
    c[1].markdown(_card("a", "⏱️", "Latency", f"{lat:.0f} <small>ms</small>", "MongoDB round trip"), unsafe_allow_html=True)
    c[2].markdown(_card("s" if live else "t", "🟢" if live else "⚪", "Stream Status", "Live" if live else "Idle",
                        "reading in last 30 s" if live else "no recent readings"), unsafe_allow_html=True)
    rows = list(db.records.find({}, {"_id": 0}).sort("date", -1).limit(60))
    with st.container(border=True):
        st.subheader("Sensor readings")
        if not rows:
            st.caption("No readings yet. Turn on the simulator or send a reading from Data Upload.")
            return
        df = pd.DataFrame(rows).iloc[::-1]
        fig = go.Figure(go.Scatter(x=list(range(len(df))), y=df["temperature"], mode="lines", name="Temperature °C",
                                   line=dict(color="#3ddc84", width=3, shape="spline")))
        fig.update_layout(height=260, xaxis=dict(visible=False), **DARK)
        st.plotly_chart(fig, width="stretch")
    with st.container(border=True):
        st.subheader("Incoming messages")
        tab = pd.DataFrame(rows[:10])
        tab["time"] = tab["date"].map(lambda d: d.strftime("%H:%M:%S") if hasattr(d, "strftime") else str(d))
        st.dataframe(tab[["station", "temperature", "co2", "aqi", "time"]], width="stretch", hide_index=True)


# ================================================================== 3. SATELLITE IMAGERY
def _image_stats(path):
    try:
        from PIL import Image
        im = Image.open(path)
        w, h = im.size
        im = im.convert("RGB")
        im.thumbnail((512, 512))
        r, g, b = np.asarray(im, dtype=float).reshape(-1, 3).mean(axis=0)
        return {"width": w, "height": h, "green_index": round((g - r) / (g + r + 1e-9), 3), "brightness": round((r + g + b) / 3, 1)}
    except Exception:
        return {}


def imagery_page(db, user):
    st.title("🛰️ Satellite Imagery")
    with st.container(border=True):
        f = st.file_uploader("Drag and drop satellite image", type=["png", "jpg", "jpeg", "tif", "tiff", "nc"])
        c = st.columns(4)
        sat = c[0].text_input("Satellite", "Sentinel-2")
        day = c[1].date_input("Date", datetime.date.today())
        region = c[2].text_input("Region", "Sindh")
        res = c[3].number_input("Resolution (m)", 1, 5000, 10)
        if f and f.name.lower().endswith((".png", ".jpg", ".jpeg")):
            st.image(f, width=360)
        if f and st.button("Upload & process", type="primary"):
            IMG_DIR.mkdir(parents=True, exist_ok=True)
            path = IMG_DIR / f"{int(time.time())}_{Path(f.name).name}"
            path.write_bytes(f.getvalue())
            stats = _image_stats(path)
            db.satellite_images.insert_one({"name": f.name, "path": str(path), "size": f.size, "satellite": sat.strip(),
                                            "date": str(day), "region": region.strip(), "resolution_m": int(res),
                                            "user": user["id"], "time": datetime.datetime.utcnow(), **stats})
            st.success("Image saved." + (f" Green index: {stats['green_index']}" if stats else " (stats are available for PNG/JPG only)"))
    imgs = list(db.satellite_images.find().sort("time", -1).limit(20))
    with st.container(border=True):
        st.subheader("Uploaded imagery")
        if not imgs:
            st.caption("No imagery yet.")
            return
        st.dataframe(pd.DataFrame([{"File": i["name"], "Satellite": i["satellite"], "Region": i["region"], "Date": i["date"],
                                    "Res (m)": i["resolution_m"], "Green index": i.get("green_index"),
                                    "Size": _fmt_bytes(i["size"])} for i in imgs]), width="stretch", hide_index=True)
        pick = st.selectbox("Preview", [i["name"] for i in imgs])
        p = Path(next(i["path"] for i in imgs if i["name"] == pick))
        if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p.exists():
            st.image(str(p), width=480)
        st.caption("Green index = (green - red) / (green + red): higher means more vegetation.")


# ================================================================== 4. ROLES & PERMISSIONS
def roles_page(db, user):
    st.title("🔐 Roles & Permissions")
    m = _matrix(db)
    st.caption("Admin always has full access. Manage Users and this page are admin-only for security. "
               "Changes apply from the user's next click.")
    rows = [{"Role": "admin", **{lab: True for lab in PERMS.values()}}]
    rows += [{"Role": r, **{lab: m[r][k] for k, lab in PERMS.items()}} for r in ("analyst", "viewer")]
    edited = st.data_editor(pd.DataFrame(rows), hide_index=True, width="stretch", key="perm_editor",
                            disabled=["Role", PERMS["manage_users"]])
    if st.button("Save permissions", type="primary"):
        vals = {row["Role"]: {k: bool(row[lab]) and k != "manage_users" for k, lab in PERMS.items()}
                for _, row in edited.iterrows() if row["Role"] != "admin"}
        db.permissions.update_one({"_id": "matrix"}, {"$set": {"values": vals}}, upsert=True)
        st.success("Permissions saved.")


# ================================================================== 5. ALERT RULES
def alert_rules_page(db, user):
    st.title("🔔 Alert Rules & Notifications")
    with st.container(border=True):
        st.subheader("Add a rule")
        with st.form("add_rule", clear_on_submit=True):
            c = st.columns(4)
            metric = c[0].selectbox("Metric", list(METRICS), format_func=METRICS.get)
            op = c[1].selectbox("Condition", [">", "<"], format_func=lambda x: "greater than" if x == ">" else "less than")
            val = c[2].number_input("Threshold", value=40.0)
            sev = c[3].selectbox("Severity", ["Low", "Medium", "High"], index=1)
            email = st.checkbox("Also notify by email (uses [smtp] from secrets.toml)")
            if st.form_submit_button("Add rule", type="primary"):
                db.alert_rules.insert_one({"metric": metric, "op": op, "threshold": float(val), "severity": sev,
                                           "email": email, "in_app": True, "enabled": True, "user": user["id"],
                                           "time": datetime.datetime.utcnow()})
                st.rerun()
    rules = list(db.alert_rules.find().sort("time", -1))
    with st.container(border=True):
        st.subheader("Active rules")
        if not rules:
            st.caption("No rules yet.")
        for r in rules:
            c = st.columns([5, 1, 1])
            c[0].write(f"**{METRICS[r['metric']]}** {r['op']} **{r['threshold']:g}**  ·  {r['severity']}"
                       + ("  ·  ✉️" if r["email"] else ""))
            on = c[1].toggle("On", value=r["enabled"], key=f"rule_on_{r['_id']}")
            if on != r["enabled"]:
                db.alert_rules.update_one({"_id": r["_id"]}, {"$set": {"enabled": on}})
                st.rerun()
            if c[2].button("Delete", key=f"rule_del_{r['_id']}"):
                db.alert_rules.delete_one({"_id": r["_id"]})
                st.rerun()
        if rules and st.button("Apply rules & scan latest data", type="primary"):
            cur = _th(db)
            for r in rules:
                if r["enabled"]:
                    cur.setdefault(r["metric"], {})["max" if r["op"] == ">" else "min"] = r["threshold"]
            db.thresholds.update_one({"_id": "global"}, {"$set": {"values": cur}}, upsert=True)
            key = lambda a: (a.get("station"), a.get("field"), a.get("time"))
            seen = {key(a) for a in db.alerts.find({}, {"station": 1, "field": 1, "time": 1})}
            sev = {"High": "critical", "Medium": "warning", "Low": "low"}
            rule_of = {r["metric"]: r for r in rules if r["enabled"]}
            new = []
            for rec in db.records.find({}, {"_id": 0}).sort("date", -1).limit(300):
                for a in analytics.alert_docs(rec, cur):
                    if key(a) in seen:
                        continue
                    seen.add(key(a))
                    if a["field"] in rule_of:
                        a["severity"] = sev[rule_of[a["field"]]["severity"]]
                    new.append(a)
            if new:
                db.alerts.insert_many(new)
            st.success(f"Rules applied as global thresholds. {len(new)} new alert(s) created.")
            mail = [a for a in new if rule_of.get(a["field"], {}).get("email")]
            if mail:
                ok, err = _send_email(f"EarthScape: {len(mail)} new alert(s)",
                                      "\n".join(f"{a['station']}: {a['title']} - {a['message']}" for a in mail[:20]))
                st.success("Email sent.") if ok else st.error(f"Email failed: {err}")


# ================================================================== 6. TABLEAU
def tableau_page(db, user):
    st.title("📈 Tableau Analytics")
    s = db.settings.find_one({"_id": "tableau"}) or {}
    with st.container(border=True):
        url = st.text_input("Tableau Public embed URL", value=s.get("url", ""),
                            help="Tableau Public > Share > Embed code mein jo src=... link hai wo paste karein.")
        if st.button("Save link") and user["role"] != "viewer":
            db.settings.update_one({"_id": "tableau"}, {"$set": {"url": url.strip()}}, upsert=True)
            st.rerun()
    if s.get("url"):
        components.iframe(s["url"], height=720, scrolling=True)
    df = analytics.load(db)
    if df.empty:
        st.info("No climate data yet.")
        return
    st.download_button("Export data for Tableau (CSV)", df.to_csv(index=False).encode("utf-8"), "earthscape_for_tableau.csv", "text/csv")
    with st.container(border=True):
        st.subheader("Built-in preview (same data)")
        f = st.columns(2)
        years = sorted(df["date"].dt.year.dropna().unique().astype(int))
        yr = f[0].selectbox("Year", ["All"] + years)
        stn = f[1].multiselect("Station", sorted(df["station"].astype(str).unique()))
        d = df if yr == "All" else df[df["date"].dt.year == yr]
        if stn:
            d = d[d["station"].astype(str).isin(stn)]
        a, b = st.columns(2)
        if "co2" in d and d["co2"].notna().any():
            g = d.groupby("station")["co2"].mean().round(1).sort_values(ascending=False).head(12)
            a.plotly_chart(go.Figure(go.Bar(x=g.index.astype(str), y=g.values, marker_color="#00bffb")).update_layout(
                height=300, title="Average CO₂ by station", **{**DARK, "margin": dict(l=10, r=10, t=40, b=10)}), width="stretch")
        if "temperature" in d and d["temperature"].notna().any():
            m = d.set_index("date")["temperature"].resample("MS").mean().dropna()
            b.plotly_chart(go.Figure(go.Scatter(x=m.index, y=m.round(2), line=dict(color="#ff9a3d", width=3))).update_layout(
                height=300, title="Temperature trend", **{**DARK, "margin": dict(l=10, r=10, t=40, b=10)}), width="stretch")
