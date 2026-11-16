# # """EarthScape Climate Agency - the whole website in Python (Streamlit).
# # Run:  streamlit run app.py --theme.base dark

# # Folder structure:
# #     app.py
# #     support_page.py
# #     settings_page.py
# #     assets/Emerald Earth Eco Landscape.png
# #     assets/support_globe.png
# #     .streamlit/secrets.toml
# # Streamlit 1.39+ chahiye (st.container(key=...) aur button icons).
# # """
# # # ------------------------------------------------------------------ imports (sab ek jagah)
# # import base64
# # import datetime
# # import html
# # import re
# # import sys
# # from pathlib import Path

# # import pandas as pd
# # import streamlit as st
# # from bson import ObjectId

# # sys.path.insert(0, str(Path(__file__).resolve().parent))   # app.py ke folder se Login.py / signup.py / analytics.py / splash.py milein

# # import analytics
# # from Alert import alerts_page                          # Alerts page (Alert.py)
# # from Climite import climate_map_page                   # Climate Map page
# # from Dashboard import dashboard_page
# # from Extra_pages import analytics_page, profile_page, reports_page
# # from settings_page import settings_page                # Settings page (settings_page.py)
# # from Data_Ingestion import ingestion_page              # Data Management -> Ingestion tab
# # from data_storage import storage_page                  # Data Management -> Storage tab
# # from data_processing import processing_page            # Data Management -> Processing tab
# # from Login import login_page
# # from signup import register_page
# # from splash import splash_page
# # from support_page import support_page                  # Support & Feedback page (support_page.py)

# # st.set_page_config(page_title="EarthScape Climate Agency", page_icon="🌍", layout="wide")
# # db = analytics.get_db()

# # CSS = """<style>
# # .stApp{background:radial-gradient(1100px 520px at 18% -8%,#0c2f5a 0%,transparent 62%),#040d1c}
# # [data-testid=stSidebar]{background:#061424;border-right:1px solid #173553}
# # [data-testid=stHeader]{background:transparent}
# # [data-testid=stVerticalBlockBorderWrapper]{background:rgba(10,27,46,.88);border-color:#173553!important;border-radius:14px}
# # .kpi{border-radius:14px;padding:16px;border:1px solid;display:grid;grid-template-columns:54px 1fr;gap:4px 12px;align-items:center;min-height:108px}
# # .kpi .ico{font-size:34px;text-align:center}.kpi .lab{color:#d3e0ee;font-size:13px}.kpi .val{font-size:27px;font-weight:700;color:#fff;line-height:1.15}
# # .kpi .val small{font-size:14px;font-weight:600}.kpi .chg{grid-column:1/-1;font-size:12px;color:#8ea6bf}
# # .kpi.t{background:linear-gradient(135deg,#3b1417,#14131f);border-color:#7a2a2c}
# # .kpi.c{background:linear-gradient(135deg,#0b3568,#0a1e3a);border-color:#1f6fbe}
# # .kpi.a{background:linear-gradient(135deg,#0d4a1c,#0b2315);border-color:#2a8a3a}
# # .kpi.s{background:linear-gradient(135deg,#075a8c,#0a2740);border-color:#1f88c8}
# # .alert{display:flex;gap:12px;align-items:center;padding:10px;border-radius:10px;background:#0b2036;border:1px solid #112f4c;margin-bottom:8px}
# # .alert .i{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;font-size:18px;background:#4a1a1d;flex:none}
# # .alert .i.warning{background:#4a3510}.alert b{display:block}.alert span{color:#8ea6bf;font-size:12px}.alert .w{margin-left:auto;color:#8ea6bf;font-size:12px;white-space:nowrap}
# # .pred{border:1px solid #3a2a66;background:#171033;border-radius:10px;padding:8px 16px;text-align:center;font-size:26px;font-weight:700}
# # .pred small{display:block;font-size:12px;color:#8ea6bf;font-weight:400}
# # .brand{text-align:center;font-size:26px;font-weight:700}.brand span{color:#3ddc84}
# # .tag{text-align:center;color:#8ea6bf;margin-bottom:14px}
# # div.stButton>button[kind=primary],div.stFormSubmitButton>button{background:linear-gradient(90deg,#58df57,#00bffb);color:#06210f;border:0;font-weight:700}
# # </style>"""
# # st.markdown(CSS, unsafe_allow_html=True)


# # # ================================================================== SIDEBAR NAVIGATION
# # BANNER_IMG = Path(__file__).parent / "assets" / "Emerald Earth Eco Landscape.png"

# # # (page name, material icon).  Sirf wahi dikhte hain jo PAGES mein hon.
# # ITEMS = [
# #     ("Dashboard", ":material/home:"),
# #     ("Climate Map", ":material/map:"),
# #     ("Data Management", ":material/storage:"),
# #     ("Data Analytics", ":material/bar_chart:"),
# #     ("Data Upload", ":material/cloud_upload:"),
# #     ("Reports", ":material/description:"),
# #     ("Alerts", ":material/notifications:"),
# #     ("Profile", ":material/person:"),
# #     ("Settings", ":material/settings:"),
# #     ("Support & Feedback", ":material/headset_mic:"),
# #     ("Manage Users", ":material/groups:"),
# # ]

# # NAV_CSS = """<style>
# # [data-testid=stSidebar]{background:linear-gradient(180deg,#06182c 0%,#040d1c 100%);border-right:1px solid #173553}
# # [data-testid=stSidebar] .stButton{width:100%}
# # [data-testid=stSidebar] .stButton>button{position:relative;width:100%;justify-content:flex-start;gap:.7rem;
# #   background:transparent;border:0;box-shadow:none;color:#d8e4f2;font-size:15px;padding:.62rem .9rem;border-radius:12px}
# # [data-testid=stSidebar] .stButton>button div{justify-content:flex-start;text-align:left}
# # [data-testid=stSidebar] .stButton>button:hover{background:rgba(0,191,251,.10);color:#fff}
# # [data-testid=stSidebar] .stButton>button[kind=primary]{background:linear-gradient(90deg,#58df57,#00bffb);
# #   color:#06210f;font-weight:700;box-shadow:0 0 20px rgba(0,191,251,.35)}
# # [data-testid=stSidebar] [data-testid=stVerticalBlock]{gap:.25rem}
# # .st-key-nav_logout button{border:1px solid #173553!important;justify-content:center!important}
# # .nav-brand{display:flex;align-items:center;gap:12px;margin:4px 6px 18px}
# # .nav-brand .lg{font-size:38px;line-height:1;width:54px;height:54px;border-radius:50%;display:grid;place-items:center;
# #   background:radial-gradient(circle at 35% 30%,#1a7fd1,#07243f);border:2px solid #1fb6e8}
# # .nav-brand .nm{font-size:23px;font-weight:700;color:#fff;line-height:1.1}
# # .nav-brand .sb{font-size:16px;font-weight:600;color:#3ddc84}
# # .nav-banner{position:relative;height:150px;border-radius:16px;margin:16px 4px 10px;padding:14px;overflow:hidden;
# #   border:1px solid #1f6fbe;display:flex;align-items:flex-end;
# #   background:radial-gradient(circle at 78% 30%,rgba(47,155,255,.55),transparent 42%),linear-gradient(160deg,#0f6a32,#0a3d63)}
# # .nav-banner .tx{color:#fff;font-weight:800;font-size:20px;line-height:1.15;text-shadow:0 2px 6px rgba(0,0,0,.6)}
# # </style>"""

