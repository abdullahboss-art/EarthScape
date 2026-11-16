"""Dashboard.py - EarthScape live dashboard (v3: active notification bell + har card se page par jump).
Saara data database se live aata hai, koi static value nahi.

app.py me:  from Dashboard import dashboard_page
"""
import datetime
import html
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analytics

# ------------------------------------------------------------------ settings
LIVE_SECONDS = 10      # itne second baad dashboard khud refresh hoga (toggle se band bhi ho sakta hai)
NAV_KEY = "page"       # Sidebar_nav ki session_state key (go_to() yahi set karta hai)
Z_LIMIT = 2.5          # fallback anomaly detection: value apne station ke average se itne std door ho to anomaly

# Station ke naam se map location (sirf fallback; pehle records ke lat/lon ya db.stations use hota hai)
CITY_COORDS = {
    "karachi": (24.86, 67.01), "lahore": (31.52, 74.36), "islamabad": (33.68, 73.05),
    "peshawar": (34.01, 71.58), "quetta": (30.18, 66.99), "multan": (30.16, 71.52),
    "faisalabad": (31.42, 73.08), "hyderabad": (25.40, 68.37), "rawalpindi": (33.57, 73.02),
    "delhi": (28.61, 77.21), "mumbai": (19.08, 72.88), "dhaka": (23.81, 90.41),
    "dubai": (25.20, 55.27), "riyadh": (24.71, 46.68), "istanbul": (41.01, 28.98),
    "cairo": (30.04, 31.24), "lagos": (6.52, 3.38), "nairobi": (-1.29, 36.82),
    "cape town": (-33.92, 18.42), "london": (51.51, -0.13), "paris": (48.86, 2.35),
    "berlin": (52.52, 13.40), "moscow": (55.76, 37.62), "beijing": (39.90, 116.41),
    "tokyo": (35.68, 139.69), "bangkok": (13.76, 100.50), "singapore": (1.35, 103.82),
    "jakarta": (-6.21, 106.85), "sydney": (-33.87, 151.21), "new york": (40.71, -74.01),
    "los angeles": (34.05, -118.24), "toronto": (43.65, -79.38), "mexico city": (19.43, -99.13),
    "sao paulo": (-23.55, -46.63), "buenos aires": (-34.60, -58.38),
}
UNITS = {"temperature": "°C", "co2": " ppm", "aqi": ""}
NAMES = {"temperature": "Temperature", "co2": "CO₂", "aqi": "AQI"}

