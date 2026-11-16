"""Climate Map page for EarthScape (Streamlit + Plotly).
Is file ko app.py ke saath isi folder mein rakhein (naam: Climite.py).
Saath mein countries.py bhi isi folder mein honi chahiye.
Data analytics.load(db) se aata hai.  Optional: pip install global-land-mask
"""
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

import analytics
from countries import COUNTRIES, iso3

# station name (lowercase) -> (lat, lon).  Naye stations form / convert script se db.stations mein save hote hain.
KNOWN = {
    "karachi": (24.86, 67.01), "lahore": (31.52, 74.36), "islamabad": (33.68, 73.05),
    "rawalpindi": (33.60, 73.04), "peshawar": (34.01, 71.58), "quetta": (30.18, 66.98),
    "multan": (30.16, 71.52), "faisalabad": (31.42, 73.08), "hyderabad": (25.39, 68.37),
    "gujranwala": (32.16, 74.19), "delhi": (28.61, 77.21),
    "mumbai": (19.08, 72.88), "dhaka": (23.81, 90.41), "dubai": (25.20, 55.27),
    "riyadh": (24.71, 46.68), "cairo": (30.04, 31.24), "istanbul": (41.01, 28.98),
    "moscow": (55.76, 37.62), "london": (51.51, -0.13), "paris": (48.86, 2.35),
    "berlin": (52.52, 13.40), "new york": (40.71, -74.01), "los angeles": (34.05, -118.24),
    "sao paulo": (-23.55, -46.63), "lagos": (6.52, 3.38), "nairobi": (-1.29, 36.82),
    "beijing": (39.90, 116.41), "tokyo": (35.68, 139.69), "sydney": (-33.87, 151.21),
}

# layer -> (column, unit, zmin, zmax, icon, kpi colour class)   None = data se automatic
LAYERS = {
    "Temperature": ("temperature", "°C", -20, 45, "🌡️", "t"),
    "CO₂": ("co2", "ppm", None, None, "☁️", "c"),
    "Air Quality (AQI)": ("aqi", "", 0, 200, "🍃", "a"),
    "Humidity": ("humidity", "%", 0, 100, "💧", "s"),
    "Rainfall": ("rainfall", "mm", None, None, "🌧️", "s"),
    "Sea Level": ("sea_level", "mm", None, None, "🌊", "s"),
}

COLORSCALE = [(0, "#1d4cff"), (0.2, "#00c8ff"), (0.4, "#19e68c"),
              (0.6, "#e8f02a"), (0.8, "#ff9a1f"), (1, "#ff2a2a")]

# column -> (Open-Meteo endpoint, variable).  Sea level ka live source nahi hai.
WORLD_VARS = {
    "temperature": ("https://api.open-meteo.com/v1/forecast", "temperature_2m"),
    "humidity": ("https://api.open-meteo.com/v1/forecast", "relative_humidity_2m"),
    "rainfall": ("https://api.open-meteo.com/v1/forecast", "precipitation"),
    "aqi": ("https://air-quality-api.open-meteo.com/v1/air-quality", "us_aqi"),
    "co2": ("https://air-quality-api.open-meteo.com/v1/air-quality", "carbon_dioxide"),
    # Marine API: sea level (tides + pressure effect) metres mein, sirf samundar ke points par; neeche mm mein badal diya jata hai
    "sea_level": ("https://marine-api.open-meteo.com/v1/marine", "sea_level_height_msl"),
}

COUNTRY_NAMES = sorted(v[0] for v in COUNTRIES.values())
NAME_TO_ISO = {v[0]: k for k, v in COUNTRIES.items()}


# ------------------------------------------------------------------ data helpers
def station_info(db):
    """db.stations se: key -> (lat, lon) aur key -> country name."""
    coords, countries = dict(KNOWN), {}
    for s in db.stations.find():
        coords[s["_id"]] = (s["lat"], s["lon"])
        if s.get("country"):
            countries[s["_id"]] = s["country"]
    return coords, countries


