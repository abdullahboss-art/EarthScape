"""EarthScape - My Profile page (profile.html ka Streamlit version).

app.py mein:
    from profile_page import profile_page
    "Profile": lambda u: profile_page(db, u),

Naya:
  * Logout button (session saaf -> login page). Google (st.login) se aaye hon to st.logout() bhi chalta hai.
  * Google se login ho aur uska profile valid ho to Google ka naam / email / photo dikhta hai.
"""
import datetime
import hashlib
import html

import streamlit as st
from bson import ObjectId

try:
    import bigdata_pages          # permissions_for() + PAGE_PERM (Roles & Permissions matrix)
except Exception:                 # pragma: no cover
    bigdata_pages = None

TIMEZONES = ["Asia/Karachi", "UTC", "Asia/Dubai", "Asia/Kolkata", "Asia/Dhaka", "Europe/London",
             "Europe/Berlin", "America/New_York", "America/Los_Angeles", "Australia/Sydney"]
LANGUAGES = ["English", "Urdu", "Hindi", "Arabic", "French", "German"]
ACCESS = {"admin": "Full access", "analyst": "Read & write", "viewer": "Read only"}

CSS = """<style>
.pf-avatar{width:84px;height:84px;border-radius:50%;margin:0 auto 12px;display:grid;place-items:center;
  font-size:30px;font-weight:700;color:#06210f;background:linear-gradient(135deg,#58df57,#00bffb)}
img.pf-avatar{display:block;object-fit:cover;border:2px solid #1fb6e8}
.pf-name{font-size:19px;font-weight:700;text-align:center;color:#fff}
.pf-mail{font-size:12px;color:#8ea6bf;text-align:center;margin:3px 0 10px}
.pf-center{text-align:center}
.pf-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;
  border-bottom:1px solid #112f4c;font-size:13px}
.pf-row:last-child{border-bottom:0}
.pf-row .m{color:#8ea6bf}
.pf-tag{display:inline-block;padding:3px 12px;border-radius:999px;font-size:11px;font-weight:700}
.pf-g{background:#0d3a1f;color:#58df57;border:1px solid #2a8a3a}
.pf-r{background:#4a1a1d;color:#ff7a7c;border:1px solid #7a2a2c}
.pf-a{background:#4a3510;color:#ffc04d;border:1px solid #8a6a1a}
.pf-b{background:#0b3568;color:#6cc0ff;border:1px solid #1f6fbe}
.pf-bar-wrap{display:flex;align-items:center;gap:14px;font-size:12px;margin:10px 0;color:#d3e0ee}
.pf-bar-wrap .l{width:70px}.pf-bar-wrap .c{width:34px;text-align:right;font-weight:700}
.pf-bar{flex:1;height:10px;background:#0b2036;border-radius:999px;overflow:hidden}
.pf-bar i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#58df57,#00bffb)}
.pf-bar i.r{background:linear-gradient(90deg,#ff7a7c,#ff4d4f)}
.pf-perms{display:flex;flex-wrap:wrap;gap:8px}
</style>"""


# ------------------------------------------------------------------ helpers
def _timeago(t):
    if not t:
        return "Never"
    s = (datetime.datetime.utcnow() - t).total_seconds()
    if s < 60:
        return "just now"
    if s < 3600:
        return f"{int(s // 60)}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    if s < 86400 * 90:
        return f"{int(s // 86400)}d ago"
    return t.strftime("%d %b %Y")


def _dmy(t):
    return t.strftime("%d/%m/%Y") if t else "-"


def _tag(text, cls):
    return f'<span class="pf-tag {cls}">{html.escape(str(text))}</span>'


def _row(label, value_html):
    return f'<div class="pf-row"><span class="m">{label}</span><span>{value_html}</span></div>'


def _initials(name):
    parts = (name or "?").split()
    return ("".join(p[0] for p in parts[:2]) or "?").upper()


def _stored_hash(doc):
    return doc.get("password_hash") or doc.get("password") or ""