CSS = """<style>
/* ---------- cards ---------- */
[data-testid=stVerticalBlockBorderWrapper]{transition:border-color .25s, box-shadow .25s, transform .25s}
[data-testid=stVerticalBlockBorderWrapper]:hover{border-color:#2a6fa8!important;box-shadow:0 0 0 1px rgba(0,191,251,.15),0 10px 30px rgba(0,120,255,.12)}
.es-h{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:700;color:#fff;margin:2px 0 10px}
.es-h .dot{width:9px;height:9px;border-radius:50%;background:linear-gradient(135deg,#58df57,#00bffb);box-shadow:0 0 10px #00bffb}
.es-h .r{margin-left:auto;font-size:11px;font-weight:600;color:#8ea6bf;background:#0b2036;border:1px solid #173553;padding:2px 10px;border-radius:12px}
/* ---------- top bar ---------- */
.es-top{display:flex;justify-content:flex-end;align-items:center;gap:16px;height:40px}
.es-user{display:flex;align-items:center;gap:8px;background:#0b2036;border:1px solid #173553;border-radius:24px;padding:4px 14px 4px 5px}
.es-user i{width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#58df57,#00bffb);display:grid;place-items:center;font-style:normal;font-weight:800;color:#06210f}
/* ---------- notification bell (chota gol icon + red badge) ---------- */
.st-key-es_bell_off,.st-key-es_bell_on{position:relative;width:46px;margin-left:auto;overflow:visible}
.st-key-es_bell_off button,.st-key-es_bell_on button{width:46px;min-width:46px;height:42px;padding:0;border-radius:50%;background:#0b2036;
  border:1px solid #173553;color:#fff;font-size:20px;justify-content:center}
.st-key-es_bell_off button svg,.st-key-es_bell_on button svg,
.st-key-es_bell_off button [data-testid=stIconMaterial],.st-key-es_bell_on button [data-testid=stIconMaterial]{display:none!important}
.st-key-es_bell_off button:hover,.st-key-es_bell_on button:hover{border-color:#00bffb!important;background:#0f2c48}
.st-key-es_bell_on button{border-color:#ff3b4a!important;box-shadow:0 0 12px rgba(255,59,74,.45)}
.st-key-es_bell_on::after{content:var(--n);position:absolute;top:-6px;right:-4px;min-width:20px;height:20px;padding:0 5px;border-radius:10px;
  background:#ff3b4a;color:#fff;font-size:11px;font-weight:800;display:grid;place-items:center;pointer-events:none;
  box-shadow:0 0 8px #ff3b4a;animation:es-pulse 1.4s infinite}
/* ---------- jump / link buttons ---------- */
[class*="st-key-es_go_"] button{background:transparent;border:1px solid #173553;color:#8ea6bf;font-size:12px;min-height:0;padding:.2rem .8rem;border-radius:10px}
[class*="st-key-es_go_"] button:hover{border-color:#00bffb;color:#fff;background:rgba(0,191,251,.10)}
/* ---------- clickable alert / notification rows ---------- */
[class*="st-key-es_al_"] button,[class*="st-key-es_bn_"] button{justify-content:flex-start;text-align:left;background:#0b2036;border:1px solid #112f4c;
  border-left:3px solid #ff4d5a;color:#e8f1fb;border-radius:12px;padding:.55rem .8rem;font-size:13px}
[class*="st-key-es_al_"] button div,[class*="st-key-es_bn_"] button div{justify-content:flex-start;text-align:left}
[class*="st-key-es_al_warning"] button,[class*="st-key-es_bn_warning"] button{border-left-color:#ffb020}
[class*="st-key-es_al_info"] button,[class*="st-key-es_bn_info"] button{border-left-color:#27a9ff}
[class*="st-key-es_al_"] button:hover,[class*="st-key-es_bn_"] button:hover{background:#0f2c48;border-color:#00bffb}
/* ---------- hero ---------- */
.es-hero{padding:6px 0 4px}
.es-hero h1{margin:0;font-size:34px;font-weight:800;background:linear-gradient(90deg,#fff 30%,#58df57 65%,#00bffb);-webkit-background-clip:text;background-clip:text;color:transparent}
.es-hero p{margin:4px 0 0;color:#8ea6bf;font-size:14px}
/* ---------- KPI ---------- */
.es-kpi{position:relative;overflow:hidden;border-radius:16px;padding:16px 16px 12px;border:1px solid;display:grid;grid-template-columns:52px 1fr;gap:2px 12px;align-items:center;min-height:118px}
.es-kpi:before{content:"";position:absolute;right:-30px;top:-30px;width:130px;height:130px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.16),transparent 70%)}
.es-kpi .ico{font-size:32px;text-align:center;width:50px;height:50px;border-radius:14px;background:rgba(255,255,255,.12);display:grid;place-items:center}
.es-kpi .lab{color:#e8f1fb;font-size:12.5px;font-weight:600;letter-spacing:.2px}
.es-kpi .val{font-size:29px;font-weight:800;color:#fff;line-height:1.15}.es-kpi .val small{font-size:13px;font-weight:600;opacity:.85}
.es-kpi .chg{grid-column:1/-1;font-size:12px;color:#e3edf7;opacity:.9;margin-top:4px}
.es-kpi .spark{position:absolute;right:14px;bottom:10px;width:96px;height:34px}
.es-kpi.t{background:linear-gradient(135deg,#d6303a,#4a0f14);border-color:#e0464c}
.es-kpi.c{background:linear-gradient(135deg,#2a7be0,#0a2447);border-color:#3d8ee8}
.es-kpi.a{background:linear-gradient(135deg,#25b047,#0a3016);border-color:#3cc85a}
.es-kpi.s{background:linear-gradient(135deg,#1fb8ec,#0a3552);border-color:#3cc4f0}
/* ---------- anomaly rows ---------- */
.es-alert{display:flex;gap:12px;align-items:center;padding:9px 10px;border-radius:12px;background:#0b2036;border:1px solid #112f4c;border-left:3px solid #ff4d5a;margin-bottom:8px}
.es-alert.warning{border-left-color:#ffb020}.es-alert.info{border-left-color:#27a9ff}
.es-alert .i{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:16px;background:#4a1a1d;flex:none}
.es-alert.warning .i{background:#4a3510}.es-alert.info .i{background:#10324a}
.es-alert b{display:block;font-size:13.5px;color:#fff}.es-alert span{color:#8ea6bf;font-size:11.5px}
.es-alert .w{margin-left:auto;color:#8ea6bf;font-size:11.5px;white-space:nowrap;text-align:right}
@keyframes es-pulse{0%{box-shadow:0 0 0 0 rgba(255,59,74,.7)}100%{box-shadow:0 0 0 8px rgba(255,59,74,0)}}
/* ---------- chips ---------- */
.es-chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.es-chip{background:#0b2036;border:1px solid #173553;border-radius:12px;padding:6px 12px;font-size:12px;color:#8ea6bf}
.es-chip b{display:block;font-size:19px;color:#fff;line-height:1.1}
.es-chip.bad b{color:#ff8a4c}
/* ---------- ok state ---------- */
.es-ok{text-align:center;padding:26px 8px;border-radius:12px;background:linear-gradient(135deg,rgba(37,176,71,.14),rgba(0,191,251,.06));border:1px dashed #2a8a3a}
.es-ok .big{font-size:40px}.es-ok b{display:block;font-size:18px;color:#fff;margin-top:2px}.es-ok span{color:#8ea6bf;font-size:12px}
/* ---------- AI ---------- */
.es-pred{font-size:42px;font-weight:800;line-height:1.05;background:linear-gradient(90deg,#ffb020,#ff4d5a);-webkit-background-clip:text;background-clip:text;color:transparent}
.es-pred small{display:block;font-size:12px;color:#8ea6bf;font-weight:500;-webkit-text-fill-color:#8ea6bf}
.es-pill{display:inline-block;margin-top:8px;background:#171033;border:1px solid #3a2a66;border-radius:14px;padding:4px 12px;font-size:12px;color:#d8ccff}
/* ---------- footer ---------- */
.es-foot{display:flex;align-items:center;gap:8px;color:#8ea6bf;font-size:12px;margin-top:6px}
.es-foot .live{width:8px;height:8px;border-radius:50%;background:#3ddc84;animation:es-pulse2 1.6s infinite}
@keyframes es-pulse2{0%{box-shadow:0 0 0 0 rgba(61,220,132,.7)}100%{box-shadow:0 0 0 9px rgba(61,220,132,0)}}
</style>"""

