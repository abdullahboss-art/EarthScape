"""Settings page for EarthScape.

app.py mein:
    from settings_page import settings_page
    PAGES = {..., "Settings": lambda u: settings_page(db, u), ...}

Settings MongoDB ke `settings` collection mein save hoti hain:
    {"_id": user["id"]}  -> har user ki apni settings
(Sidebar ki `show_banner` aur `notifications` keys yahin se set hoti hain.)

Doosre pages mein settings use karne ke liye:
    from settings_page import load_settings
    s = load_settings(db, user)      # s["timezone"], s["temp_unit"], ...
"""

import datetime
import json
import re

import streamlit as st


# =========================
# DEFAULTS & OPTIONS
# =========================

DEFAULTS = {
    # General
    "app_name": "EarthScape Climate Agency",
    "timezone": "UTC",
    "date_format": "ISO 8601 (YYYY-MM-DD)",
    "temp_unit": "Celsius (°C)",
    "language": "English",
    "start_page": "Dashboard",
    # Notifications
    "email_alerts": True,
    "notifications": True,
    "weekly_report": False,
    "product_updates": False,
    "digest": "Instant",
    "severities": ["Warning", "Critical"],
    "alert_email": "",
    # Appearance
    "accent": "#19E6A1",
    "chart_palette": "Ocean",
    "compact": False,
    "animations": True,
    "show_banner": True,
    # Security
    "session_timeout": "30 minutes",
    "login_alerts": True,
}

TIMEZONES = [
    "UTC", "Asia/Karachi", "Asia/Dubai", "Asia/Riyadh", "Asia/Kolkata",
    "Asia/Dhaka", "Asia/Singapore", "Asia/Tokyo", "Europe/London",
    "Europe/Paris", "Europe/Berlin", "Africa/Cairo", "America/New_York",
    "America/Chicago", "America/Los_Angeles", "Australia/Sydney",
]

DATE_FORMATS = {
    "ISO 8601 (YYYY-MM-DD)": "%Y-%m-%d",
    "DD/MM/YYYY": "%d/%m/%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
    "DD MMM YYYY": "%d %b %Y",
}

TEMP_UNITS = ["Celsius (°C)", "Fahrenheit (°F)", "Kelvin (K)"]
LANGUAGES = ["English", "Urdu", "Arabic"]
START_PAGES = [
    "Dashboard", "Climate Map", "Data Management", "Data Analytics",
    "Data Upload", "Reports", "Alerts",
]
DIGESTS = ["Instant", "Hourly digest", "Daily digest", "Weekly digest"]
SEVERITIES = ["Info", "Warning", "Critical"]
TIMEOUTS = ["15 minutes", "30 minutes", "1 hour", "4 hours", "Never"]

PALETTES = {
    "Ocean": ["#19E6A1", "#16D3E0", "#2E86FF", "#7C5CFF", "#FF6BA6"],
    "Sunset": ["#FFB347", "#FF7E5F", "#FD3A69", "#B24592", "#6A4C93"],
    "Forest": ["#B8F27B", "#5FD068", "#2FA36B", "#1B7F6B", "#145A5A"],
    "Mono": ["#F2F6FA", "#C5D1DE", "#97A8BB", "#6A7F96", "#3F566E"],
}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


# =========================
# CSS DESIGN
# =========================