# # BADGE = ('{sel}::after{{content:"{txt}";position:absolute;right:14px;top:50%;transform:translateY(-50%);'
# #          'min-width:22px;height:22px;padding:0 6px;border-radius:999px;display:grid;place-items:center;'
# #          'font-size:12px;font-weight:700;color:#fff;background:{bg}}}')


# # @st.cache_data(show_spinner=False)
# # def _banner_b64(mtime):
# #     """Banner image ko base64 mein convert karta hai. mtime cache key hai, isliye image badalne par refresh ho jata hai."""
# #     return base64.b64encode(BANNER_IMG.read_bytes()).decode()


# # def _banner_css():
# #     if not BANNER_IMG.exists():
# #         return ""   # image na mile to purana gradient banner chalega
# #     b64 = _banner_b64(BANNER_IMG.stat().st_mtime)
# #     return (".nav-banner{background:linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(4,13,28,.75) 100%),"
# #             f"url('data:image/png;base64,{b64}') center/cover no-repeat !important}}")


# # def _slug(name):
# #     return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# # def go_to(name):
# #     """Kisi bhi page par jao (jaise Dashboard ke 'View Full Map' button se)."""
# #     st.session_state["page"] = name


# # def render_sidebar(db, user, available):
# #     if st.session_state.get("page") not in available:
# #         st.session_state["page"] = available[0]
# #     current = st.session_state["page"]

# #     # settings_page.py in keys ko set karta hai: "notifications" aur "show_banner"
# #     prefs = db.settings.find_one({"_id": user["id"]}) or {}
# #     unread = db.alerts.count_documents({"read": False}) if prefs.get("notifications", True) else 0

# #     dyn = BADGE.format(sel=".st-key-navwrap_manage_users button", txt="👑", bg="transparent")
# #     if unread:
# #         dyn += BADGE.format(sel=".st-key-navwrap_alerts button", txt=str(min(unread, 99)), bg="#ff4d4f")
# #     dyn += _banner_css()
# #     st.markdown(NAV_CSS + f"<style>{dyn}</style>", unsafe_allow_html=True)

# #     with st.sidebar:
# #         st.markdown('<div class="nav-brand"><div class="lg">🌍</div><div><div class="nm">EarthScape</div>'
# #                     '<div class="sb">Climate Agency</div></div></div>', unsafe_allow_html=True)
# #         for name, icon in ITEMS:
# #             if name not in available:
# #                 continue
# #             with st.container(key=f"navwrap_{_slug(name)}"):
# #                 st.button(name, key=f"nav_{_slug(name)}", icon=icon,
# #                           type="primary" if name == current else "secondary",
# #                           on_click=go_to, args=(name,))
# #         if prefs.get("show_banner", True):
# #             st.markdown('<div class="nav-banner"><div class="tx">Together for<br>a Greener Planet</div></div>',
# #                         unsafe_allow_html=True)
# #         st.caption(f"Signed in as **{user['name']}** ({user['role']})")
# #         if st.button("Logout", key="nav_logout", icon=":material/logout:"):
# #             for k in [k for k in st.session_state if k != "splash_done"]:   # splash dobara na chale
# #                 del st.session_state[k]
# #             st.rerun()
# #     return st.session_state["page"]


# # # ================================================================== helpers
# # def ago(t):
# #     s = (datetime.datetime.utcnow() - t).total_seconds()
# #     if s < 3600:
# #         return f"{max(1, int(s // 60))}m ago"
# #     if s < 86400:
# #         return f"{int(s // 3600)}h ago"
# #     return f"{int(s // 86400)}d ago" if s < 86400 * 90 else t.strftime("%d %b %Y")


# # def get_thresholds():
# #     d = db.thresholds.find_one({"_id": "global"})
# #     return d["values"] if d else analytics.DEFAULT_TH


# # # ------------------------------------------------------------------ upload
# # def upload_page(user):
# #     st.title("⬆️ Data Upload")
# #     if user["role"] == "viewer":
# #         st.warning("Your account is read-only (viewer). Ask an administrator for the analyst role to upload data.")
# #     else:
# #         a, b = st.columns(2)
# #         with a.container(border=True):
# #             st.subheader("Upload CSV / Excel / JSON file")
# #             st.caption("Columns: date, station, temperature, co2, humidity, rainfall, sea_level, aqi. "
# #                        "Only the first three are required. Missing values are filled automatically.")
# #             f = st.file_uploader("Drag and drop your file here", type=["csv", "json", "xlsx"])
# #             if f and st.button("Upload & analyse", type="primary"):
# #                 try:
# #                     name = f.name.lower()
# #                     df = pd.read_csv(f) if name.endswith(".csv") else pd.read_excel(f) if name.endswith(".xlsx") else pd.read_json(f)
# #                     df = analytics.clean(df)
# #                     n = analytics.save(db, df)
# #                     na = analytics.scan(db, df, get_thresholds())
# #                     db.uploads.insert_one({"user": user["id"], "name": f.name, "size": f.size, "rows": n,
# #                                            "time": datetime.datetime.utcnow()})
# #                     st.success(f"{n:,} rows imported. {na} new alert(s) created.")
# #                 except Exception as e:
# #                     st.error(str(e))
# #         with b.container(border=True):
# #             st.subheader("Send a live sensor reading")
# #             with st.form("live"):
# #                 station = st.text_input("Station", "Karachi")
# #                 c = st.columns(3)
# #                 temp = c[0].number_input("Temperature °C", value=30.0)
# #                 co2 = c[1].number_input("CO₂ ppm", value=420.0)
# #                 aqi = c[2].number_input("AQI", value=50.0)
# #                 if st.form_submit_button("Send reading"):
# #                     rec = {"date": datetime.datetime.utcnow(), "station": station.strip(), "temperature": temp, "co2": co2, "aqi": aqi,
# #                            "humidity": None, "rainfall": None, "sea_level": None}
# #                     if not rec["station"]:
# #                         st.error("Station is required")
# #                     else:
# #                         db.records.insert_one(dict(rec))
# #                         al = analytics.alert_docs(rec, get_thresholds())
# #                         if al:
# #                             db.alerts.insert_many(al)
# #                             st.error("ALERT: " + "; ".join(x["message"] for x in al))
# #                         else:
# #                             st.success("Reading saved, no alerts.")
# #     with st.container(border=True):
# #         st.subheader("🗂️ Recent Uploads")
# #         ups = list(db.uploads.find().sort("time", -1).limit(5))
# #         if not ups:
# #             st.caption("No uploads yet.")
# #         for u_ in ups:
# #             size = f"{u_['size'] / 1024:,.0f} KB" if u_["size"] < 1024 ** 2 else f"{u_['size'] / 1024 ** 2:.1f} MB"
# #             st.markdown(f'<div class="alert"><div class="i info">📄</div><div><b>{html.escape(u_["name"])}</b>'
# #                         f'<span>{size} · {u_["rows"]:,} rows</span></div><div class="w">{ago(u_["time"])}</div></div>',
# #                         unsafe_allow_html=True)
# #     with st.container(border=True):
# #         st.subheader("Latest records")
# #         rows = list(db.records.find({}, {"_id": 0}).sort("date", -1).limit(10))
# #         st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True) if rows else st.caption("No data yet")


