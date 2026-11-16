"""EarthScape - Alerts page (functional, MongoDB based).
app.py ke saath isi folder mein rakhein.
Use:  from Alerts_page import alerts_page   ->   alerts_page(db, user)
"""
import datetime
import html

import pandas as pd
import streamlit as st

# severity (lowercase) -> (label, color)
SEV = {
    "high": ("High", "#d92d20"), "critical": ("High", "#d92d20"), "danger": ("High", "#d92d20"),
    "medium": ("Medium", "#e8860c"), "warning": ("Medium", "#e8860c"),
    "low": ("Low", "#16a34a"),
    "info": ("Info", "#2563eb"),
}
FILTERS = ["All", "High", "Medium", "Low", "Info"]

CSS = """<style>
.al-row{display:flex;align-items:center;gap:14px;padding:11px 12px;border-radius:12px;background:#0b2036;
  border:1px solid #112f4c;min-height:56px}
.al-row.read{opacity:.55}
.al-badge{min-width:78px;text-align:center;padding:6px 10px;border-radius:8px;font-weight:700;font-size:13px;color:#fff}
.al-main{flex:1;min-width:0}
.al-main b{display:block;color:#fff;font-size:15px}
.al-main span{color:#8ea6bf;font-size:12px}
.al-time{color:#8ea6bf;font-size:13px;white-space:nowrap}
.al-dot{width:8px;height:8px;border-radius:50%;background:#00bffb;display:inline-block;margin-right:6px}
</style>"""


def _ago(t):
    s = (datetime.datetime.utcnow() - t).total_seconds()
    if s < 3600:
        return f"{max(1, int(s // 60))}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago" if s < 86400 * 90 else t.strftime("%d %b %Y")


def _sev(a):
    return SEV.get(str(a.get("severity", "info")).lower(), ("Info", "#2563eb"))


def _thresholds(db):
    d = db.thresholds.find_one({"_id": "global"})
    if d:
        return d["values"]
    try:
        import analytics
        return analytics.DEFAULT_TH
    except Exception:
        return {}


def _num(th, field, key, default=0.0):
    return float((th.get(field, {}) or {}).get(key, default) or default)


def _check(th, t, co, aqi):
    """Entered values ko thresholds se compare karke messages banata hai."""
    out = []
    tl = th.get("temperature") or {}
    if tl.get("max") and t > tl["max"]:
        out.append(f"Temperature {t:g} °C is above the limit ({tl['max']:g} °C)")
    if tl.get("min") is not None and t < tl["min"]:
        out.append(f"Temperature {t:g} °C is below the minimum ({tl['min']:g} °C)")
    cl = (th.get("co2") or {}).get("max")
    if cl and co > cl:
        out.append(f"CO₂ {co:g} ppm is above the limit ({cl:g} ppm)")
    al = (th.get("aqi") or {}).get("max")
    if al and aqi > al:
        out.append(f"AQI {aqi:g} is above the limit ({al:g})")
    return out