def station_country_values(g_all, col, countries):
    """Stations ka average country ke hisab se -> Series(iso3 -> value)."""
    if g_all.empty or not countries:
        return pd.Series(dtype=float)
    keys = g_all["station"].str.strip().str.lower()
    iso = keys.map(lambda k: iso3(countries[k]) if k in countries else None)
    return g_all[col].groupby(iso).mean().dropna()


def window_filter(df, days):
    """FIX: har station ka time range uske APNE aakhri date se gina jata hai.
    Pehle poore data ki sab se nayi date use hoti thi, is liye jin stations ka
    data thoda purana tha (ya monthly data tha) woh map se gayab ho jate the."""
    if days == 0:
        return df
    last = df.groupby("station")["date"].transform("max")
    return df[df["date"] >= last - pd.Timedelta(days=days)]


def idw_grid(lats, lons, vals, step=3, power=2, max_dist=30):
    """Stations ke beech ki values ka andaza; station se max_dist degree door tak hi rang."""
    glat, glon = np.arange(-60, 85, step), np.arange(-180, 180, step)
    LON, LAT = np.meshgrid(glon, glat)
    plat, plon = LAT.ravel(), LON.ravel()
    dlat = plat[:, None] - lats[None, :]
    dlon = (plon[:, None] - lons[None, :] + 180) % 360 - 180
    dist = np.sqrt(dlat ** 2 + dlon ** 2)
    keep = dist.min(1) <= max_dist
    w = 1 / (dist[keep] + 1e-6) ** power
    return plat[keep], plon[keep], (w * vals).sum(1) / w.sum(1)


def _fetch(col, la, lo):
    """Open-Meteo (free, no key) se in points ka abhi ka data; batches ek saath."""
    url, var = WORLD_VARS[col]

    def one(i):
        r = requests.get(url, timeout=20, params={
            "latitude": ",".join(f"{x:.2f}" for x in la[i:i + 100]),
            "longitude": ",".join(f"{x:.2f}" for x in lo[i:i + 100]),
            "current": var})
        r.raise_for_status()
        data = r.json()
        data = data if isinstance(data, list) else [data]
        return [(d.get("current") or {}).get(var) for d in data]

    with ThreadPoolExecutor(max_workers=4) as ex:
        out = [v for part in ex.map(one, range(0, len(la), 100)) for v in part]
    arr = np.array(out, dtype=float)           # None -> nan (zameen ke points sea level mein nan aate hain)
    return arr * 1000 if col == "sea_level" else arr   # sea level: m -> mm


@st.cache_data(ttl=3600, persist="disk", show_spinner="Loading live world data (first time only)...")
def world_data(col, step=12, bounds=None):
    """Grid ka abhi ka data (Heat grid view).
    bounds=None -> poori duniya (12 degree step, mota grid).
    bounds=(lat_min, lat_max, lon_min, lon_max) -> sirf us region ki barik grid (1 degree step)."""
    if bounds:
        la0, la1, lo0, lo1 = bounds
        lats = np.arange(max(la0, -89), min(la1, 89) + 0.01, step)
        lons = np.arange(max(lo0, -180), min(lo1, 180) + 0.01, step)
    else:
        lats, lons = np.arange(-60, 76, step), np.arange(-180, 180, step)
    LON, LAT = np.meshgrid(lons, lats)
    la, lo = LAT.ravel(), LON.ravel()
    z = _fetch(col, la, lo)
    ok = ~np.isnan(z)
    la, lo, z = la[ok], lo[ok], z[ok]
    if z.size == 0:
        raise ValueError("no data returned for this layer")
    try:                                       # optional: samundar hata do, sirf zameen rakho (sea level par lagu nahi)
        if col == "sea_level":
            raise ImportError
        from global_land_mask import globe
        keep = globe.is_land(la, lo)
        if keep.any():
            la, lo, z = la[keep], lo[keep], z[keep]
    except Exception:
        pass
    return la, lo, z