CSS = """
<style>
/* ---------- tabs ---------- */
.st-key-settings_wrap [data-baseweb="tab-list"] { gap: 10px; border-bottom: none; }
.st-key-settings_wrap [data-baseweb="tab-border"] { display: none; }
.st-key-settings_wrap [data-baseweb="tab-highlight"] { background: __ACCENT__ !important; height: 3px; border-radius: 3px; }
.st-key-settings_wrap button[data-baseweb="tab"] {
    background: rgba(14,40,66,.75);
    border: 1px solid #173f63;
    border-radius: 12px;
    padding: 8px 20px;
    height: auto;
    color: #cfe0f3;
    transition: all .2s ease;
}
.st-key-settings_wrap button[data-baseweb="tab"]:hover { border-color: __ACCENT__; }
.st-key-settings_wrap button[data-baseweb="tab"][aria-selected="true"] {
    color: __ACCENT__;
    border-color: __ACCENT__;
    box-shadow: 0 0 14px rgba(25,230,161,.18);
}

/* ---------- cards ---------- */
div[class*="st-key-set_card"] {
    background: linear-gradient(160deg, rgba(12,36,64,.92), rgba(6,20,36,.92));
    border: 1px solid #1b4a73;
    border-radius: 16px;
    padding: __PAD__;
    box-shadow: 0 0 24px rgba(0,120,220,.12);
    margin-top: 6px;
}
.es-card-title { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.es-card-sub { color: #8ea6bf; font-size: 13px; margin-bottom: 14px; }
.es-section { color: #e6f0fb; font-weight: 600; font-size: 15px; margin: 18px 0 8px 0;
              padding-top: 14px; border-top: 1px solid #173f63; }

/* ---------- inputs ---------- */
.st-key-settings_wrap .stTextInput input,
.st-key-settings_wrap .stNumberInput input,
.st-key-settings_wrap div[data-baseweb="select"] > div,
.st-key-settings_wrap div[data-baseweb="input"] {
    background: rgba(8,26,46,.95) !important;
    border: 1px solid #173f63 !important;
    border-radius: 10px !important;
}
.st-key-settings_wrap label p { color: #cfe0f3; font-weight: 500; }

/* ---------- buttons ---------- */
.st-key-settings_wrap [data-testid="stFormSubmitButton"] button,
.st-key-settings_wrap .stDownloadButton button {
    background: linear-gradient(90deg, #22e07f, #16d3e0);
    color: #04231a;
    font-weight: 700;
    border: none;
    border-radius: 12px;
    padding: .5rem 1.6rem;
    box-shadow: 0 0 18px rgba(25,230,161,.28);
    transition: transform .15s ease, box-shadow .15s ease;
}
.st-key-settings_wrap [data-testid="stFormSubmitButton"] button:hover,
.st-key-settings_wrap .stDownloadButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 26px rgba(25,230,161,.45);
    color: #04231a;
}
.st-key-reset_btn button {
    background: transparent !important;
    border: 1px solid #ff6b6b !important;
    color: #ff8a8a !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}
.st-key-reset_btn button:hover { background: rgba(255,107,107,.12) !important; }

/* ---------- misc ---------- */
.es-info {
    display: flex; align-items: center; gap: 14px;
    background: rgba(10,32,54,.85); border: 1px solid #173f63;
    border-radius: 12px; padding: 12px 16px; color: #cfe0f3; margin-bottom: 8px;
}
.es-info .ic { font-size: 26px; }
.es-info small { color: #8ea6bf; display: block; }
.es-chip {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    background: rgba(25,230,161,.14); color: __ACCENT__; font-size: 12px; margin-left: 6px;
}
.es-preview { color: #9db4cc; font-size: 13px; margin: 2px 0 12px 0; }
.es-preview b { color: __ACCENT__; }
</style>
"""


# =========================
# DATABASE HELPERS
# =========================

def _uid(user):
    return str(user.get("id") or user.get("name", "unknown"))


def load_settings(db, user):
    """User ki settings (defaults ke saath merge ho kar)."""
    try:
        doc = db.settings.find_one({"_id": _uid(user)}) or {}
    except Exception:
        doc = {}
    doc.pop("_id", None)
    return {**DEFAULTS, **doc}


def _save(db, user, patch):
    patch = dict(patch)
    patch["updated"] = datetime.datetime.utcnow()
    db.settings.update_one({"_id": _uid(user)}, {"$set": patch}, upsert=True)
    st.session_state["_settings_flash"] = "Settings saved successfully."
    st.rerun()


def _idx(options, value):
    try:
        return list(options).index(value)
    except ValueError:
        return 0