def _check_password(stored, plain):
    """Login.py/signup.py jo bhi hashing use karte hain, yahan uska match hona chahiye.
    Common formats support: werkzeug, bcrypt, sha256 hex, plain."""
    try:
        if stored.startswith(("pbkdf2:", "scrypt:")):
            from werkzeug.security import check_password_hash
            return check_password_hash(stored, plain)
        if stored.startswith("$2"):
            import bcrypt
            return bcrypt.checkpw(plain.encode(), stored.encode())
    except Exception:
        return False
    if len(stored) == 64:
        return hashlib.sha256(plain.encode()).hexdigest() == stored
    return stored == plain


def _make_password(stored, plain):
    """Naya hash usi format mein banata hai jis mein purana tha."""
    if stored.startswith("$2"):
        import bcrypt
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
    if len(stored) == 64:
        return hashlib.sha256(plain.encode()).hexdigest()
    if stored.startswith(("pbkdf2:", "scrypt:")) or not stored:
        from werkzeug.security import generate_password_hash
        return generate_password_hash(plain)
    return plain


def _count(coll, query):
    try:
        return coll.count_documents(query)
    except Exception:
        return 0


# ------------------------------------------------------------------ google profile
def _oidc_logged_in():
    """True agar Streamlit ke built-in st.login (Google OIDC) se login hua ho."""
    try:
        return bool(getattr(st.user, "is_logged_in", False))
    except Exception:
        return False


def _google_info(doc):
    """Google profile return karta hai agar user Google se aaya ho aur profile valid ho, warna None.

    Do jagah dekhta hai:
      1) st.user (st.login / OIDC)
      2) DB ka user doc (provider == 'google' ya google_id maujood ho, aur picture wagera)
    """
    info = None
    if _oidc_logged_in():
        su = st.user
        info = {"name": su.get("name"), "email": su.get("email"),
                "picture": su.get("picture"), "verified": su.get("email_verified", True)}
    else:
        provider = str(doc.get("provider") or doc.get("auth_provider") or doc.get("login_method") or "").lower()
        if provider == "google" or doc.get("google_id") or doc.get("google_sub"):
            info = {"name": doc.get("name"), "email": doc.get("email"),
                    "picture": doc.get("picture") or doc.get("avatar") or doc.get("photo"),
                    "verified": doc.get("email_verified", True)}
    if not info:
        return None

    # validation: email asli ho aur verified ho
    email = str(info.get("email") or "").strip()
    if "@" not in email or info.get("verified") is False:
        return None
    pic = str(info.get("picture") or "").strip()
    return {"name": str(info.get("name") or "").strip(),
            "email": email,
            "picture": pic if pic.startswith("https://") else ""}   # sirf https photo allow


# ------------------------------------------------------------------ logout
def _logout():
    """Session saaf karo aur login page par bhejo (app.py user na milne par login_page dikha deta hai)."""
    google = _oidc_logged_in()
    for k in [k for k in st.session_state if k != "splash_done"]:   # splash dobara na chale
        del st.session_state[k]
    if google:
        st.logout()      # Google/OIDC session bhi khatam (ye khud rerun karta hai)
    else:
        st.rerun()


# ------------------------------------------------------------------ data fetch (DB se)
def _load(db, user):
    uid = ObjectId(user["id"])
    doc = db.users.find_one({"_id": uid}) or {}
    prefs = db.settings.find_one({"_id": user["id"]}) or {}
    since = datetime.datetime.utcnow() - datetime.timedelta(days=30)

    overview = [
        ("Uploads", _count(db.uploads, {"user": user["id"], "time": {"$gte": since}})),
        ("Reports", _count(db.reports, {"user": user["id"], "time": {"$gte": since}})),
        ("Feedback", _count(db.feedback, {"user": user["id"], "time": {"$gte": since}})),
        ("Alerts", _count(db.alerts, {"time": {"$gte": since}})),
    ]
    top = max([c for _, c in overview] + [1])
    overview = [{"label": l, "count": c, "pct": round(c / top * 100)} for l, c in overview]

    recent = []
    for u in db.uploads.find({"user": user["id"]}).sort("time", -1).limit(5):
        recent.append({"text": f"Uploaded {u.get('name', 'file')}", "created_at": u["time"]})
    try:
        for f in db.feedback.find({"user": user["id"]}).sort("time", -1).limit(5):
            recent.append({"text": "Sent feedback / support request", "created_at": f["time"]})
    except Exception:
        pass
    recent.sort(key=lambda a: a["created_at"], reverse=True)

    perms = []
    if bigdata_pages:
        try:
            matrix = bigdata_pages.permissions_for(db, doc.get("role", user["role"]))
            perms = [k for k, v in matrix.items() if v]
        except Exception:
            pass
    return doc, prefs, overview, recent[:6], perms