# # # ------------------------------------------------------------------ data management (3 tabs, 1 sidebar entry)
# # def data_management_page(user):
# #     st.title("🗄️ Data Management")
# #     t1, t2, t3 = st.tabs(["📤 Ingestion", "💾 Storage", "🌦️ Processing"])
# #     with t1:
# #         ingestion_page(db, user)
# #     with t2:
# #         storage_page(db, user)
# #     with t3:
# #         processing_page(db, user)


# # # ------------------------------------------------------------------ admin users
# # def users_page(user):
# #     st.title("👥 Manage Users")
# #     with st.container(border=True):
# #         for u in db.users.find():
# #             c = st.columns([3, 3, 2, 1])
# #             c[0].write(u["name"])
# #             c[1].write(u["email"])
# #             if str(u["_id"]) == user["id"]:
# #                 c[2].write(f"{u['role']} (you)")
# #                 continue
# #             new = c[2].selectbox("Role", ["admin", "analyst", "viewer"], index=["admin", "analyst", "viewer"].index(u["role"]),
# #                                  key=f"role_{u['_id']}", label_visibility="collapsed")
# #             if new != u["role"]:
# #                 db.users.update_one({"_id": u["_id"]}, {"$set": {"role": new}})
# #                 st.rerun()
# #             if c[3].button("Delete", key=f"del_{u['_id']}"):
# #                 db.users.delete_one({"_id": u["_id"]})
# #                 st.rerun()
# #     with st.container(border=True):
# #         st.subheader("User feedback & support requests")
# #         fb = list(db.feedback.find({}, {"_id": 0}).sort("time", -1).limit(30))
# #         st.dataframe(pd.DataFrame(fb), width="stretch", hide_index=True) if fb else st.caption("Nothing yet")


# # # ------------------------------------------------------------------ main
# # if "splash_done" not in st.session_state:
# #     if st.session_state.get("user"):           # pehle se login hai -> splash skip, seedha dashboard
# #         st.session_state["splash_done"] = True
# #     else:                                      # login nahi hai -> splash (loader), phir login page
# #         splash_box = st.empty()
# #         with splash_box.container():
# #             splash_page()
# #         splash_box.empty()
# #         st.session_state["splash_done"] = True
# #         st.rerun()

# # user = st.session_state.get("user")
# # if user and not db.users.find_one({"_id": ObjectId(user["id"])}):   # admin ne delete kar diya -> logout
# #     st.session_state.pop("user", None)
# #     user = None
# # if not user:                                    # loader ke baad login / signup
# #     if st.session_state.get("auth_view", "login") == "register":
# #         register_page(db)                       # signup.py
# #     else:
# #         login_page(db)                          # login.py
# #     st.stop()

# # PAGES = {"Dashboard": dashboard_page,                           # Dashboard.py (live data)
# #          "Climate Map": lambda u: climate_map_page(db, u),
# #          "Data Analytics": lambda u: analytics_page(db, u),
# #          "Data Upload": upload_page,
# #          "Data Management": data_management_page,               # Ingestion + Storage + Processing (tabs)
# #          "Reports": lambda u: reports_page(db, u),
# #          "Alerts": lambda u: alerts_page(db, u),                # Alert.py ka page
# #          "Profile": lambda u: profile_page(db, u),
# #          "Settings": lambda u: settings_page(db, u),            # settings_page.py
# #          "Support & Feedback": lambda u: support_page(db, u),   # support_page.py (email wala)
# #          }
# # if user["role"] == "admin":
# #     PAGES["Manage Users"] = users_page

# # choice = render_sidebar(db, user, list(PAGES))
# # PAGES[choice](user)

# """EarthScape Climate Agency - the whole website in Python (Streamlit).
# Run:  streamlit run app.py --theme.base dark

# Folder structure:
#     app.py
#     support_page.py
#     settings_page.py
#     assets/Emerald Earth Eco Landscape.png
#     assets/support_globe.png
#     .streamlit/secrets.toml
# Streamlit 1.39+ chahiye (st.container(key=...) aur button icons).
# """
# # ------------------------------------------------------------------ imports (sab ek jagah)
# import base64
# import datetime
# import html
# import re
# import sys
# from pathlib import Path

# import pandas as pd
# import streamlit as st
# from bson import ObjectId

# sys.path.insert(0, str(Path(__file__).resolve().parent))   # app.py ke folder se Login.py / signup.py / analytics.py / splash.py milein

# import analytics
# from Alert import alerts_page                          # Alerts page (Alert.py)
# from Climite import climate_map_page                   # Climate Map page
# from Dashboard import dashboard_page
# from Extra_pages import analytics_page, profile_page, reports_page
# from settings_page import settings_page                # Settings page (settings_page.py)
# from Data_Ingestion import ingestion_page              # Data Management -> Ingestion tab
# from data_storage import storage_page                  # Data Management -> Storage tab
# from data_processing import processing_page            # Data Management -> Processing tab
# from Login import login_page
# from signup import register_page
# from splash import splash_page
# from support_page import support_page                  # Support & Feedback page (support_page.py)
# import bigdata_pages                                   # Pipeline, Stream, Satellite, Roles, Alert Rules, Tableau
# import backup_security                                   # encrypted backups + security page
# import performance_page                                # Performance Monitor page