AXIS = dict(gridcolor="rgba(255,255,255,.06)", zerolinecolor="rgba(255,255,255,.06)")
DARK = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9fb4cc", size=12))


# ------------------------------------------------------------------ helpers
def _ago(t):
    s = (datetime.datetime.utcnow() - t).total_seconds()
    if s < 3600:
        return f"{max(1, int(s // 60))}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago" if s < 86400 * 90 else t.strftime("%d %b %Y")


def _fmt(v, nd=2):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if isinstance(v, (int, float, np.integer, np.floating)):
        return f"{v:,.{nd}f}".rstrip("0").rstrip(".")
    return str(v)


def _chg(change, suffix):
    if change is None or pd.isna(change):
        return "no earlier data to compare"
    return f"{'▲' if change >= 0 else '▼'} {abs(change):.2f}{suffix} vs previous period"


def _h(icon, title, right=""):
    r = f'<span class="r">{html.escape(right)}</span>' if right else ""
    return f'<div class="es-h"><span class="dot"></span>{icon} {html.escape(title)}{r}</div>'


def _series(df, col, n=30):
    """Daily average of a column (live data) for sparklines."""
    try:
        if col not in df.columns:
            return []
        s = df.set_index("date")[col].astype(float).resample("D").mean().dropna()
        return s.tail(n).tolist()
    except Exception:
        return []


