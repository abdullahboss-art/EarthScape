"""EarthScape dark-green theme: CSS, inline SVG icons and small HTML helpers.

Matches the UI mock-up (deep navy background, glass cards, green gradient buttons).
"""
import streamlit as st

GREEN = "#10d9a0"
BLUE = "#3b82f6"

# ----------------------------- inline SVG icons -----------------------------
_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{s}" height="{s}" fill="none" '
        'stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{p}</svg>')

_PATHS = {
    "leaf": '<path d="M20 4C9 4 4 9 4 15a5 5 0 0 0 5 5c6 0 11-5 11-16z" fill="{c}" fill-opacity=".25"/>'
            '<path d="M4 20c2-6 6-10 12-12"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'
           '<path d="M9 13h6M9 17h6"/>',
    "chart": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'
             '<path d="M9 18v-3M12 18v-6M15 18v-4"/>',
    "plant": '<path d="M12 21v-9"/><path d="M12 12c0-4 3-6.5 8-6.5 0 4.2-3 6.5-8 6.5z"/>'
             '<path d="M12 15c0-3-2.2-5-6.5-5 0 3.2 2.2 5 6.5 5z"/><path d="M8 21h8"/>',
    "lines": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'
             '<path d="M9 12h3M9 15h6M9 18h6"/>',
    "headset": '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/>'
               '<rect x="17" y="14" width="4" height="6" rx="1.5"/><path d="M19 20a4 4 0 0 1-4 2h-2"/>',
}


def icon(name: str, size: int = 24, color: str = GREEN) -> str:
    return _SVG.format(s=size, c=color, p=_PATHS[name].replace("{c}", color))


GLOBE_SVG = (
    "<svg class='es-globe' viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'>"
    "<defs><radialGradient id='esg' cx='35%' cy='30%' r='78%'>"
    "<stop offset='0' stop-color='#6fd6ff'/><stop offset='.4' stop-color='#1c74c0'/>"
    "<stop offset='.78' stop-color='#0a2c58'/><stop offset='1' stop-color='#04122a'/></radialGradient>"
    "<clipPath id='esc'><circle cx='100' cy='100' r='98'/></clipPath></defs>"
    "<circle cx='100' cy='100' r='98' fill='url(#esg)'/>"
    "<g clip-path='url(#esc)' fill='#3fbf7a' fill-opacity='.78'>"
    "<path d='M38 72C52 54 80 52 92 68C98 84 82 94 72 106C60 118 48 102 40 92Z'/>"
    "<path d='M108 58C124 48 150 56 160 74C162 90 142 94 130 88C116 84 102 72 108 58Z'/>"
    "<path d='M94 122C110 112 136 118 142 136C144 156 120 170 104 162C90 152 86 134 94 122Z'/></g>"
    "<circle cx='100' cy='100' r='98' fill='none' stroke='#7fd3ff' stroke-opacity='.35' stroke-width='1.5'/>"
    "</svg>"
)

REPORT_ICON = {  # report key -> (svg name, accent colour)
    "climate": ("doc", "#10d9a0"),
    "regional": ("chart", "#3b82f6"),
    "environmental": ("plant", "#14d3b8"),
    "custom": ("lines", "#a78bfa"),
}