@st.cache_data(ttl=3600, persist="disk", show_spinner="Loading live data for every country (first time only)...")
def world_countries(col):
    """Har country ke ek central point ka abhi ka data."""
    isos = list(COUNTRIES)
    la = np.array([COUNTRIES[k][1] for k in isos])
    lo = np.array([COUNTRIES[k][2] for k in isos])
    z = _fetch(col, la, lo)
    ok = ~np.isnan(z)
    if not ok.any():
        raise ValueError("no data returned for this layer")
    return [k for k, o in zip(isos, ok) if o], z[ok]


def auto_range(arr, zmin, zmax):
    if zmin is not None:
        return zmin, zmax
    lo_v, hi_v = float(np.nanmin(arr)), float(np.nanmax(arr))
    if hi_v - lo_v < 1:
        mid = (lo_v + hi_v) / 2
        lo_v, hi_v = mid - 1, mid + 1
    return lo_v, hi_v


def coords_form(db, missing, user):
    st.warning("Coordinates missing for: " + ", ".join(missing[:20]) + (" ..." if len(missing) > 20 else ""))
    if user["role"] == "viewer":
        st.caption("Ask an analyst or admin to add the location.")
        return
    with st.form("coords"):
        s = st.selectbox("Station", missing)
        c = st.columns(2)
        lat = c[0].number_input("Latitude", -90.0, 90.0, 0.0, format="%.4f")
        lon = c[1].number_input("Longitude", -180.0, 180.0, 0.0, format="%.4f")
        if st.form_submit_button("Save location"):
            db.stations.update_one({"_id": s.strip().lower()},
                                   {"$set": {"name": s, "lat": lat, "lon": lon}}, upsert=True)
            st.rerun()


def card(cls, icon, label, value, sub):
    return (f'<div class="kpi {cls}"><div class="ico">{icon}</div><div><div class="lab">{label}</div>'
            f'<div class="val">{value}</div></div><div class="chg">{sub}</div></div>')


def show_cards(cards):
    st.write("")
    for column, c in zip(st.columns(4), cards):
        column.markdown(card(*c), unsafe_allow_html=True)


# ------------------------------------------------------------------ country view
def country_view(col_map, layer, icon, cls, unit, zmin, zmax, isos, vals, selected, g, label):
    names = [COUNTRIES[k][0] for k in isos]
    vals = np.asarray(vals, dtype=float)
    fig = go.Figure(go.Choropleth(
        locations=isos, z=vals, locationmode="ISO-3", text=names,
        colorscale=COLORSCALE, zmin=zmin, zmax=zmax,
        marker=dict(line=dict(color="#0b1426", width=0.6)),
        hovertemplate="<b>%{text}</b><br>%{z:.1f} " + unit + "<extra></extra>",
        colorbar=dict(title=dict(text=unit, font=dict(color="#d3e0ee")), tickfont=dict(color="#d3e0ee"),
                      thickness=12, len=0.7, bgcolor="rgba(0,0,0,0)")))

    view = dict(lataxis_range=[-58, 85])
    if selected:
        _, la, lo = COUNTRIES[selected]
        view = dict(lataxis_range=[max(la - 16, -90), min(la + 16, 90)], lonaxis_range=[lo - 30, lo + 30])
        if selected in isos:
            fig.add_trace(go.Choropleth(
                locations=[selected], z=[vals[isos.index(selected)]], locationmode="ISO-3",
                colorscale=COLORSCALE, zmin=zmin, zmax=zmax, showscale=False, hoverinfo="skip",
                marker=dict(line=dict(color="white", width=2.5))))
    if g is not None and not g.empty:          # tumhare stations chhote safed dots
        fig.add_trace(go.Scattergeo(
            lat=g["lat"], lon=g["lon"], mode="markers", text=g["station"],
            hovertemplate="<b>%{text}</b><extra>your station</extra>",
            marker=dict(size=5, color="white", opacity=0.9)))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=True,
                    coastlinecolor="#22385c", showcountries=True, countrycolor="#1b2f50",
                    showland=True, landcolor="#101d33", showocean=True, oceancolor="#07111f",
                    showlakes=False, bgcolor="rgba(0,0,0,0)", **view)
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False)

    with col_map.container(border=True):
        head = st.columns([3, 2])
        title = f"{icon} {layer} · by country"
        if selected:
            title += f" · {COUNTRIES[selected][0]}"
        head[0].markdown(f"##### {title}")
        head[1].caption(label)
        st.plotly_chart(fig, width="stretch")

    vd = dict(zip(isos, vals.tolist()))
    mean = float(vals.mean())
    order = sorted(vd, key=vd.get, reverse=True)
    fmt = lambda v: f"{v:.1f} <small>{unit}</small>"
    if selected and selected in vd:
        v = vd[selected]
        show_cards([
            (cls, icon, f"{COUNTRIES[selected][0]} · {layer}", fmt(v), f"#{order.index(selected) + 1} of {len(order)} countries"),
            ("c", "🌍", "Average of all countries", fmt(mean), label),
            ("t", "📊", "Difference", f"{v - mean:+.1f} <small>{unit}</small>", "this country vs the average"),
            ("a", "🗺️", "Countries with data", f"{len(order)}", "on the map"),
        ])
        return
    if selected:
        st.info(f"No {layer} data for {COUNTRIES[selected][0]}.")
    hi, lo = order[0], order[-1]
    show_cards([
        (cls, icon, f"Average {layer}", fmt(mean), "average of all countries"),
        ("t", "🔥", "Highest country", fmt(vd[hi]), COUNTRIES[hi][0]),
        ("c", "❄️", "Lowest country", fmt(vd[lo]), COUNTRIES[lo][0]),
        ("a", "🗺️", "Countries with data", f"{len(order)}", label),
    ])