def _spark(values, color="#ffffff"):
    v = [float(x) for x in values if pd.notna(x)]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rng = (hi - lo) or 1.0
    w, h = 120, 34
    pts = " ".join(f"{i * w / (len(v) - 1):.1f},{h - 3 - (x - lo) / rng * (h - 8):.1f}" for i, x in enumerate(v))
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<polygon points="0,{h} {pts} {w},{h}" fill="{color}" opacity=".18"/>'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def _kpi(cls, icon, title, value, unit, sub, spark=""):
    return (f'<div class="es-kpi {cls}"><div class="ico">{icon}</div><div><div class="lab">{html.escape(title)}</div>'
            f'<div class="val">{html.escape(str(value))}<small> {html.escape(str(unit))}</small></div></div>'
            f'<div class="chg">{html.escape(sub)}</div>{spark}</div>')


# ------------------------------------------------------------------ navigation
def _navigate(page):
    """Sidebar ka page badal kar poori app dobara chalata hai (fragment ke andar se bhi kaam karta hai)."""
    st.session_state[NAV_KEY] = page
    try:
        st.rerun(scope="app")
    except TypeError:          # purana Streamlit jisme scope nahi hota
        st.rerun()


def _go(page, label, key):
    """Chota 'jump' button: click karne par us page par le jata hai."""
    if st.button(label, key=f"es_go_{key}", use_container_width=True):
        _navigate(page)


def _open_alert(db, al):
    """Alert par click: usay 'read' mark karo aur Alerts page par jao."""
    try:
        db.alerts.update_one({"_id": al["_id"]}, {"$set": {"read": True}})
    except Exception:
        pass
    st.session_state["alert_focus"] = str(al["_id"])      # Alerts page chahe to isay use kar sakta hai
    _navigate("Alerts")


def _sev(al):
    sev = str(al.get("severity", "critical"))
    return sev if sev in ("warning", "info") else "critical"


def _alert_label(al):
    icon = "ℹ️" if _sev(al) == "info" else "⚠️"
    fresh = (datetime.datetime.utcnow() - al["time"]).total_seconds() < 600
    station = str(al.get("station", "")).strip()
    title = str(al.get("title", "Alert")).strip()
    return f"{icon} {title}{' 🆕' if fresh else ''}" + (f" · {station}" if station else "") + f" · {_ago(al['time'])}"


def _bell(db):
    """Active notification bell: unread count dikhata hai, click par list khulti hai, har item par click karke Alerts page."""
    try:
        unread = db.alerts.count_documents({"read": False})
        items = list(db.alerts.find({"read": False}).sort("time", -1).limit(6))
    except Exception:
        unread, items = 0, []
    if unread:
        txt = f"{min(unread, 99)}{'+' if unread > 99 else ''}"
        st.markdown(f'<style>.st-key-es_bell_on{{--n:"{txt}"}}</style>', unsafe_allow_html=True)
    with st.container(key="es_bell_on" if unread else "es_bell_off"):
        with st.popover("🔔", use_container_width=True):
            st.markdown(f"**🔔 Notifications** · {unread} unread" if unread else "**🔔 Notifications**")
            if not items:
                st.caption("Koi nayi notification nahi. Sab kuch up to date hai ✅")
            for al in items:
                if st.button(_alert_label(al), key=f"es_bn_{_sev(al)}_{al['_id']}", use_container_width=True,
                             help=str(al.get("message", ""))):
                    _open_alert(db, al)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sab dekhein", key="es_go_bell_all", use_container_width=True):
                    _navigate("Alerts")
            with c2:
                if unread and st.button("Mark all read", key="es_go_bell_read", use_container_width=True):
                    try:
                        db.alerts.update_many({"read": False}, {"$set": {"read": True}})
                    except Exception:
                        pass
                    st.rerun()


def _station_points(db, df):
    """Har station ki latest reading + lat/lon (records ke columns, db.stations, ya CITY_COORDS se)."""
    last = df.sort_values("date").groupby("station", as_index=False).last()
    lat_c = next((c for c in ("lat", "latitude") if c in last.columns), None)
    lon_c = next((c for c in ("lon", "lng", "longitude") if c in last.columns), None)
    if lat_c and lon_c:
        last["lat"] = pd.to_numeric(last[lat_c], errors="coerce")
        last["lon"] = pd.to_numeric(last[lon_c], errors="coerce")
        return last
    coords = {}
    try:
        for s in db.stations.find({}, {"_id": 0}):
            la = s.get("lat", s.get("latitude"))
            lo = s.get("lon", s.get("lng", s.get("longitude")))
            nm = str(s.get("name") or s.get("station") or "").strip().lower()
            if nm and la is not None and lo is not None:
                coords[nm] = (float(la), float(lo))
    except Exception:
        pass

    def look(name):
        key = str(name).strip().lower()
        return coords.get(key) or CITY_COORDS.get(key) or (None, None)

    pts = last["station"].map(look)
    last["lat"] = pts.map(lambda p: p[0])
    last["lon"] = pts.map(lambda p: p[1])
    return last