def _now_preview(s):
    """Selected timezone + date format ke hisab se abhi ka waqt.
    Windows par exact timezone ke liye:  pip install tzdata
    """
    fmt = DATE_FORMATS.get(s["date_format"], "%Y-%m-%d")
    try:
        from zoneinfo import ZoneInfo
        now = datetime.datetime.now(ZoneInfo(s["timezone"]))
    except Exception:
        now = datetime.datetime.utcnow()
    return now.strftime(f"{fmt}  %H:%M")


# =========================
# TAB: GENERAL
# =========================

def _tab_general(db, user, s):
    with st.container(key="set_card_general"):
        st.markdown("<div class='es-card-title'>General Settings</div>"
                    "<div class='es-card-sub'>Basic application and regional preferences.</div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div class='es-preview'>Current time with your settings: <b>{_now_preview(s)}</b></div>",
            unsafe_allow_html=True,
        )

        with st.form("form_general", border=False):
            app_name = st.text_input("Application Name", value=s["app_name"])
            timezone = st.selectbox("Timezone", TIMEZONES, index=_idx(TIMEZONES, s["timezone"]))
            date_format = st.selectbox(
                "Date Format", list(DATE_FORMATS), index=_idx(DATE_FORMATS, s["date_format"])
            )

            st.markdown("<div class='es-section'>Regional & display</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                temp_unit = st.selectbox("Temperature Unit", TEMP_UNITS,
                                         index=_idx(TEMP_UNITS, s["temp_unit"]))
            with c2:
                language = st.selectbox("Language", LANGUAGES, index=_idx(LANGUAGES, s["language"]))
            with c3:
                start_page = st.selectbox("Default Start Page", START_PAGES,
                                          index=_idx(START_PAGES, s["start_page"]))

            saved = st.form_submit_button("Save Changes", type="primary")

        if saved:
            if len(app_name.strip()) < 2:
                st.error("Application name must be at least 2 characters.")
            else:
                _save(db, user, {
                    "app_name": app_name.strip(), "timezone": timezone,
                    "date_format": date_format, "temp_unit": temp_unit,
                    "language": language, "start_page": start_page,
                })


# =========================
# TAB: NOTIFICATIONS
# =========================

def _tab_notifications(db, user, s):
    with st.container(key="set_card_notif"):
        st.markdown("<div class='es-card-title'>Notification Settings</div>"
                    "<div class='es-card-sub'>Choose how and when EarthScape should alert you.</div>",
                    unsafe_allow_html=True)

        with st.form("form_notif", border=False):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                email_alerts = st.toggle("Email alerts", value=s["email_alerts"])
                notifications = st.toggle("In-app alerts & sidebar badge", value=s["notifications"])
                weekly_report = st.toggle("Weekly climate report by email", value=s["weekly_report"])
                product_updates = st.toggle("Product updates & announcements", value=s["product_updates"])
            with c2:
                digest = st.selectbox("Alert frequency", DIGESTS, index=_idx(DIGESTS, s["digest"]))
                severities = st.multiselect("Notify me for", SEVERITIES,
                                            default=[x for x in s["severities"] if x in SEVERITIES])
                alert_email = st.text_input("Alert email (optional)", value=s["alert_email"],
                                            placeholder="you@example.com")

            saved = st.form_submit_button("Save Changes", type="primary")

        if saved:
            alert_email = alert_email.strip()
            if alert_email and not EMAIL_RE.match(alert_email):
                st.error("Please enter a valid alert email address.")
            elif not severities:
                st.error("Select at least one severity level.")
            else:
                _save(db, user, {
                    "email_alerts": email_alerts, "notifications": notifications,
                    "weekly_report": weekly_report, "product_updates": product_updates,
                    "digest": digest, "severities": severities, "alert_email": alert_email,
                })


# =========================
# TAB: APPEARANCE
# =========================