# st.set_page_config(page_title="EarthScape Climate Agency", page_icon="🌍", layout="wide")
# db = analytics.get_db()

# CSS = """<style>
# .stApp{background:radial-gradient(1100px 520px at 18% -8%,#0c2f5a 0%,transparent 62%),#040d1c}
# [data-testid=stSidebar]{background:#061424;border-right:1px solid #173553}
# [data-testid=stHeader]{background:transparent}
# [data-testid=stVerticalBlockBorderWrapper]{background:rgba(10,27,46,.88);border-color:#173553!important;border-radius:14px}
# .kpi{border-radius:14px;padding:16px;border:1px solid;display:grid;grid-template-columns:54px 1fr;gap:4px 12px;align-items:center;min-height:108px}
# .kpi .ico{font-size:34px;text-align:center}.kpi .lab{color:#d3e0ee;font-size:13px}.kpi .val{font-size:27px;font-weight:700;color:#fff;line-height:1.15}
# .kpi .val small{font-size:14px;font-weight:600}.kpi .chg{grid-column:1/-1;font-size:12px;color:#8ea6bf}
# .kpi.t{background:linear-gradient(135deg,#3b1417,#14131f);border-color:#7a2a2c}
# .kpi.c{background:linear-gradient(135deg,#0b3568,#0a1e3a);border-color:#1f6fbe}
# .kpi.a{background:linear-gradient(135deg,#0d4a1c,#0b2315);border-color:#2a8a3a}
# .kpi.s{background:linear-gradient(135deg,#075a8c,#0a2740);border-color:#1f88c8}
# .alert{display:flex;gap:12px;align-items:center;padding:10px;border-radius:10px;background:#0b2036;border:1px solid #112f4c;margin-bottom:8px}
# .alert .i{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;font-size:18px;background:#4a1a1d;flex:none}
# .alert .i.warning{background:#4a3510}.alert b{display:block}.alert span{color:#8ea6bf;font-size:12px}.alert .w{margin-left:auto;color:#8ea6bf;font-size:12px;white-space:nowrap}
# .pred{border:1px solid #3a2a66;background:#171033;border-radius:10px;padding:8px 16px;text-align:center;font-size:26px;font-weight:700}
# .pred small{display:block;font-size:12px;color:#8ea6bf;font-weight:400}
# .brand{text-align:center;font-size:26px;font-weight:700}.brand span{color:#3ddc84}
# .tag{text-align:center;color:#8ea6bf;margin-bottom:14px}
# div.stButton>button[kind=primary],div.stFormSubmitButton>button{background:linear-gradient(90deg,#58df57,#00bffb);color:#06210f;border:0;font-weight:700}
# </style>"""
# st.markdown(CSS, unsafe_allow_html=True)


# # ================================================================== SIDEBAR NAVIGATION
# BANNER_IMG = Path(__file__).parent / "assets" / "Emerald Earth Eco Landscape.png"

# # (page name, material icon).  Sirf wahi dikhte hain jo PAGES mein hon.
# ITEMS = [
#     ("Dashboard", ":material/home:"),
#     ("Climate Map", ":material/map:"),
#     ("Data Management", ":material/storage:"),
#     ("Data Analytics", ":material/bar_chart:"),
#     ("Data Upload", ":material/cloud_upload:"),
#     ("Pipeline Monitor", ":material/hub:"),
#     ("Live Stream", ":material/sensors:"),
#     ("Satellite Imagery", ":material/satellite_alt:"),
#     ("Tableau", ":material/insights:"),
#     ("Reports", ":material/description:"),
#     ("Alerts", ":material/notifications:"),
#     ("Alert Rules", ":material/rule:"),
#     ("Profile", ":material/person:"),
#     ("Settings", ":material/settings:"),
#     ("Support & Feedback", ":material/headset_mic:"),
#     ("Manage Users", ":material/groups:"),
#     ("Roles & Permissions", ":material/admin_panel_settings:"),
#     ("Performance Monitor", ":material/speed:"),
#     ("Backup & Security", ":material/shield:"),
# ]

# NAV_CSS = """<style>
# [data-testid=stSidebar]{background:linear-gradient(180deg,#06182c 0%,#040d1c 100%);border-right:1px solid #173553}
# [data-testid=stSidebar] .stButton{width:100%}
# [data-testid=stSidebar] .stButton>button{position:relative;width:100%;justify-content:flex-start;gap:.7rem;
#   background:transparent;border:0;box-shadow:none;color:#d8e4f2;font-size:15px;padding:.62rem .9rem;border-radius:12px}
# [data-testid=stSidebar] .stButton>button div{justify-content:flex-start;text-align:left}
# [data-testid=stSidebar] .stButton>button:hover{background:rgba(0,191,251,.10);color:#fff}
# [data-testid=stSidebar] .stButton>button[kind=primary]{background:linear-gradient(90deg,#58df57,#00bffb);
#   color:#06210f;font-weight:700;box-shadow:0 0 20px rgba(0,191,251,.35)}
# [data-testid=stSidebar] [data-testid=stVerticalBlock]{gap:.25rem}
# .st-key-nav_logout button{border:1px solid #173553!important;justify-content:center!important}
# .nav-brand{display:flex;align-items:center;gap:12px;margin:4px 6px 18px}
# .nav-brand .lg{font-size:38px;line-height:1;width:54px;height:54px;border-radius:50%;display:grid;place-items:center;
#   background:radial-gradient(circle at 35% 30%,#1a7fd1,#07243f);border:2px solid #1fb6e8}
# .nav-brand .nm{font-size:23px;font-weight:700;color:#fff;line-height:1.1}
# .nav-brand .sb{font-size:16px;font-weight:600;color:#3ddc84}
# .nav-banner{position:relative;height:150px;border-radius:16px;margin:16px 4px 10px;padding:14px;overflow:hidden;
#   border:1px solid #1f6fbe;display:flex;align-items:flex-end;
#   background:radial-gradient(circle at 78% 30%,rgba(47,155,255,.55),transparent 42%),linear-gradient(160deg,#0f6a32,#0a3d63)}
# .nav-banner .tx{color:#fff;font-weight:800;font-size:20px;line-height:1.15;text-shadow:0 2px 6px rgba(0,0,0,.6)}
# </style>"""

# BADGE = ('{sel}::after{{content:"{txt}";position:absolute;right:14px;top:50%;transform:translateY(-50%);'
#          'min-width:22px;height:22px;padding:0 6px;border-radius:999px;display:grid;place-items:center;'
#          'font-size:12px;font-weight:700;color:#fff;background:{bg}}}')