def _geo_layout(fig, height, pts=None):
    fig.update_geos(projection_type="natural earth", showland=True, landcolor="#123a5e", showocean=True,
                    oceancolor="#061a30", showcountries=True, countrycolor="#24557f", showcoastlines=True,
                    coastlinecolor="#2f6a9a", showframe=False, bgcolor="rgba(0,0,0,0)", resolution=50)
    if pts is not None and len(pts) >= 2:
        fig.update_geos(fitbounds="locations")
    elif pts is not None and len(pts) == 1:
        fig.update_geos(center=dict(lat=float(pts["lat"].iloc[0]), lon=float(pts["lon"].iloc[0])), projection_scale=5)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), **DARK)


def _anomalies(df):
    """Pehle analytics.anomalies() try karta hai. Wo kuch na de to har station ke average se z-score check karta hai."""
    try:
        an = pd.DataFrame(analytics.anomalies(df))
        if not an.empty:
            return an, "analytics"
    except Exception:
        pass
    rows = []
    for col in ("temperature", "co2", "aqi"):
        if col not in df.columns:
            continue
        s = df[["date", "station", col]].dropna()
        if len(s) < 5:
            continue
        g = s.groupby("station")[col]
        cnt, mean, std = g.transform("count"), g.transform("mean"), g.transform("std")
        gm, gs = s[col].mean(), s[col].std()
        mean = mean.where(cnt >= 5, gm)
        std = std.where((cnt >= 5) & (std > 0), gs)
        if not gs or pd.isna(gs):
            continue
        z = (s[col] - mean) / std.replace(0, np.nan)
        bad = s[z.abs() >= Z_LIMIT].copy()
        if bad.empty:
            continue
        bad["metric"], bad["value"], bad["expected"], bad["z"] = col, bad[col], mean[bad.index], z[bad.index]
        rows.append(bad[["date", "station", "metric", "value", "expected", "z"]])
    if not rows:
        return pd.DataFrame(), "none"
    out = pd.concat(rows)
    out = out.reindex(out["z"].abs().sort_values(ascending=False).index).reset_index(drop=True)
    return out, "zscore"


# ------------------------------------------------------------------ cards
def _card_trend(df):
    st.markdown(_h("📈", "Climate Trends & 12-Month Forecast"), unsafe_allow_html=True)
    h2, h3 = st.columns(2)
    metrics = {"Temperature °C": "temperature", "CO₂ ppm": "co2", "AQI": "aqi"}
    metrics = {n: col for n, col in metrics.items() if col in df.columns and df[col].notna().any()}
    label = h2.selectbox("Metric", list(metrics), key="es_metric", label_visibility="collapsed")
    scope = h3.selectbox("Scope", ["Global"] + sorted(df["station"].astype(str).unique()), key="es_scope",
                         label_visibility="collapsed")
    d = df if scope == "Global" else df[df["station"].astype(str) == scope]
    try:
        t = analytics.trend(d, metrics[label])
        n = len(t["history"])
        fig = go.Figure()
        fig.add_scatter(x=t["labels"][:n], y=t["history"], name="Historical", mode="lines",
                        line=dict(color="#00bffb", width=3, shape="spline"), fill="tozeroy",
                        fillcolor="rgba(0,191,251,.10)")
        if t["forecast"]:
            fig.add_scatter(x=t["labels"][n - 1:], y=[t["history"][-1]] + t["forecast"], name="Forecast",
                            mode="lines+markers", line=dict(color="#ff9a3d", width=3, dash="dash", shape="spline"),
                            marker=dict(size=5))
        fig.update_xaxes(**AXIS)
        fig.update_yaxes(**AXIS)
        fig.update_layout(height=290, margin=dict(l=6, r=6, t=6, b=6), hovermode="x unified",
                          legend=dict(orientation="h", y=1.14, x=0), **DARK)
        st.plotly_chart(fig, width="stretch")
    except Exception:
        st.caption("Trend ke liye kam az kam kuch mahine ka data chahiye.")
    _go("Data Analytics", "Open Data Analytics →", "trend")


