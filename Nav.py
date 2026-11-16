
import base64
import re
from pathlib import Path

import streamlit as st

BANNER_IMG = Path(__file__).parent / "assets" / "Emerald Earth Eco Landscape.png"

# (page name, material icon).  Sirf wahi dikhte hain jo app.py ke PAGES mein hon.
ITEMS = [
    ("Dashboard", ":material/home:"),
    ("Climate Map", ":material/map:"),
    ("Data Analytics", ":material/bar_chart:"),
    # ("Data Upload", ":material/cloud_upload:"),
    ("Reports", ":material/description:"),
    ("Alerts", ":material/notifications:"),
    ("Profile", ":material/person:"),
    ("Settings", ":material/settings:"),
    ("Support & Feedback", ":material/headset_mic:"),
    ("Manage Users", ":material/groups:"),
]

CSS = """<style>
[data-testid=stSidebar]{background:linear-gradient(180deg,#06182c 0%,#040d1c 100%);border-right:1px solid #173553}
[data-testid=stSidebar] .stButton{width:100%}
[data-testid=stSidebar] .stButton>button{position:relative;width:100%;justify-content:flex-start;gap:.7rem;
  background:transparent;border:0;box-shadow:none;color:#d8e4f2;font-size:15px;padding:.62rem .9rem;border-radius:12px}
[data-testid=stSidebar] .stButton>button div{justify-content:flex-start;text-align:left}
[data-testid=stSidebar] .stButton>button:hover{background:rgba(0,191,251,.10);color:#fff}
[data-testid=stSidebar] .stButton>button[kind=primary]{background:linear-gradient(90deg,#58df57,#00bffb);
  color:#06210f;font-weight:700;box-shadow:0 0 20px rgba(0,191,251,.35)}
[data-testid=stSidebar] [data-testid=stVerticalBlock]{gap:.25rem}
.st-key-nav_logout button{border:1px solid #173553!important;justify-content:center!important}
.nav-brand{display:flex;align-items:center;gap:12px;margin:4px 6px 18px}
.nav-brand .lg{font-size:38px;line-height:1;width:54px;height:54px;border-radius:50%;display:grid;place-items:center;
  background:radial-gradient(circle at 35% 30%,#1a7fd1,#07243f);border:2px solid #1fb6e8}
.nav-brand .nm{font-size:23px;font-weight:700;color:#fff;line-height:1.1}
.nav-brand .sb{font-size:16px;font-weight:600;color:#3ddc84}
.nav-banner{position:relative;height:150px;border-radius:16px;margin:16px 4px 10px;padding:14px;overflow:hidden;
  border:1px solid #1f6fbe;display:flex;align-items:flex-end;
  background:radial-gradient(circle at 78% 30%,rgba(47,155,255,.55),transparent 42%),linear-gradient(160deg,#0f6a32,#0a3d63)}
.nav-banner .tx{color:#fff;font-weight:800;font-size:20px;line-height:1.15;text-shadow:0 2px 6px rgba(0,0,0,.6)}
</style>"""

BADGE = ('{sel}::after{{content:"{txt}";position:absolute;right:14px;top:50%;transform:translateY(-50%);'
         'min-width:22px;height:22px;padding:0 6px;border-radius:999px;display:grid;place-items:center;'
         'font-size:12px;font-weight:700;color:#fff;background:{bg}}}')


@st.cache_data(show_spinner=False)
def _banner_b64():
    """Banner image ko base64 mein convert karta hai (sirf ek baar, cache ho jata hai)."""
    try:
        return base64.b64encode(BANNER_IMG.read_bytes()).decode()
    except FileNotFoundError:
        return None   # image na mile to purana gradient banner chalega


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def go_to(name):
    """Kisi bhi page par jao (jaise Dashboard ke 'View Full Map' button se)."""
    st.session_state["page"] = name


def render_sidebar(db, user, available):
    if st.session_state.get("page") not in available:
        st.session_state["page"] = available[0]
    current = st.session_state["page"]

    prefs = db.settings.find_one({"_id": user["id"]}) or {}
    unread = db.alerts.count_documents({"read": False}) if prefs.get("notifications", True) else 0

    dyn = BADGE.format(sel=".st-key-navwrap_manage_users button", txt="👑", bg="transparent")
    if unread:
        dyn += BADGE.format(sel=".st-key-navwrap_alerts button", txt=str(min(unread, 99)), bg="#ff4d4f")
    st.markdown(CSS + f"<style>{dyn}</style>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="nav-brand"><div class="lg">🌍</div><div><div class="nm">EarthScape</div>'
                    '<div class="sb">Climate Agency</div></div></div>', unsafe_allow_html=True)
        for name, icon in ITEMS:
            if name not in available:
                continue
            with st.container(key=f"navwrap_{_slug(name)}"):
                st.button(name, key=f"nav_{_slug(name)}", icon=icon,
                          type="primary" if name == current else "secondary",
                          on_click=go_to, args=(name,))
        if prefs.get("show_banner", True):
            b64 = _banner_b64()
            bg = (
                "background:linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(4,13,28,.75) 100%),"
                f"url(data:image/png;base64,{b64}) center/cover no-repeat;"
            ) if b64 else ""
            st.markdown(
                f'<div class="nav-banner" style="{bg}">'
                '<div class="tx">Together for<br>a Greener Planet</div></div>',
                unsafe_allow_html=True,
            )
        st.caption(f"Signed in as **{user['name']}** ({user['role']})")
        if st.button("Logout", key="nav_logout", icon=":material/logout:"):
            for k in [k for k in st.session_state if k != "splash_done"]:   # splash dobara na chale
                del st.session_state[k]
            st.rerun()
    return st.session_state["page"]