# @st.cache_data(show_spinner=False)
# def _banner_b64(mtime):
#     """Banner image ko base64 mein convert karta hai. mtime cache key hai, isliye image badalne par refresh ho jata hai."""
#     return base64.b64encode(BANNER_IMG.read_bytes()).decode()


# def _banner_css():
#     if not BANNER_IMG.exists():
#         return ""   # image na mile to purana gradient banner chalega
#     b64 = _banner_b64(BANNER_IMG.stat().st_mtime)
#     return (".nav-banner{background:linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(4,13,28,.75) 100%),"
#             f"url('data:image/png;base64,{b64}') center/cover no-repeat !important}}")


# def _slug(name):
#     return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# def go_to(name):
#     """Kisi bhi page par jao (jaise Dashboard ke 'View Full Map' button se)."""
#     st.session_state["page"] = name


# def render_sidebar(db, user, available):
#     if st.session_state.get("page") not in available:
#         st.session_state["page"] = available[0]
#     current = st.session_state["page"]

#     # settings_page.py in keys ko set karta hai: "notifications" aur "show_banner"
#     prefs = db.settings.find_one({"_id": user["id"]}) or {}
#     unread = db.alerts.count_documents({"read": False}) if prefs.get("notifications", True) else 0

#     dyn = BADGE.format(sel=".st-key-navwrap_manage_users button", txt="👑", bg="transparent")
#     if unread:
#         dyn += BADGE.format(sel=".st-key-navwrap_alerts button", txt=str(min(unread, 99)), bg="#ff4d4f")
#     dyn += _banner_css()
#     st.markdown(NAV_CSS + f"<style>{dyn}</style>", unsafe_allow_html=True)

#     with st.sidebar:
#         st.markdown('<div class="nav-brand"><div class="lg">🌍</div><div><div class="nm">EarthScape</div>'
#                     '<div class="sb">Climate Agency</div></div></div>', unsafe_allow_html=True)
#         for name, icon in ITEMS:
#             if name not in available:
#                 continue
#             with st.container(key=f"navwrap_{_slug(name)}"):
#                 st.button(name, key=f"nav_{_slug(name)}", icon=icon,
#                           type="primary" if name == current else "secondary",
#                           on_click=go_to, args=(name,))
#         if prefs.get("show_banner", True):
#             st.markdown('<div class="nav-banner"><div class="tx">Together for<br>a Greener Planet</div></div>',
#                         unsafe_allow_html=True)
#         st.caption(f"Signed in as **{user['name']}** ({user['role']})")
#         if st.button("Logout", key="nav_logout", icon=":material/logout:"):
#             for k in [k for k in st.session_state if k != "splash_done"]:   # splash dobara na chale
#                 del st.session_state[k]
#             st.rerun()
#     return st.session_state["page"]


# # ================================================================== helpers
# def ago(t):
#     s = (datetime.datetime.utcnow() - t).total_seconds()
#     if s < 3600:
#         return f"{max(1, int(s // 60))}m ago"
#     if s < 86400:
#         return f"{int(s // 3600)}h ago"
#     return f"{int(s // 86400)}d ago" if s < 86400 * 90 else t.strftime("%d %b %Y")


# def get_thresholds():
#     d = db.thresholds.find_one({"_id": "global"})
#     return d["values"] if d else analytics.DEFAULT_TH


# # ------------------------------------------------------------------ upload
# def upload_page(user):
#     st.title("⬆️ Data Upload")
#     if user["role"] == "viewer":
#         st.warning("Your account is read-only (viewer). Ask an administrator for the analyst role to upload data.")
#     else:
#         a, b = st.columns(2)
#         with a.container(border=True):
#             st.subheader("Upload CSV / Excel / JSON file")
#             st.caption("Columns: date, station, temperature, co2, humidity, rainfall, sea_level, aqi. "
#                        "Only the first three are required. Missing values are filled automatically.")
#             f = st.file_uploader("Drag and drop your file here", type=["csv", "json", "xlsx"])
#             if f and st.button("Upload & analyse", type="primary"):
#                 try:
#                     name = f.name.lower()
#                     df = pd.read_csv(f) if name.endswith(".csv") else pd.read_excel(f) if name.endswith(".xlsx") else pd.read_json(f)
#                     df = analytics.clean(df)
#                     n = analytics.save(db, df)
#                     na = analytics.scan(db, df, get_thresholds())
#                     db.uploads.insert_one({"user": user["id"], "name": f.name, "size": f.size, "rows": n,
#                                            "time": datetime.datetime.utcnow()})
#                     st.success(f"{n:,} rows imported. {na} new alert(s) created.")
#                 except Exception as e:
#                     st.error(str(e))
#         with b.container(border=True):
#             st.subheader("Send a live sensor reading")
#             with st.form("live"):
#                 station = st.text_input("Station", "Karachi")
#                 c = st.columns(3)
#                 temp = c[0].number_input("Temperature °C", value=30.0)
#                 co2 = c[1].number_input("CO₂ ppm", value=420.0)
#                 aqi = c[2].number_input("AQI", value=50.0)
#                 if st.form_submit_button("Send reading"):
#                     rec = {"date": datetime.datetime.utcnow(), "station": station.strip(), "temperature": temp, "co2": co2, "aqi": aqi,
#                            "humidity": None, "rainfall": None, "sea_level": None}
#                     if not rec["station"]:
#                         st.error("Station is required")
#                     else:
#                         db.records.insert_one(dict(rec))
#                         al = analytics.alert_docs(rec, get_thresholds())
#                         if al:
#                             db.alerts.insert_many(al)
#                             st.error("ALERT: " + "; ".join(x["message"] for x in al))
#                         else:
#                             st.success("Reading saved, no alerts.")
#     with st.container(border=True):
#         st.subheader("🗂️ Recent Uploads")
#         ups = list(db.uploads.find().sort("time", -1).limit(5))
#         if not ups:
#             st.caption("No uploads yet.")
#         for u_ in ups:
#             size = f"{u_['size'] / 1024:,.0f} KB" if u_["size"] < 1024 ** 2 else f"{u_['size'] / 1024 ** 2:.1f} MB"
#             st.markdown(f'<div class="alert"><div class="i info">📄</div><div><b>{html.escape(u_["name"])}</b>'
#                         f'<span>{size} · {u_["rows"]:,} rows</span></div><div class="w">{ago(u_["time"])}</div></div>',
#                         unsafe_allow_html=True)
#     with st.container(border=True):
#         st.subheader("Latest records")
#         rows = list(db.records.find({}, {"_id": 0}).sort("date", -1).limit(10))
#         st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True) if rows else st.caption("No data yet")