def _card_map(pts, mapped):
    st.markdown(_h("🗺️", "Global Climate Map", f"{len(mapped)} stations"), unsafe_allow_html=True)
    if mapped.empty:
        st.caption("Stations ke coordinates nahi mile. Records me lat/lon columns daalein ya `stations` collection banayein.")
    else:
        temp = mapped["temperature"].astype(float) if "temperature" in mapped.columns else pd.Series([0.0] * len(mapped), index=mapped.index)
        lo, hi = float(temp.min()), float(temp.max())
        if lo == hi:
            lo, hi = lo - 1, hi + 1
        co = mapped["co2"] if "co2" in mapped.columns else pd.Series([None] * len(mapped), index=mapped.index)
        aq = mapped["aqi"] if "aqi" in mapped.columns else pd.Series([None] * len(mapped), index=mapped.index)
        hover = [f"<b>{s}</b><br>🌡️ {_fmt(tv, 1)} °C<br>☁️ CO₂ {_fmt(c_, 0)} ppm<br>🍃 AQI {_fmt(a_, 0)}"
                 for s, tv, c_, a_ in zip(mapped["station"], temp, co, aq)]
        fig = go.Figure()
        fig.add_trace(go.Scattergeo(lat=mapped["lat"], lon=mapped["lon"], hoverinfo="skip", mode="markers",
                                    marker=dict(size=38, color=temp, colorscale="Turbo", cmin=lo, cmax=hi,
                                                opacity=0.18, showscale=False)))
        labels = len(mapped) <= 12
        fig.add_trace(go.Scattergeo(lat=mapped["lat"], lon=mapped["lon"], hovertext=hover, hoverinfo="text",
                                    text=mapped["station"].tolist() if labels else None,
                                    mode="markers+text" if labels else "markers",
                                    textposition="top center", textfont=dict(size=10, color="#cfe3f7"),
                                    marker=dict(size=15, color=temp, colorscale="Turbo", cmin=lo, cmax=hi, showscale=True,
                                                colorbar=dict(title="°C", thickness=9, len=0.7, x=1.0),
                                                line=dict(width=1.5, color="#fff"))))
        _geo_layout(fig, 310, mapped)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
    missing = len(pts) - len(mapped)
    if missing:
        st.caption(f"{missing} station(s) ke coordinates nahi mile, isliye map par nahi dikhe.")
    _go("Climate Map", "View Full Map →", "map")


def _card_alerts(db, alert_filter):
    total = db.alerts.count_documents(alert_filter)
    st.markdown(_h("🔔", "Latest Alerts", f"{total} total"), unsafe_allow_html=True)
    items = list(db.alerts.find(alert_filter).sort("time", -1).limit(5))
    if not items:
        st.markdown('<div class="es-ok"><div class="big">🔕</div><b>No alerts</b><span>Sab kuch normal hai</span></div>',
                    unsafe_allow_html=True)
    for al in items:       # har alert ek button hai: click karo to Alerts page khulta hai
        if st.button(_alert_label(al), key=f"es_al_{_sev(al)}_{al['_id']}", use_container_width=True,
                     help=str(al.get("message", ""))):
            _open_alert(db, al)
    _go("Alerts", "View All Alerts →", "alerts")