# ------------------------------------------------------------------ actions
def _save_profile(db, user, name, email, dept, tz, lang):
    email = email.strip().lower()
    if not name.strip() or not email:
        return st.error("Name and email are required")
    if db.users.find_one({"email": email, "_id": {"$ne": ObjectId(user["id"])}}):
        return st.error("This email is already used by another account")
    db.users.update_one({"_id": ObjectId(user["id"])},
                        {"$set": {"name": name.strip(), "email": email, "department": dept.strip(),
                                  "timezone": tz, "language": lang}})
    st.session_state["user"] = {**user, "name": name.strip(), "email": email}
    st.success("Profile updated")
    st.rerun()


def _change_password(db, user, current, new, confirm):
    doc = db.users.find_one({"_id": ObjectId(user["id"])}) or {}
    stored = _stored_hash(doc)
    if not _check_password(stored, current):
        return st.error("Current password is incorrect")
    if len(new) < 8:
        return st.error("New password must be at least 8 characters")
    if new != confirm:
        return st.error("New passwords do not match")
    field = "password_hash" if "password_hash" in doc or "password" not in doc else "password"
    db.users.update_one({"_id": doc["_id"]},
                        {"$set": {field: _make_password(stored, new),
                                  "password_changed_at": datetime.datetime.utcnow()}})
    st.success("Password updated")