# # ------------------------------------------------------------------ data management (3 tabs, 1 sidebar entry)
# def data_management_page(user):
#     st.title("🗄️ Data Management")
#     t1, t2, t3 = st.tabs(["📤 Ingestion", "💾 Storage", "🌦️ Processing"])
#     with t1:
#         ingestion_page(db, user)
#     with t2:
#         storage_page(db, user)
#     with t3:
#         processing_page(db, user)


# # ------------------------------------------------------------------ admin users
# def users_page(user):
#     st.title("👥 Manage Users")
#     with st.container(border=True):
#         for u in db.users.find():
#             c = st.columns([3, 3, 2, 1])
#             c[0].write(u["name"])
#             c[1].write(u["email"])
#             if str(u["_id"]) == user["id"]:
#                 c[2].write(f"{u['role']} (you)")
#                 continue
#             new = c[2].selectbox("Role", ["admin", "analyst", "viewer"], index=["admin", "analyst", "viewer"].index(u["role"]),
#                                  key=f"role_{u['_id']}", label_visibility="collapsed")
#             if new != u["role"]:
#                 db.users.update_one({"_id": u["_id"]}, {"$set": {"role": new}})
#                 st.rerun()
#             if c[3].button("Delete", key=f"del_{u['_id']}"):
#                 db.users.delete_one({"_id": u["_id"]})
#                 st.rerun()
#     with st.container(border=True):
#         st.subheader("User feedback & support requests")
#         fb = list(db.feedback.find({}, {"_id": 0}).sort("time", -1).limit(30))
#         st.dataframe(pd.DataFrame(fb), width="stretch", hide_index=True) if fb else st.caption("Nothing yet")


# # ------------------------------------------------------------------ main
# if "splash_done" not in st.session_state:
#     if st.session_state.get("user"):           # pehle se login hai -> splash skip, seedha dashboard
#         st.session_state["splash_done"] = True
#     else:                                      # login nahi hai -> splash (loader), phir login page
#         splash_box = st.empty()
#         with splash_box.container():
#             splash_page()
#         splash_box.empty()
#         st.session_state["splash_done"] = True
#         st.rerun()

# user = st.session_state.get("user")
# if user and not db.users.find_one({"_id": ObjectId(user["id"])}):   # admin ne delete kar diya -> logout
#     st.session_state.pop("user", None)
#     user = None
# if not user:                                    # loader ke baad login / signup
#     if st.session_state.get("auth_view", "login") == "register":
#         register_page(db)                       # signup.py
#     else:
#         login_page(db)                          # login.py
#     st.stop()

# backup_security.auto_backup(db)               # roz ek encrypted backup (agar purana ho)

# PAGES = {"Dashboard": dashboard_page,                           # Dashboard.py (live data)
#          "Climate Map": lambda u: climate_map_page(db, u),
#          "Data Analytics": lambda u: analytics_page(db, u),
#          "Data Upload": upload_page,
#          "Data Management": data_management_page,               # Ingestion + Storage + Processing (tabs)
#          "Reports": lambda u: reports_page(db, u),
#          "Alerts": lambda u: alerts_page(db, u),                # Alert.py ka page
#          "Profile": lambda u: profile_page(db, u),
#          "Settings": lambda u: settings_page(db, u),            # settings_page.py
#          "Support & Feedback": lambda u: support_page(db, u),   # support_page.py (email wala)
#          }
# PAGES.update({"Pipeline Monitor": lambda u: bigdata_pages.pipeline_page(db, u),
#               "Live Stream": lambda u: bigdata_pages.stream_page(db, u),
#               "Satellite Imagery": lambda u: bigdata_pages.imagery_page(db, u),
#               "Tableau": lambda u: bigdata_pages.tableau_page(db, u),
#               "Alert Rules": lambda u: bigdata_pages.alert_rules_page(db, u)})
# if user["role"] == "admin":
#     PAGES["Manage Users"] = users_page
#     PAGES["Roles & Permissions"] = lambda u: bigdata_pages.roles_page(db, u)
#     PAGES["Performance Monitor"] = lambda u: performance_page.render()
#     PAGES["Backup & Security"] = lambda u: backup_security.backup_page(db, u)
# # Roles & Permissions page ka matrix yahan asli taur par lagu hota hai (admin ko sab milta hai)
# _perm = bigdata_pages.permissions_for(db, user["role"])
# PAGES = {n: f for n, f in PAGES.items() if _perm.get(bigdata_pages.PAGE_PERM.get(n), True)}

# choice = render_sidebar(db, user, list(PAGES))
# PAGES[choice](user)

"""EarthScape Climate Agency - the whole website in Python (Streamlit).
Run:  streamlit run app.py --theme.base dark

Folder structure:
    app.py
    profile_page.py
    support_page.py
    settings_page.py
    assets/Emerald Earth Eco Landscape.png
    assets/support_globe.png
    .streamlit/secrets.toml
Streamlit 1.39+ chahiye (st.container(key=...) aur button icons).
"""
# ------------------------------------------------------------------ imports (sab ek jagah)
import base64
import datetime
import html
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from bson import ObjectId

sys.path.insert(0, str(Path(__file__).resolve().parent))   # app.py ke folder se Login.py / signup.py / analytics.py / splash.py milein

import analytics
from Alert import alerts_page                          # Alerts page (Alert.py)
from Climite import climate_map_page                   # Climate Map page
from Dashboard import dashboard_page
from Extra_pages import analytics_page, reports_page
from profile_page import profile_page                  # Profile page (profile_page.py)
from settings_page import settings_page                # Settings page (settings_page.py)
from Data_Ingestion import ingestion_page              # Data Management -> Ingestion tab
from data_storage import storage_page                  # Data Management -> Storage tab
from data_processing import processing_page            # Data Management -> Processing tab
from Login import login_page
from signup import register_page
from splash import splash_page
from support_page import support_page                  # Support & Feedback page (support_page.py)
import bigdata_pages                                   # Pipeline, Stream, Satellite, Roles, Alert Rules, Tableau
import backup_security                                 # encrypted backups + security page
import performance_page                                # Performance Monitor page

st.set_page_config(page_title="EarthScape Climate Agency", page_icon="🌍", layout="wide")
db = analytics.get_db()

