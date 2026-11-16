"""EarthScape splash screen: background + 2 logos + chalta hua loader (0% -> 100%)."""
import base64
import os
import time

import streamlit as st

# ---------------- settings (yahan sirf naam / size badalna hai) ----------------
BG_IMAGE = "Earth_bg.png"            # poori screen ka background
LOGO_1 = "Earth_logo.png"            # upar wala bara logo (globe / icon)
LOGO_2 = "Earth_Logo (2).png"        # uske neeche wala logo (EarthScape naam / wordmark)
LOGO_1_HEIGHT = 24                   # logo 1 ki height (screen ka % - vh)
LOGO_2_HEIGHT = 10                   # logo 2 ki height (vh)
SECONDS = 3.5                        # splash kitni der chale
# --------------------------------------------------------------------------------

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

STEPS = [(0, "Starting EarthScape..."), (25, "Connecting to database..."),
         (50, "Analyzing Climate Data..."), (80, "Preparing dashboard..."), (96, "Almost ready...")]

STYLE = """
<style>
[data-testid=stSidebar], [data-testid=stHeader], [data-testid=stToolbar] {{display:none !important}}
.es-bg {{position:fixed; inset:0; z-index:999990; background:#040d1c {bg} center/cover no-repeat}}
.es-logos {{position:fixed; z-index:999991; left:50%; top:44%; transform:translate(-50%,-50%);
           display:flex; flex-direction:column; align-items:center; gap:2.5vh}}
.es-logos img {{max-width:80vw; width:auto; object-fit:contain}}
.es-bar {{position:fixed; z-index:999991; left:50%; bottom:13vh; transform:translateX(-50%);
         width:min(62vw,760px); color:#fff; font-family:sans-serif}}
.es-text {{text-align:center; font-size:clamp(13px,1.5vw,24px); margin-bottom:1.4vh}}
.es-row {{display:flex; align-items:center; gap:14px}}
.es-track {{flex:1; height:clamp(10px,1.6vw,24px); border-radius:99px; background:rgba(255,255,255,.07);
           border:1px solid rgba(160,200,230,.35); overflow:hidden}}
.es-fill {{height:100%; border-radius:99px; background:linear-gradient(90deg,#00e5ff,#3ddc84 70%,#7bea4a);
          box-shadow:0 0 14px rgba(61,220,132,.7); transition:width .12s linear}}
.es-pct {{font-size:clamp(14px,1.8vw,28px); width:3.4em}}
</style>
"""


def _data_uri(name):
    """Image ko base64 mein badalta hai. File na mile to None (app crash nahi hoti)."""
    path = os.path.join(ASSETS, name)
    if not os.path.exists(path):
        return None
    mime = "image/png" if name.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def _bar(pct, msg):
    return (f'<div class="es-bar"><div class="es-text">{msg}</div><div class="es-row">'
            f'<div class="es-track"><div class="es-fill" style="width:{pct}%"></div></div>'
            f'<div class="es-pct">{pct}%</div></div></div>')


def splash_page(seconds=SECONDS):
    bg, l1, l2 = _data_uri(BG_IMAGE), _data_uri(LOGO_1), _data_uri(LOGO_2)
    logos = "".join(f'<img src="{src}" style="height:{h}vh">' for src, h in ((l1, LOGO_1_HEIGHT), (l2, LOGO_2_HEIGHT)) if src)
    top_box, bar_box = st.empty(), st.empty()      # images ek baar, sirf bar baar baar update
    top_box.markdown(STYLE.format(bg=f"url({bg})" if bg else "") + '<div class="es-bg"></div>'
                     f'<div class="es-logos">{logos}</div>', unsafe_allow_html=True)
    msg = STEPS[0][1]
    for pct in range(0, 101, 2):
        for start, text in STEPS:
            if pct >= start:
                msg = text
        bar_box.markdown(_bar(pct, msg), unsafe_allow_html=True)
        time.sleep(seconds / 51)
    time.sleep(0.3)
    bar_box.empty()
    top_box.empty()