# --------------------------------- CSS --------------------------------------
CSS = """
<style>
:root{
  --bg:#06101d; --side:#081626; --card:#0c1c30; --card2:#10243b; --line:#1d3a5a;
  --text:#e6eef8; --muted:#8aa0b8; --green:#10d9a0; --green2:#0d9f6e; --blue:#3b82f6;
}
/* ---------- app shell ---------- */
.stApp{
  background:
    radial-gradient(900px 480px at 85% -8%, rgba(16,217,160,.10), transparent 60%),
    radial-gradient(800px 500px at -5% 105%, rgba(59,130,246,.10), transparent 60%),
    var(--bg);
  color:var(--text);
}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none !important;}
.block-container{padding-top:2rem;padding-bottom:3rem;max-width:1250px;}
h1,h2,h3,h4{color:var(--text);letter-spacing:.1px;}

/* ---------- page header ---------- */
.es-head{display:flex;align-items:center;gap:12px;margin:0 0 22px 0;}
.es-head h1{margin:0;padding:0;font-size:28px;font-weight:700;line-height:1.1;}
.es-head .es-sub{color:var(--muted);font-size:13px;margin-top:3px;}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#091a2e 0%,#06111f 100%);border-right:1px solid #12304d;}
[data-testid="stSidebar"] > div:first-child{padding-top:.6rem;}
.es-brand{display:flex;align-items:center;gap:11px;padding:6px 6px 22px 6px;}
.es-brand .logo{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;
  background:linear-gradient(145deg,rgba(16,217,160,.25),rgba(16,217,160,.05));border:1px solid rgba(16,217,160,.45);
  box-shadow:0 0 18px rgba(16,217,160,.25);}
.es-brand b{display:block;font-size:19px;color:var(--text);line-height:1.05;}
.es-brand small{display:block;color:var(--green);font-size:9.5px;letter-spacing:2.2px;margin-top:2px;}
[data-testid="stSidebar"] [data-testid="stRadio"] > label{display:none;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]{gap:0;width:100%;}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div{width:100%;}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]{
  width:100%;padding:9px 12px;border-radius:9px;cursor:pointer;transition:background .15s;margin:0;}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child{display:none;}  /* hide radio dot */
[data-testid="stSidebar"] label[data-testid="stRadioOption"] p{font-size:14px;color:var(--muted);margin:0;}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover{background:rgba(255,255,255,.05);}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:has(input:checked){
  background:linear-gradient(90deg,var(--green2),var(--green));box-shadow:0 4px 16px rgba(16,217,160,.28);}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:has(input:checked) p{color:#03231a;font-weight:700;}
.es-side-card{margin-top:26px;border-radius:12px;padding:14px;border:1px solid var(--line);
  background:radial-gradient(120px 90px at 85% 110%, rgba(60,170,255,.55), transparent 70%),
             linear-gradient(160deg,#0d2a45,#08182b);}
.es-side-card b{font-size:13px;color:var(--text);line-height:1.25;display:block;}
.es-side-card span{font-size:11px;color:var(--green);}

/* ---------- cards ---------- */
.es-card,
[class*="st-key-card_"],
[class*="st-key-rep_"]{
  background:linear-gradient(160deg,#0f2740 0%,#0a1b30 100%);
  border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px;
  box-shadow:0 8px 28px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.04);}
[class*="st-key-card_"] [data-testid="stVerticalBlock"]{gap:.7rem;}
.es-card-title{font-size:16px;font-weight:600;color:var(--text);margin:0 0 6px 0;}
.es-muted{color:var(--muted);font-size:13px;}

/* ---------- report cards ---------- */
[class*="st-key-rep_"]{text-align:center;padding:22px 14px 12px 14px;min-height:232px;
  transition:transform .15s, box-shadow .15s, border-color .15s;}
[class*="st-key-rep_"]:hover{transform:translateY(-3px);border-color:rgba(16,217,160,.55);
  box-shadow:0 14px 34px rgba(0,0,0,.4),0 0 22px rgba(16,217,160,.12);}
.es-rep{display:flex;flex-direction:column;align-items:center;gap:6px;}
.es-rep .tile{width:68px;height:68px;border-radius:16px;display:grid;place-items:center;margin-bottom:6px;}
.es-rep .t{font-size:15.5px;font-weight:600;color:var(--text);}
.es-rep .s{font-size:12.5px;color:var(--muted);}
[class*="st-key-rep_"] [data-testid="stDownloadButton"] button{
  background:transparent;border:none;box-shadow:none;color:var(--green);font-weight:600;font-size:13px;
  padding:2px 0;min-height:0;justify-content:center;}
[class*="st-key-rep_"] [data-testid="stDownloadButton"] button:hover{color:#6ff2cd;background:transparent;}
[class*="st-key-rep_"] [data-testid="stElementContainer"]{width:100% !important;}
[class*="st-key-rep_"] [data-testid="stDownloadButton"]{display:flex;justify-content:center;width:100%;}
[class*="st-key-rep_"] [data-testid="stDownloadButton"] button{width:100%;}

/* ---------- buttons / inputs ---------- */
.stButton > button[kind="primary"],
.stFormSubmitButton > button,
.stButton > button[kind="primaryFormSubmit"]{
  background:linear-gradient(90deg,var(--green2),var(--green));color:#03231a;font-weight:700;border:none;
  border-radius:9px;padding:.55rem 1.4rem;box-shadow:0 6px 18px rgba(16,217,160,.28);transition:filter .15s, transform .15s;}
.stButton > button[kind="primary"]:hover,.stFormSubmitButton > button:hover{filter:brightness(1.12);transform:translateY(-1px);color:#03231a;border:none;}
.stButton > button[kind="primary"] p,.stFormSubmitButton > button p{color:#03231a;font-weight:700;}
.stFormSubmitButton > button{width:100%;}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"] > div{
  background:#0e2339 !important;border-color:var(--line) !important;border-radius:9px !important;}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within,[data-baseweb="select"] > div:focus-within{
  border-color:var(--green) !important;box-shadow:0 0 0 1px var(--green) !important;}
[data-testid="stForm"]{border:none;padding:0;background:transparent;}
label p,[data-testid="stWidgetLabel"] p{color:var(--muted);font-size:13px;}

/* ---------- FAQ expanders ---------- */
[data-testid="stExpander"]{background:#0e2339;border:1px solid var(--line) !important;border-radius:10px;margin-bottom:8px;}
[data-testid="stExpander"] summary{padding:.65rem .9rem;}
[data-testid="stExpander"] summary p{font-size:14px;color:var(--text);}
[data-testid="stExpander"] summary:hover{background:rgba(255,255,255,.03);}
[data-testid="stExpander"] details{border:none;}

/* ---------- export bar ---------- */
.st-key-card_export{padding:14px 20px;}
.st-key-card_export [data-testid="stHorizontalBlock"]{align-items:center;}

/* ---------- support banner ---------- */
.es-banner{position:relative;overflow:hidden;display:flex;align-items:center;gap:18px;padding:22px 26px;min-height:104px;
  border-radius:14px;border:1px solid var(--line);
  background:linear-gradient(100deg,#0d2742 0%,#0a1c33 60%,#0a2a4a 100%);}
.es-banner .ic{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;flex:0 0 auto;
  background:rgba(16,217,160,.10);border:1px solid rgba(16,217,160,.4);}
.es-banner b{display:block;font-size:16px;color:var(--text);}
.es-banner span{font-size:13px;color:var(--muted);}
.es-globe{position:absolute;right:-30px;top:-38px;width:200px;height:200px;
  filter:drop-shadow(0 0 22px rgba(70,170,255,.55));}
.st-key-card_faq,.st-key-card_contact{min-height:372px;}

/* ---------- metric cards (performance) ---------- */
[data-testid="stMetric"]{
  background:linear-gradient(160deg,#0f2740 0%,#0a1b30 100%);border:1px solid var(--line);border-radius:14px;
  padding:16px 20px;box-shadow:0 8px 28px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.04);}
[data-testid="stMetricLabel"] p{color:var(--muted);font-size:13px;}
[data-testid="stMetricValue"]{font-size:30px;font-weight:700;color:var(--text);}
[data-testid="stMetricDelta"]{color:var(--muted) !important;font-size:12px;}
.st-key-card_perf{margin-top:6px;}

/* ---------- misc ---------- */
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:10px;overflow:hidden;}
[data-testid="stAlert"]{border-radius:10px;}
::-webkit-scrollbar{width:8px;height:8px;} ::-webkit-scrollbar-thumb{background:#1d3a5a;border-radius:8px;}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    sub = f"<div class='es-sub'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"<div class='es-head'>{icon('leaf', 34)}<div><h1>{title}</h1>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def report_card_html(key: str, title: str, sub: str) -> str:
    name, color = REPORT_ICON[key]
    tile_style = (f"background:linear-gradient(145deg,{color}33,{color}0d);"
                  f"border:1px solid {color}66;box-shadow:0 0 20px {color}30;")
    return (f"<div class='es-rep'><div class='tile' style='{tile_style}'>{icon(name, 34, color)}</div>"
            f"<div class='t'>{title}</div><div class='s'>{sub}</div></div>")