CSS = """<style>
.stApp{background:radial-gradient(1100px 520px at 18% -8%,#0c2f5a 0%,transparent 62%),#040d1c}
[data-testid=stSidebar]{background:#061424;border-right:1px solid #173553}
[data-testid=stHeader]{background:transparent}
[data-testid=stVerticalBlockBorderWrapper]{background:rgba(10,27,46,.88);border-color:#173553!important;border-radius:14px}
.kpi{border-radius:14px;padding:16px;border:1px solid;display:grid;grid-template-columns:54px 1fr;gap:4px 12px;align-items:center;min-height:108px}
.kpi .ico{font-size:34px;text-align:center}.kpi .lab{color:#d3e0ee;font-size:13px}.kpi .val{font-size:27px;font-weight:700;color:#fff;line-height:1.15}
.kpi .val small{font-size:14px;font-weight:600}.kpi .chg{grid-column:1/-1;font-size:12px;color:#8ea6bf}
.kpi.t{background:linear-gradient(135deg,#3b1417,#14131f);border-color:#7a2a2c}
.kpi.c{background:linear-gradient(135deg,#0b3568,#0a1e3a);border-color:#1f6fbe}
.kpi.a{background:linear-gradient(135deg,#0d4a1c,#0b2315);border-color:#2a8a3a}
.kpi.s{background:linear-gradient(135deg,#075a8c,#0a2740);border-color:#1f88c8}
.alert{display:flex;gap:12px;align-items:center;padding:10px;border-radius:10px;background:#0b2036;border:1px solid #112f4c;margin-bottom:8px}
.alert .i{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;font-size:18px;background:#4a1a1d;flex:none}
.alert .i.warning{background:#4a3510}.alert b{display:block}.alert span{color:#8ea6bf;font-size:12px}.alert .w{margin-left:auto;color:#8ea6bf;font-size:12px;white-space:nowrap}
.pred{border:1px solid #3a2a66;background:#171033;border-radius:10px;padding:8px 16px;text-align:center;font-size:26px;font-weight:700}
.pred small{display:block;font-size:12px;color:#8ea6bf;font-weight:400}
.brand{text-align:center;font-size:26px;font-weight:700}.brand span{color:#3ddc84}
.tag{text-align:center;color:#8ea6bf;margin-bottom:14px}
div.stButton>button[kind=primary],div.stFormSubmitButton>button{background:linear-gradient(90deg,#58df57,#00bffb);color:#06210f;border:0;font-weight:700}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)


# ================================================================== SIDEBAR NAVIGATION
BANNER_IMG = Path(__file__).parent / "assets" / "Emerald Earth Eco Landscape.png"

# (page name, material icon).  Sirf wahi dikhte hain jo PAGES mein hon.
ITEMS = [
    ("Dashboard", ":material/home:"),
    ("Climate Map", ":material/map:"),
    ("Data Management", ":material/storage:"),
    ("Data Analytics", ":material/bar_chart:"),
    ("Data Upload", ":material/cloud_upload:"),
    ("Pipeline Monitor", ":material/hub:"),
    ("Live Stream", ":material/sensors:"),
    ("Satellite Imagery", ":material/satellite_alt:"),
    ("Tableau", ":material/insights:"),
    ("Reports", ":material/description:"),
    ("Alerts", ":material/notifications:"),
    ("Alert Rules", ":material/rule:"),
    ("Profile", ":material/person:"),
    ("Settings", ":material/settings:"),
    ("Support & Feedback", ":material/headset_mic:"),
    ("Manage Users", ":material/groups:"),
    ("Roles & Permissions", ":material/admin_panel_settings:"),
    ("Performance Monitor", ":material/speed:"),
    ("Backup & Security", ":material/shield:"),
]

NAV_CSS = """<style>
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
def _banner_b64(mtime):
    """Banner image ko base64 mein convert karta hai. mtime cache key hai, isliye image badalne par refresh ho jata hai."""
    return base64.b64encode(BANNER_IMG.read_bytes()).decode()


def _banner_css():
    if not BANNER_IMG.exists():
        return ""   # image na mile to purana gradient banner chalega
    b64 = _banner_b64(BANNER_IMG.stat().st_mtime)
    return (".nav-banner{background:linear-gradient(180deg,rgba(0,0,0,0) 40%,rgba(4,13,28,.75) 100%),"
            f"url('data:image/png;base64,{b64}') center/cover no-repeat !important}}")


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def go_to(name):
    """Kisi bhi page par jao (jaise Dashboard ke 'View Full Map' button se)."""
    st.session_state["page"] = name


def render_sidebar(db, user, available):
    if st.session_state.get("page") not in available:
        st.session_state["page"] = available[0]
    current = st.session_state["page"]

    # settings_page.py in keys ko set karta hai: "notifications" aur "show_banner"
    prefs = db.settings.find_one({"_id": user["id"]}) or {}
    unread = db.alerts.count_documents({"read": False}) if prefs.get("notifications", True) else 0

    dyn = BADGE.format(sel=".st-key-navwrap_manage_users button", txt="👑", bg="transparent")
    if unread:
        dyn += BADGE.format(sel=".st-key-navwrap_alerts button", txt=str(min(unread, 99)), bg="#ff4d4f")
    dyn += _banner_css()
    st.markdown(NAV_CSS + f"<style>{dyn}</style>", unsafe_allow_html=True)

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
            st.markdown('<div class="nav-banner"><div class="tx">Together for<br>a Greener Planet</div></div>',
                        unsafe_allow_html=True)
        st.caption(f"Signed in as **{user['name']}** ({user['role']})")
        if st.button("Logout", key="nav_logout", icon=":material/logout:"):
            for k in [k for k in st.session_state if k != "splash_done"]:   # splash dobara na chale
                del st.session_state[k]
            st.rerun()
    return st.session_state["page"]


# ================================================================== helpers
def ago(t):
    s = (datetime.datetime.utcnow() - t).total_seconds()
    if s < 3600:
        return f"{max(1, int(s // 60))}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago" if s < 86400 * 90 else t.strftime("%d %b %Y")


def get_thresholds():
    d = db.thresholds.find_one({"_id": "global"})
    return d["values"] if d else analytics.DEFAULT_TH