def _tab_appearance(db, user, s):
    with st.container(key="set_card_appearance"):
        st.markdown("<div class='es-card-title'>Appearance Settings</div>"
                    "<div class='es-card-sub'>Personalise colours and how data looks.</div>",
                    unsafe_allow_html=True)

        swatches = "".join(
            f"<span style='display:inline-block;width:34px;height:18px;border-radius:6px;"
            f"margin-right:6px;background:{c}'></span>"
            for c in PALETTES.get(s["chart_palette"], PALETTES["Ocean"])
        )
        st.markdown(
            f"<div class='es-preview'>Current chart palette ({s['chart_palette']}): {swatches}</div>",
            unsafe_allow_html=True,
        )

        with st.form("form_appearance", border=False):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                accent = st.color_picker("Accent colour", value=s["accent"])
                chart_palette = st.selectbox("Chart colour palette", list(PALETTES),
                                             index=_idx(PALETTES, s["chart_palette"]))
            with c2:
                compact = st.toggle("Compact layout (less spacing)", value=s["compact"])
                animations = st.toggle("Enable animations", value=s["animations"])
                show_banner = st.toggle("Show sidebar banner", value=s["show_banner"])

            saved = st.form_submit_button("Save Changes", type="primary")

        if saved:
            _save(db, user, {
                "accent": accent, "chart_palette": chart_palette, "compact": compact,
                "animations": animations, "show_banner": show_banner,
            })


# =========================
# TAB: SECURITY
# =========================

def _tab_security(db, user, s):
    with st.container(key="set_card_security"):
        st.markdown("<div class='es-card-title'>Security Settings</div>"
                    "<div class='es-card-sub'>Session preferences and your data.</div>",
                    unsafe_allow_html=True)

        role = str(user.get("role", "user")).capitalize()
        st.markdown(
            f"<div class='es-info'><div class='ic'>🔐</div>"
            f"<div><b>Signed in as {user.get('name', 'user')}</b>"
            f"<small>Role: {role} &middot; access is limited to your role permissions</small></div></div>",
            unsafe_allow_html=True,
        )

        with st.form("form_security", border=False):
            session_timeout = st.selectbox("Auto logout after inactivity", TIMEOUTS,
                                           index=_idx(TIMEOUTS, s["session_timeout"]))
            login_alerts = st.toggle("Email me when my account signs in", value=s["login_alerts"])
            saved = st.form_submit_button("Save Changes", type="primary")

        if saved:
            _save(db, user, {"session_timeout": session_timeout, "login_alerts": login_alerts})

        st.markdown("<div class='es-section'>Data & privacy</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download my settings (JSON)",
                data=json.dumps(s, indent=2, default=str),
                file_name="earthscape_settings.json",
                mime="application/json",
            )
        with c2:
            if st.button("Reset to defaults", key="reset_btn"):
                db.settings.delete_one({"_id": _uid(user)})
                st.session_state["_settings_flash"] = "Settings reset to defaults."
                st.rerun()


# =========================
# SETTINGS PAGE
# =========================

def settings_page(db, user):
    s = load_settings(db, user)
    st.session_state["es_settings"] = s          # app.py / doosre pages yahan se bhi parh sakte hain

    css = CSS.replace("__ACCENT__", s["accent"]).replace("__PAD__", "12px 16px" if s["compact"] else "20px 24px")
    st.markdown(css, unsafe_allow_html=True)

    st.title("Settings")

    msg = st.session_state.pop("_settings_flash", None)
    if msg:
        st.success(msg)

    with st.container(key="settings_wrap"):
        t_gen, t_not, t_app, t_sec = st.tabs(["General", "Notifications", "Appearance", "Security"])
        with t_gen:
            _tab_general(db, user, s)
        with t_not:
            _tab_notifications(db, user, s)
        with t_app:
            _tab_appearance(db, user, s)
        with t_sec:
            _tab_security(db, user, s)

    if s.get("updated"):
        st.caption(f"Last saved: {s['updated']:%Y-%m-%d %H:%M} UTC")