# ------------------------------------------------------------------ page
def profile_page(db, user):
    st.markdown(CSS, unsafe_allow_html=True)

    # ---------------- header + logout
    h1, h2 = st.columns([5, 1], vertical_alignment="center")
    with h1:
        st.title("👤 My Profile")
        st.caption("Manage your account, security and activity")
    with h2:
        if st.button("Logout", key="pf_logout", icon=":material/logout:", use_container_width=True):
            _logout()

    doc, prefs, overview, recent, perms = _load(db, user)
    role = doc.get("role", user["role"])
    role_label = role.title()
    status = doc.get("status", "active")
    tfa = bool(doc.get("two_factor"))

    # Google profile (agar valid ho to wohi dikhao)
    g = _google_info(doc)
    is_google = g is not None
    show_name = (g["name"] if is_google and g["name"] else doc.get("name", ""))
    show_email = (g["email"] if is_google else doc.get("email", ""))
    if is_google and g["picture"]:
        avatar = f'<img class="pf-avatar" src="{html.escape(g["picture"], quote=True)}" referrerpolicy="no-referrer" alt="">'
    else:
        avatar = f'<div class="pf-avatar">{_initials(show_name)}</div>'

    left, right = st.columns([1, 2.6], gap="medium")

    # ---------------- LEFT
    with left:
        with st.container(border=True):
            badges = _tag(role_label, "pf-g") + (" " + _tag("Google", "pf-b") if is_google else "")
            st.markdown(f'{avatar}'
                        f'<div class="pf-name">{html.escape(show_name)}</div>'
                        f'<div class="pf-mail">{html.escape(show_email)}</div>'
                        f'<div class="pf-center">{badges}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Account Stats")
            st.markdown(
                _row("Member since", f"<b>{_dmy(doc.get('created_at'))}</b>")
                + _row("Last login", f"<b>{_timeago(doc.get('last_login'))}</b>")
                + _row("Sign-in method", f"<b>{'Google' if is_google else 'Email & password'}</b>")
                + _row("Role", _tag(role_label, "pf-g"))
                + _row("Status", _tag(status.title(), "pf-g" if status == "active" else "pf-r"))
                + _row("Access level", f"<b>{ACCESS.get(role, '-')}</b>"), unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Security")
            pw_row = ("" if is_google else
                      _row("Password changed", f"<b>{_timeago(doc.get('password_changed_at'))}</b>"))
            st.markdown(
                _row("Two-factor auth", _tag("Enabled" if tfa else "Off", "pf-g" if tfa else "pf-a"))
                + pw_row
                + _row("Data encryption", _tag("AES-256", "pf-b")), unsafe_allow_html=True)

    # ---------------- RIGHT
    with right:
        with st.container(border=True):
            st.subheader("Activity Overview  ·  Last 30 days")
            bars = "".join(
                f'<div class="pf-bar-wrap"><span class="l">{o["label"]}</span>'
                f'<div class="pf-bar"><i class="{"r" if o["label"] == "Alerts" else ""}" style="width:{o["pct"]}%"></i></div>'
                f'<span class="c">{o["count"]}</span></div>' for o in overview)
            st.markdown(bars, unsafe_allow_html=True)

        main, side = st.columns([1.2, 1], gap="medium")

        with main:
            with st.container(border=True):
                with st.form("pf_info"):
                    st.subheader("Personal Information")
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Full Name", show_name)
                    # Google wale ka email Google se bandha hota hai, isliye badalne nahi dete
                    email = c2.text_input("Email", show_email, disabled=is_google)
                    c1.text_input("Role", role_label, disabled=True)
                    dept = c2.text_input("Department", doc.get("department", "") or "")
                    tzs = TIMEZONES if doc.get("timezone", "Asia/Karachi") in TIMEZONES else [doc["timezone"]] + TIMEZONES
                    lgs = LANGUAGES if doc.get("language", "English") in LANGUAGES else [doc["language"]] + LANGUAGES
                    tz = c1.selectbox("Time zone", tzs, index=tzs.index(doc.get("timezone", "Asia/Karachi")))
                    lang = c2.selectbox("Language", lgs, index=lgs.index(doc.get("language", "English")))
                    if st.form_submit_button("Save Changes", type="primary"):
                        _save_profile(db, user, name, email, dept, tz, lang)

                if is_google:
                    st.subheader("Change Password")
                    st.info("Aap Google se sign in hain, password aapke Google account se manage hota hai.")
                else:
                    with st.form("pf_pass", clear_on_submit=True):
                        st.subheader("Change Password")
                        p1, p2, p3 = st.columns(3)
                        cur = p1.text_input("Current", type="password")
                        new = p2.text_input("New", type="password")
                        con = p3.text_input("Confirm", type="password")
                        if st.form_submit_button("Update Password", type="primary"):
                            _change_password(db, user, cur, new, con)

                st.subheader(f"Role Permissions  ·  {role_label}")
                if perms:
                    st.markdown('<div class="pf-perms">' + "".join(_tag(p, "pf-g") for p in perms) + "</div>",
                                unsafe_allow_html=True)
                else:
                    st.caption("No permission data available.")

        with side:
            notif = prefs.get("notif", {})
            with st.form("pf_notif"), st.container(border=True):
                st.subheader("Notification Preferences")
                e = st.toggle("Email alerts", value=notif.get("email", True))
                r = st.toggle("Real-time anomaly alerts", value=notif.get("realtime", True))
                w = st.toggle("Weekly climate report", value=notif.get("weekly", False))
                if st.form_submit_button("Save Preferences", use_container_width=True):
                    db.settings.update_one({"_id": user["id"]},
                                           {"$set": {"notif": {"email": e, "realtime": r, "weekly": w}}},
                                           upsert=True)
                    st.success("Preferences saved")
            with st.container(border=True):
                st.subheader("Recent Activity")
                if not recent:
                    st.caption("No activity yet.")
                st.markdown("".join(_row(html.escape(a["text"]), f'<span class="m">{_timeago(a["created_at"])}</span>')
                                    for a in recent), unsafe_allow_html=True)