def alerts_page(db, user):
    st.markdown(CSS, unsafe_allow_html=True)
    flash = st.session_state.pop("al_flash", None)
    if flash:
        (st.error if flash[0] == "alert" else st.success)(flash[1])
    is_admin = user["role"] == "admin"
    can_create = user["role"] in ("admin", "analyst")
    can_edit = can_create          # analyst bhi limits badal sakta hai

    # ---------- header
    h1, h2 = st.columns([4, 1])
    h1.title("🔔 Alerts")
    unread_total = db.alerts.count_documents({"read": {"$ne": True}})
    if h2.button("Mark All as Read", width="stretch", disabled=unread_total == 0):
        db.alerts.update_many({}, {"$set": {"read": True}})
        st.rerun()

    left, right = st.columns([2.2, 1])

    # ---------- alerts list
    with left.container(border=True):
        f1, f2, f3 = st.columns([3, 2, 1.2])
        sev_filter = f1.radio("Severity", FILTERS, horizontal=True, label_visibility="collapsed")
        query = f2.text_input("Search", placeholder="Search title / station…", label_visibility="collapsed")
        only_unread = f3.toggle("Unread only")

        items = list(db.alerts.find().sort("time", -1).limit(300))
        if sev_filter != "All":
            items = [a for a in items if _sev(a)[0] == sev_filter]
        if only_unread:
            items = [a for a in items if not a.get("read")]
        if query.strip():
            q = query.strip().lower()
            items = [a for a in items if q in f"{a.get('title', '')} {a.get('station', '')} {a.get('message', '')}".lower()]

        shown = st.session_state.get("alerts_shown", 10)
        st.caption(f"{len(items)} alert(s) · {unread_total} unread")
        if not items:
            st.info("No alerts match.")

        for a in items[:shown]:
            label, color = _sev(a)
            unread = not a.get("read")
            c = st.columns([10, 1.1, 0.9] if is_admin else [10, 1.1])
            dot = '<i class="al-dot"></i>' if unread else ""
            t = a.get("time")
            c[0].markdown(
                f'<div class="al-row {"" if unread else "read"}"><div class="al-badge" style="background:{color}">{label}</div>'
                f'<div class="al-main"><b>{dot}{html.escape(str(a.get("title", "")))}</b>'
                f'<span>{html.escape(str(a.get("station", "")))} · {html.escape(str(a.get("message", "")))}</span></div>'
                f'<div class="al-time">{_ago(t) if t else ""}</div></div>', unsafe_allow_html=True)
            if c[1].button("", key=f"rd_{a['_id']}", icon=":material/done:" if unread else ":material/undo:",
                           help="Mark as read" if unread else "Mark as unread"):
                db.alerts.update_one({"_id": a["_id"]}, {"$set": {"read": unread}})
                st.rerun()
            if is_admin and c[2].button("", key=f"dl_{a['_id']}", icon=":material/delete:", help="Delete"):
                db.alerts.delete_one({"_id": a["_id"]})
                st.rerun()

        b1, b2 = st.columns(2)
        if len(items) > shown and b1.button("Show more", key="al_more"):
            st.session_state["alerts_shown"] = shown + 10
            st.rerun()
        if is_admin and b2.button("Clear read alerts", key="al_clear"):
            n = db.alerts.delete_many({"read": True}).deleted_count
            st.toast(f"{n} read alert(s) deleted")
            st.rerun()

    # ---------- enter data here (left, under alerts list)
    if can_create:
        with left.container(border=True):
            st.subheader("📤 Enter a reading")
            st.caption("Yahan data likhein. Neeche foran bata dega ke limits ke hisaab se theek hai ya alert banega.")
            th_live = _thresholds(db)
            station = st.text_input("Station", "Karachi", key="al_station")
            c = st.columns(3)
            t_ = c[0].number_input("Temperature °C", value=30.0, key="al_t")
            co_ = c[1].number_input("CO₂ ppm", value=420.0, key="al_co2")
            a_ = c[2].number_input("AQI", value=50.0, key="al_aqi")
            problems = _check(th_live, t_, co_, a_)
            if problems:
                st.warning("⚠️ Alert banega:\n\n" + "\n".join(f"- {p}" for p in problems))
            else:
                st.success("✅ Sab values limits ke andar hain, alert nahi banega.")
            if st.button("Send reading", type="primary", key="al_send"):
                if not station.strip():
                    st.error("Station is required")
                else:
                    import analytics
                    rec = {"date": datetime.datetime.utcnow(), "station": station.strip(), "temperature": t_,
                           "co2": co_, "aqi": a_, "humidity": None, "rainfall": None, "sea_level": None}
                    db.records.insert_one(dict(rec))
                    al = analytics.alert_docs(rec, th_live)
                    if al:
                        db.alerts.insert_many(al)
                        st.session_state["al_flash"] = ("alert", "ALERT: " + "; ".join(x["message"] for x in al))
                    else:
                        st.session_state["al_flash"] = ("ok", "Reading saved, no alerts.")
                    st.rerun()

    # ---------- thresholds
    with right.container(border=True):
        st.subheader("Alert Thresholds")
        th = _thresholds(db)
        with st.form("thresholds"):
            temp = st.number_input("Temperature (°C) max", value=_num(th, "temperature", "max", 35.0), disabled=not can_create)
            tmin = st.number_input("Temperature (°C) min", value=_num(th, "temperature", "min", -10.0), disabled=not can_create)
            aqi = st.number_input("AQI max", value=_num(th, "aqi", "max", 150.0), disabled=not can_create)
            co2 = st.number_input("CO₂ (ppm) max", value=_num(th, "co2", "max", 600.0), disabled=not can_create)
            rain = st.number_input("Rainfall (mm) max", value=_num(th, "rainfall", "max", 100.0), disabled=not can_create)
            if st.form_submit_button("Update Thresholds", type="primary", width="stretch", disabled=not can_create):
                new = dict(th)
                new["temperature"] = {"max": temp, "min": tmin}
                new["aqi"] = {"max": aqi}
                new["co2"] = {"max": co2}
                new["rainfall"] = {"max": rain}
                db.thresholds.update_one({"_id": "global"}, {"$set": {"values": new}}, upsert=True)
                st.success("Thresholds updated")
        if not can_create:
            st.caption("Only administrators and analysts can change thresholds.")

    # ---------- manual alert
    if can_create:
        with st.expander("➕ Create alert manually"):
            with st.form("new_alert", clear_on_submit=True):
                title = st.text_input("Title")
                station = st.text_input("Station / Region")
                message = st.text_input("Message")
                sev = st.selectbox("Severity", ["High", "Medium", "Low", "Info"])
                if st.form_submit_button("Create"):
                    if not title.strip():
                        st.error("Title is required")
                    else:
                        db.alerts.insert_one({"title": title.strip(), "station": station.strip() or "-",
                                              "message": message.strip() or "-",
                                              "severity": {"High": "critical", "Medium": "warning"}.get(sev, sev.lower()),
                                              "time": datetime.datetime.utcnow(), "read": False})
                        st.success("Alert created")
                        st.rerun()

    # ---------- data behind the alerts
    st.write("")
    with st.container(border=True):
        st.subheader("📡 Latest Readings")
        th_now = _thresholds(db)
        rows = list(db.records.find({}, {"_id": 0}).sort("date", -1).limit(15))
        if not rows:
            st.caption("No readings yet. Upload data on the Data Upload page or enter one in the form on this page.")
        else:
            rdf = pd.DataFrame(rows)

            def _hl(col):
                lim = th_now.get(col.name) or {}
                mx, mn = lim.get("max"), lim.get("min")
                out = []
                for v in col:
                    bad = pd.notna(v) and ((bool(mx) and v > mx) or (col.name == "temperature" and mn is not None and v < mn))
                    out.append("background-color:#4a1a1d;color:#ffb3b3;font-weight:700" if bad else "")
                return out

            num = [c for c in ("temperature", "co2", "aqi", "rainfall") if c in rdf.columns]
            st.dataframe(rdf.style.apply(_hl, subset=num), width="stretch", hide_index=True)
            st.caption("Red cells cross the current thresholds.")