def _card_anomalies(user, df, mapped):
    st.markdown(_h("🌋", "Climate Anomalies"), unsafe_allow_html=True)
    if user["role"] == "viewer":
        st.caption("Sirf admins aur analysts ke liye.")
        return
    an, src = _anomalies(df)
    if an.empty:
        st.markdown(f'<div class="es-ok"><div class="big">✅</div><b>All clear</b>'
                    f'<span>{len(df):,} readings · {df["station"].nunique()} stations check kiye, koi ghair-mamooli value nahi</span></div>',
                    unsafe_allow_html=True)
        return
    n_st = an["station"].nunique() if "station" in an.columns else "–"
    st.markdown(f'<div class="es-chips"><div class="es-chip bad"><b>{len(an):,}</b>anomalies</div>'
                f'<div class="es-chip"><b>{n_st}</b>stations</div></div>', unsafe_allow_html=True)
    if "station" in an.columns and not mapped.empty:
        cnt = an.groupby("station").size().rename("count").reset_index()
        m = cnt.merge(mapped[["station", "lat", "lon"]], on="station").dropna(subset=["lat", "lon"])
        if not m.empty:
            fig = go.Figure(go.Scattergeo(
                lat=m["lat"], lon=m["lon"], hoverinfo="text",
                text=[f"<b>{s}</b><br>{c_} anomalies" for s, c_ in zip(m["station"], m["count"])],
                marker=dict(size=(m["count"].clip(upper=30) + 12), color=m["count"], colorscale="YlOrRd",
                            opacity=0.85, line=dict(width=1.5, color="#fff"))))
            _geo_layout(fig, 170, m)
            st.plotly_chart(fig, width="stretch")
    if src == "zscore":
        for _, r in an.head(3).iterrows():
            unit = UNITS.get(r["metric"], "")
            dt = r["date"].strftime("%d %b") if hasattr(r["date"], "strftime") else str(r["date"])
            st.markdown(f'<div class="es-alert warning"><div class="i">📈</div><div>'
                        f'<b>{NAMES.get(r["metric"], r["metric"])} {_fmt(r["value"], 1)}{unit}</b>'
                        f'<span>{html.escape(str(r["station"]))} · normal ≈ {_fmt(r["expected"], 1)}{unit} · z={r["z"]:+.1f}</span></div>'
                        f'<div class="w">{dt}</div></div>', unsafe_allow_html=True)
    else:
        st.dataframe(an.head(6), width="stretch", hide_index=True, height=170)
    _go("Data Analytics", "Analyse in detail →", "anom")


def _card_ai(df):
    st.markdown(_h("🧠", "AI Prediction"), unsafe_allow_html=True)
    year = datetime.date.today().year + 5
    p = analytics.predict_delta(df, year)
    if not p:
        st.markdown('<div class="es-ok"><div class="big">⏳</div><b>Data chahiye</b><span>Prediction ke liye kam az kam 6 mahine ka data</span></div>',
                    unsafe_allow_html=True)
        return
    st.markdown(f'<div class="es-pred">{p["delta"]:+.2f}°C<small>Avg temperature change by {p["year"]}</small></div>'
                f'<span class="es-pill">🔥 Warming rate {p["slope"]:+.2f} °C / year</span>', unsafe_allow_html=True)
    try:
        t = analytics.trend(df, "temperature")
        hist, fc = t["history"][-12:], (t["forecast"] or [])
        fig = go.Figure()
        fig.add_scatter(y=hist, x=list(range(len(hist))), mode="lines", line=dict(color="#3ddc84", width=3, shape="spline"),
                        fill="tozeroy", fillcolor="rgba(61,220,132,.10)", hoverinfo="skip")
        if fc:
            fig.add_scatter(y=[hist[-1]] + fc, x=list(range(len(hist) - 1, len(hist) + len(fc))), mode="lines",
                            line=dict(color="#ffb020", width=3, dash="dash", shape="spline"), hoverinfo="skip")
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(height=120, margin=dict(l=0, r=0, t=6, b=0), showlegend=False, **DARK)
        st.plotly_chart(fig, width="stretch")
    except Exception:
        pass
    _go("Reports", "Open Reports →", "ai")