# ------------------------------------------------------------------ upload
def upload_page(user):
    st.title("⬆️ Data Upload")
    if user["role"] == "viewer":
        st.warning("Your account is read-only (viewer). Ask an administrator for the analyst role to upload data.")
    else:
        a, b = st.columns(2)
        with a.container(border=True):
            st.subheader("Upload CSV / Excel / JSON file")
            st.caption("Columns: date, station, temperature, co2, humidity, rainfall, sea_level, aqi. "
                       "Only the first three are required. Missing values are filled automatically.")
            f = st.file_uploader("Drag and drop your file here", type=["csv", "json", "xlsx"])
            if f and st.button("Upload & analyse", type="primary"):
                try:
                    name = f.name.lower()
                    df = pd.read_csv(f) if name.endswith(".csv") else pd.read_excel(f) if name.endswith(".xlsx") else pd.read_json(f)
                    df = analytics.clean(df)
                    n = analytics.save(db, df)
                    na = analytics.scan(db, df, get_thresholds())
                    db.uploads.insert_one({"user": user["id"], "name": f.name, "size": f.size, "rows": n,
                                           "time": datetime.datetime.utcnow()})
                    st.success(f"{n:,} rows imported. {na} new alert(s) created.")
                except Exception as e:
                    st.error(str(e))
        with b.container(border=True):
            st.subheader("Send a live sensor reading")
            with st.form("live"):
                station = st.text_input("Station", "Karachi")
                c = st.columns(3)
                temp = c[0].number_input("Temperature °C", value=30.0)
                co2 = c[1].number_input("CO₂ ppm", value=420.0)
                aqi = c[2].number_input("AQI", value=50.0)
                if st.form_submit_button("Send reading"):
                    rec = {"date": datetime.datetime.utcnow(), "station": station.strip(), "temperature": temp, "co2": co2, "aqi": aqi,
                           "humidity": None, "rainfall": None, "sea_level": None}
                    if not rec["station"]:
                        st.error("Station is required")
                    else:
                        db.records.insert_one(dict(rec))
                        al = analytics.alert_docs(rec, get_thresholds())
                        if al:
                            db.alerts.insert_many(al)
                            st.error("ALERT: " + "; ".join(x["message"] for x in al))
                        else:
                            st.success("Reading saved, no alerts.")
    with st.container(border=True):
        st.subheader("🗂️ Recent Uploads")
        ups = list(db.uploads.find().sort("time", -1).limit(5))
        if not ups:
            st.caption("No uploads yet.")
        for u_ in ups:
            size = f"{u_['size'] / 1024:,.0f} KB" if u_["size"] < 1024 ** 2 else f"{u_['size'] / 1024 ** 2:.1f} MB"
            st.markdown(f'<div class="alert"><div class="i info">📄</div><div><b>{html.escape(u_["name"])}</b>'
                        f'<span>{size} · {u_["rows"]:,} rows</span></div><div class="w">{ago(u_["time"])}</div></div>',
                        unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("Latest records")
        rows = list(db.records.find({}, {"_id": 0}).sort("date", -1).limit(10))
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True) if rows else st.caption("No data yet")


# ------------------------------------------------------------------ data management (3 tabs, 1 sidebar entry)
def data_management_page(user):
    st.title("🗄️ Data Management")
    t1, t2, t3 = st.tabs(["📤 Ingestion", "💾 Storage", "🌦️ Processing"])
    with t1:
        ingestion_page(db, user)
    with t2:
        storage_page(db, user)
    with t3:
        processing_page(db, user)


# ------------------------------------------------------------------ admin users
def users_page(user):
    st.title("👥 Manage Users")
    with st.container(border=True):
        for u in db.users.find():
            c = st.columns([3, 3, 2, 1])
            c[0].write(u["name"])
            c[1].write(u["email"])
            if str(u["_id"]) == user["id"]:
                c[2].write(f"{u['role']} (you)")
                continue
            new = c[2].selectbox("Role", ["admin", "analyst", "viewer"], index=["admin", "analyst", "viewer"].index(u["role"]),
                                 key=f"role_{u['_id']}", label_visibility="collapsed")
            if new != u["role"]:
                db.users.update_one({"_id": u["_id"]}, {"$set": {"role": new}})
                st.rerun()
            if c[3].button("Delete", key=f"del_{u['_id']}"):
                db.users.delete_one({"_id": u["_id"]})
                st.rerun()
    with st.container(border=True):
        st.subheader("User feedback & support requests")
        fb = list(db.feedback.find({}, {"_id": 0}).sort("time", -1).limit(30))
        st.dataframe(pd.DataFrame(fb), width="stretch", hide_index=True) if fb else st.caption("Nothing yet")


# ------------------------------------------------------------------ main
if "splash_done" not in st.session_state:
    if st.session_state.get("user"):           # pehle se login hai -> splash skip, seedha dashboard
        st.session_state["splash_done"] = True
    else:                                      # login nahi hai -> splash (loader), phir login page
        splash_box = st.empty()
        with splash_box.container():
            splash_page()
        splash_box.empty()
        st.session_state["splash_done"] = True
        st.rerun()

user = st.session_state.get("user")
if user and not db.users.find_one({"_id": ObjectId(user["id"])}):   # admin ne delete kar diya -> logout
    st.session_state.pop("user", None)
    user = None
if not user:                                    # loader ke baad login / signup
    if st.session_state.get("auth_view", "login") == "register":
        register_page(db)                       # signup.py
    else:
        login_page(db)                          # login.py
    st.stop()

backup_security.auto_backup(db)               # roz ek encrypted backup (agar purana ho)

PAGES = {"Dashboard": dashboard_page,                           # Dashboard.py (live data)
         "Climate Map": lambda u: climate_map_page(db, u),
         "Data Analytics": lambda u: analytics_page(db, u),
         "Data Upload": upload_page,
         "Data Management": data_management_page,               # Ingestion + Storage + Processing (tabs)
         "Reports": lambda u: reports_page(db, u),
         "Alerts": lambda u: alerts_page(db, u),                # Alert.py ka page
         "Profile": lambda u: profile_page(db, u),              # profile_page.py
         "Settings": lambda u: settings_page(db, u),            # settings_page.py
         "Support & Feedback": lambda u: support_page(db, u),   # support_page.py (email wala)
         }
PAGES.update({"Pipeline Monitor": lambda u: bigdata_pages.pipeline_page(db, u),
              "Live Stream": lambda u: bigdata_pages.stream_page(db, u),
              "Satellite Imagery": lambda u: bigdata_pages.imagery_page(db, u),
              "Tableau": lambda u: bigdata_pages.tableau_page(db, u),
              "Alert Rules": lambda u: bigdata_pages.alert_rules_page(db, u)})
if user["role"] == "admin":
    PAGES["Manage Users"] = users_page
    PAGES["Roles & Permissions"] = lambda u: bigdata_pages.roles_page(db, u)
    PAGES["Performance Monitor"] = lambda u: performance_page.render()
    PAGES["Backup & Security"] = lambda u: backup_security.backup_page(db, u)
# Roles & Permissions page ka matrix yahan asli taur par lagu hota hai (admin ko sab milta hai)
_perm = bigdata_pages.permissions_for(db, user["role"])
PAGES = {n: f for n, f in PAGES.items() if _perm.get(bigdata_pages.PAGE_PERM.get(n), True)}

choice = render_sidebar(db, user, list(PAGES))
PAGES[choice](user)