# ------------------------------------------------------------------ page
def climate_map_page(db, user):
    st.title("🌐 Climate Map")
    st.caption("Your station readings and the live world data on one map - by point or by country.")
    df = analytics.load(db)
    if df.empty:
        st.info("No climate data yet. Open **Data Upload** and upload a file first.")
        return

    col_map, col_ctrl = st.columns([5, 1.4])
    with col_ctrl.container(border=True):
        st.markdown("##### ⚙️ Controls")
        layer = st.selectbox("Map Layer", list(LAYERS))
        days = st.selectbox("Time Range", [7, 30, 90, 365, 0], index=1,
                            format_func=lambda d: "All data" if d == 0 else f"Last {d} days",
                            help="Har station ka range uske apne aakhri reading se gina jata hai.")
        source = st.radio("Data", ["My stations", "World (live)"],
                          help="World (live): poori duniya ka abhi ka data - Temperature, CO2, AQI, Humidity, Rainfall.")
        if source == "World (live)":
            # sea level sirf samundar par hota hai, is liye country view nahi
            views = ["Heat grid"] if LAYERS[layer][0] == "sea_level" else ["By country", "Heat grid"]
        else:
            views = ["Glow markers", "Heatmap", "By country"]
        view = st.radio("View", views)
        region_iso, half = None, 8
        if view == "Heat grid":
            rpick = st.selectbox("Zoom to", ["Whole world"] + COUNTRY_NAMES,
                                 help="Apne mulk ko chun lo - us ke aas paas ka barik (1°) live data aayega.")
            if rpick != "Whole world":
                region_iso = NAME_TO_ISO[rpick]
                half = st.slider("Area size (°)", 4, 20, 8)
        selected = None
        if view == "By country":
            pick = st.selectbox("Country", ["All countries"] + COUNTRY_NAMES)
            selected = None if pick == "All countries" else NAME_TO_ISO[pick]
    col, unit, zmin, zmax, icon, cls = LAYERS[layer]

    want_world = source == "World (live)"
    fallback_note = ""
    if want_world and col not in WORLD_VARS:
        col_ctrl.caption("No live world data for this layer - showing your stations.")
        want_world = False
    if not want_world and view == "Heat grid":
        view = "Glow markers"

    # ---- station values
    coords, countries = station_info(db)
    g_all = pd.DataFrame(columns=["station", col])
    g = pd.DataFrame(columns=["station", col, "lat", "lon"])
    missing = []
    if col in df.columns and not df[col].dropna().empty:
        d = window_filter(df.dropna(subset=[col]), days)      # FIX: per-station window
        g_all = d.groupby("station")[col].mean().dropna().reset_index()
        g = g_all.copy()
        keys = g["station"].str.strip().str.lower()
        g["lat"] = keys.map(lambda k: coords.get(k, (np.nan, np.nan))[0])
        g["lon"] = keys.map(lambda k: coords.get(k, (np.nan, np.nan))[1])
        g["ctext"] = keys.map(lambda k: f", {countries[k]}" if k in countries else "")
        missing = g.loc[g["lat"].isna(), "station"].tolist()
        g = g.dropna(subset=["lat", "lon"])
        if not want_world and not d.empty:
            fallback_note = f"data: {d['date'].min():%Y-%m-%d} → {d['date'].max():%Y-%m-%d}"
    elif not want_world:
        if col in WORLD_VARS:                  # tumhare data mein ye layer nahi -> live world dikhao, khali page nahi
            want_world = True
            view = "Heat grid" if col == "sea_level" else "By country"   # sea level samundar ka data hai, country view nahi
            fallback_note = f"No '{col}' data in your uploads yet - showing live world data."
        else:
            col_map.info(f"No '{col}' data uploaded yet, and there is no live source for this layer.")
            return

    # ---- by country
    world_failed = False
    if view == "By country":
        iso_list = vals = None
        label = fallback_note
        if want_world:
            try:
                iso_list, vals = world_countries(col)
                label = fallback_note or "live now - one central point per country"
            except Exception as e:
                world_failed = True
                col_map.warning(f"Live world data could not be loaded ({e}). Showing your stations only.")
        else:
            sc = station_country_values(g_all, col, countries)
            if len(sc):
                iso_list, vals = list(sc.index), sc.to_numpy()
                label = f"average of your stations in {len(sc)} countries"
            else:
                col_map.info("Your stations have no country info yet. Run convert_climate_csv.py again "
                             "(it now saves countries). Showing markers instead.")
                view = "Glow markers"
        if iso_list is not None:
            zlo, zhi = auto_range(vals, zmin, zmax)
            country_view(col_map, layer, icon, cls, unit, zlo, zhi, iso_list, vals, selected, g, label)
            return
        view = "Glow markers"

    # ---- live world grid (Heat grid)
    w = None
    if want_world and not world_failed:
        try:
            if region_iso:
                _, rla, rlo = COUNTRIES[region_iso]
                bounds = (round(rla - half, 1), round(rla + half, 1),
                          round(rlo - half * 1.3, 1), round(rlo + half * 1.3, 1))
                w = world_data(col, 1.0 if half <= 10 else 1.5, bounds)
            else:
                w = world_data(col)
        except Exception as e:
            col_map.warning(f"Live world data could not be loaded ({e}). Showing your stations only.")
    if w is None and g.empty:
        if missing:
            coords_form(db, missing, user)
        else:
            col_map.info("No data to show for this layer and time range.")
        return

    zmin, zmax = auto_range(w[2] if w is not None else g[col].to_numpy(dtype=float), zmin, zmax)

    fig = go.Figure()
    cbar = dict(title=dict(text=unit, font=dict(color="#d3e0ee")), tickfont=dict(color="#d3e0ee"),
                thickness=12, len=0.8, x=0.99, xanchor="right", y=0.5, bgcolor="rgba(0,0,0,0)")

    # ---- heat layer
    heat, radius, note = None, 28, ""
    if w is not None:
        heat, radius = w, 40
    elif view == "Heatmap":
        if len(g) >= 3:
            heat = idw_grid(g["lat"].to_numpy(), g["lon"].to_numpy(), g[col].to_numpy())
        else:
            note = "Heatmap needs at least 3 stations - showing glow markers instead."
    if heat is not None:
        fig.add_trace(go.Densitymap(lat=heat[0], lon=heat[1], z=heat[2], radius=radius, opacity=0.85,
                                    colorscale=COLORSCALE, zmin=zmin, zmax=zmax,
                                    colorbar=cbar, hoverinfo="skip"))

    # ---- station markers
    if not g.empty:
        glow = heat is None
        if glow:
            for size, op in ((54, 0.10), (34, 0.20)):
                fig.add_trace(go.Scattermap(
                    lat=g["lat"], lon=g["lon"], mode="markers", hoverinfo="skip",
                    marker=dict(size=size, color=g[col], colorscale=COLORSCALE,
                                cmin=zmin, cmax=zmax, opacity=op)))
        label = g["station"] + "  " + g[col].round(1).astype(str) + " " + unit
        fig.add_trace(go.Scattermap(
            lat=g["lat"], lon=g["lon"], mode="markers+text" if len(g) <= 15 else "markers", text=label,
            textposition="top center", textfont=dict(color="white", size=13),
            customdata=np.column_stack([g["station"], g[col].round(2), g["ctext"]]),
            hovertemplate="<b>%{customdata[0]}</b>%{customdata[2]}<br>%{customdata[1]} " + unit + "<extra></extra>",
            marker=dict(size=14 if glow else 10, color=g[col], colorscale=COLORSCALE,
                        cmin=zmin, cmax=zmax, showscale=glow, colorbar=cbar)))

    if w is not None:
        if region_iso:
            center = dict(lat=COUNTRIES[region_iso][1], lon=COUNTRIES[region_iso][2])
            zoom = 5 if half <= 6 else 4.2 if half <= 10 else 3.3
        else:
            center, zoom = dict(lat=20, lon=10), 1.0
    else:
        span = max(g["lat"].max() - g["lat"].min(), g["lon"].max() - g["lon"].min())
        center = dict(lat=float(g["lat"].mean()), lon=float(g["lon"].mean()))
        zoom = 1.2 if span > 60 else 2.5 if span > 15 else 5
    fig.update_layout(map_style="carto-darkmatter", map_center=center, map_zoom=zoom,
                      margin=dict(l=0, r=0, t=0, b=0), height=560,
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False)

    with col_map.container(border=True):
        head = st.columns([3, 2])
        head[0].markdown(f"##### {icon} {layer} " + ((f"· {COUNTRIES[region_iso][0]} region (live now)" if region_iso else "· World (live now)")
                                                  if w is not None else f"· {len(g)} station(s)"))
        if note or fallback_note:
            head[1].caption(note or fallback_note)
        st.plotly_chart(fig, width="stretch")

    # ---- stat cards
    if w is not None:
        z = w[2]
        hi, lo = int(np.argmax(z)), int(np.argmin(z))
        show_cards([
            (cls, icon, f"World average {layer}", f"{z.mean():.1f} <small>{unit}</small>", "live grid average"),
            ("t", "🔥", "Hottest point", f"{z[hi]:.1f} <small>{unit}</small>", f"near {w[0][hi]:.0f}°, {w[1][hi]:.0f}°"),
            ("c", "❄️", "Coldest point", f"{z[lo]:.1f} <small>{unit}</small>", f"near {w[0][lo]:.0f}°, {w[1][lo]:.0f}°"),
            ("a", "📍", "Your stations", f"{len(g)}", "shown on the map"),
        ])
    else:
        top, low = g.loc[g[col].idxmax()], g.loc[g[col].idxmin()]
        show_cards([
            (cls, icon, f"Average {layer}", f"{g[col].mean():.1f} <small>{unit}</small>", "all stations on the map"),
            ("t", "🔥", "Highest", f"{top[col]:.1f} <small>{unit}</small>", str(top["station"])),
            ("c", "❄️", "Lowest", f"{low[col]:.1f} <small>{unit}</small>", str(low["station"])),
            ("a", "📍", "Stations on map", f"{len(g)}", f"{len(missing)} without location" if missing else "all located"),
        ])

    if missing:
        with st.expander(f"{len(missing)} station(s) not on map - add location"):
            coords_form(db, missing, user)