# ------------------------------------------------------------------ live body
def _body(user, days, query):
    db = analytics.get_db()
    full = analytics.load(db)
    if full.empty:
        st.info("Abhi database me climate data nahi hai. **Data Upload** ya **Data Management** se data daalein.")
        return
    full = full.copy()
    full["date"] = pd.to_datetime(full["date"], errors="coerce")

    df = full
    q = (query or "").strip()
    alert_filter = {}
    if q:
        df = full[full["station"].astype(str).str.contains(q, case=False, na=False, regex=False)]
        rx = {"$regex": re.escape(q), "$options": "i"}
        alert_filter = {"$or": [{"station": rx}, {"title": rx}, {"message": rx}]}
        if df.empty:
            st.warning(f"'{q}' naam ka koi station nahi mila.")
            return

    # ---------------- KPI cards (sparkline = last 30 days ka live trend)
    k = analytics.kpis(df, days)
    c = st.columns(4)
    c[0].markdown(_kpi("t", "🌡️", "Avg Temperature", _fmt(k["temperature"]["value"]), "°C",
                       _chg(k["temperature"]["change"], "°C"), _spark(_series(df, "temperature"))), unsafe_allow_html=True)
    c[1].markdown(_kpi("c", "☁️", "CO₂ Level", _fmt(k["co2"]["value"]), "ppm",
                       _chg(k["co2"]["pct"], "%"), _spark(_series(df, "co2"))), unsafe_allow_html=True)
    c[2].markdown(_kpi("a", "🍃", "Air Quality Index", _fmt(k["aqi"]["value"]), f"({k['aqi']['label']})",
                       _chg(k["aqi"]["pct"], "%"), _spark(_series(df, "aqi"))), unsafe_allow_html=True)
    c[3].markdown(_kpi("s", "💧", "Sea Level", _fmt(k["sea_level"]["value"]), "mm/year",
                       "trend over all uploaded data", _spark(_series(df, "sea_level"))), unsafe_allow_html=True)
    for i, name in enumerate(("temp", "co2", "aqi", "sea")):       # har KPI ke neeche detail ka button
        with c[i]:
            _go("Data Analytics", "Details →", f"kpi_{name}")
    st.write("")

    pts = _station_points(db, df)
    mapped = pts.dropna(subset=["lat", "lon"])

    a, b = st.columns([3, 2])
    with a.container(border=True):
        _card_trend(df)
    with b.container(border=True):
        _card_map(pts, mapped)

    x, y, z = st.columns(3)
    with x.container(border=True):
        _card_alerts(db, alert_filter)
    with y.container(border=True):
        _card_anomalies(user, df, mapped)
    with z.container(border=True):
        _card_ai(df)

    st.markdown(f'<div class="es-foot"><span class="live"></span>Live · updated {datetime.datetime.now():%H:%M:%S} · '
                f'{len(df):,} records · {df["station"].nunique()} stations · '
                f'{df["date"].min():%Y-%m-%d} → {df["date"].max():%Y-%m-%d}</div>', unsafe_allow_html=True)


# Auto-refresh wala (live) aur bina refresh wala version
if hasattr(st, "fragment"):
    @st.fragment(run_every=LIVE_SECONDS)
    def _body_live(user, days, query):
        _body(user, days, query)

    @st.fragment
    def _body_static(user, days, query):
        _body(user, days, query)
else:                                   # purana Streamlit: auto-refresh nahi, har click par naya data
    _body_live = _body_static = _body


# ------------------------------------------------------------------ page
def dashboard_page(user):
    st.markdown(CSS, unsafe_allow_html=True)
    db = analytics.get_db()

    s_col, l_col, b_col, u_col = st.columns([4, 1, 0.6, 2])
    query = s_col.text_input("Search", placeholder="🔍 Search station...", label_visibility="collapsed", key="es_search")
    live = l_col.toggle("Live", value=True, key="es_live", help=f"Har {LIVE_SECONDS} second baad data refresh")
    with b_col:
        _bell(db)                                                 # active notification bell
    u_col.markdown(f'<div class="es-top"><div class="es-user"><i>{html.escape(user["name"][:1].upper())}</i>'
                   f'<span>{html.escape(user["name"].split()[0])} · {html.escape(user["role"].title())}</span></div></div>',
                   unsafe_allow_html=True)

    left, right = st.columns([4, 1])
    left.markdown(f'<div class="es-hero"><h1>🍃 Welcome Back, {html.escape(user["name"].split()[0])}!</h1>'
                  f'<p>Monitoring our planet. Building a sustainable future.</p></div>', unsafe_allow_html=True)
    days = right.selectbox("Period", [7, 30, 90, 365, 0], index=1, label_visibility="collapsed", key="es_days",
                           format_func=lambda d: "All data" if d == 0 else f"Last {d} days")

    (_body_live if live else _body_static)(user, days, query)