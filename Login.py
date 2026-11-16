"""EarthScape - LOGIN page (split-screen design).
Sign-up page is in signup.py (it re-uses shell() and hash_pw() from this file).

Images (optional) go in  assets/  next to this file:
    assets/login_bg.png   left side picture (.jpg/.jpeg/.webp also work)
    assets/logo.png       logo above "EarthScape" (.svg/.webp also work)

Google sign-in uses st.login("google")  ->  needs [auth] + [auth.google] in .streamlit/secrets.toml
and:  pip install Authlib>=1.3.2
"""
import base64
import hashlib
import html
import re
import secrets
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"


# ------------------------------------------------------------------ password helpers
def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()


def check_pw(pw, stored):
    return secrets.compare_digest(hash_pw(pw, stored.split("$")[0]), stored)


# ------------------------------------------------------------------ validation (shared by login + signup)
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def validate_name(v):
    if not v:
        return "Full name is required."
    if len(v) < 2:
        return "Full name must be at least 2 characters."
    if len(v) > 60:
        return "Full name must be 60 characters or fewer."
    if not v[0].isalpha() or not all(c.isalpha() or c in " .'-" for c in v):
        return "Full name can only contain letters, spaces, apostrophes, dots and hyphens."


def validate_email(v):
    if not v:
        return "Email address is required."
    if len(v) > 254 or not EMAIL_RE.match(v):
        return "Enter a valid email address (e.g. name@example.com)."


def validate_new_password(v):
    if not v:
        return "Password is required."
    if len(v) < 8:
        return "Password must be at least 8 characters."
    if len(v) > 128:
        return "Password must be 128 characters or fewer."
    if " " in v:
        return "Password cannot contain spaces."
    if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
        return "Password must contain at least one letter and one number."


def show_error(placeholder, text):
    """Red message directly under a field."""
    placeholder.markdown(f'<div class="field-err">⚠ {html.escape(text)}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ styling
def _asset_uri(*names):
    """base64 data-URI of the first existing file in assets/, else None."""
    folders = [ASSETS, Path(__file__).parent, Path.cwd() / "assets", Path.cwd()]
    for n in names:
        p = next((f / n for f in folders if (f / n).exists()), None)
        if p:
            ext = p.suffix.lower().lstrip(".")
            mime = "image/svg+xml" if ext == "svg" else f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
            return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    return None


ICON_MAIL = "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4-8 5-8-5V6l8 5 8-5z"
ICON_LOCK = "M18 8h-1V6a5 5 0 0 0-10 0v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2zM9 6a3 3 0 0 1 6 0v2H9zm3 11a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"
ICON_USER = "M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-3.3 0-10 1.7-10 5v3h20v-3c0-3.3-6.7-5-10-5z"

# real Google "G" logo (svg, '#' -> %23 so it works inside a CSS url())
GOOGLE_G = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
            "<path fill='#EA4335' d='M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z'/>"
            "<path fill='#4285F4' d='M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z'/>"
            "<path fill='#FBBC05' d='M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z'/>"
            "<path fill='#34A853' d='M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z'/>"
            "</svg>").replace("#", "%23")


def _icon_css(key, path):
    return (f".st-key-{key} input{{padding-left:46px!important;background:url(\"data:image/svg+xml;utf8,"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24' fill='%23c9d6e6'>"
            f"<path d='{path}'/></svg>\") no-repeat 14px center transparent!important}}")


EXTRA_CSS = """
/* inputs: ek hi dark-blue color */
.st-key-authright [data-baseweb=input],.st-key-authright [data-baseweb=base-input]{background:#0b1f35!important}
.st-key-authright [data-baseweb=input]{border:1px solid #1d3a5a!important;border-radius:10px!important}
.st-key-authright [data-baseweb=base-input]{border:0!important}
.st-key-authright [data-baseweb=input]:focus-within{border-color:#3ddc84!important}
.st-key-authright input{color:#fff!important}

/* Forgot Password: right align + vertical center */
.st-key-forgot{display:flex;justify-content:flex-end}
.st-key-forgot button{width:auto!important}
.st-key-forgot button p{margin:0;font-size:14px}
.st-key-authright [data-testid=stCheckbox] label p{margin:0}

/* Login button */
.st-key-login_btn button{background:linear-gradient(90deg,#58df57,#00bffb)!important;border:0!important}
.st-key-login_btn button p{color:#06210f!important;font-weight:700;font-size:16px;margin:0}
.st-key-login_btn button:hover{filter:brightness(1.08)}

/* Google button + real G logo */
.st-key-google button{background:#0b1f35!important;border:1px solid #1d3a5a!important;color:#fff!important}
.st-key-google button:hover{border-color:#3ddc84!important}
.st-key-google button p{display:flex;align-items:center;justify-content:center;margin:0}
.st-key-google button p:before{content:"";display:inline-block;width:24px;height:24px;border-radius:50%;margin-right:10px;
  background:#fff url("data:image/svg+xml;utf8,__G__") no-repeat center/14px 14px}

/* "Don't have an account? Sign Up" */
.switch-txt{padding:0 6px 0 0!important;line-height:1}
.st-key-to_register button p,.st-key-to_login button p{margin:0}
""".replace("__G__", GOOGLE_G)


AUTH_CSS = """<style>
.st-key-authcard{border:1px solid #1d4a7a;border-radius:18px;overflow:hidden;padding:0!important;
  background:rgba(6,20,36,.94);box-shadow:0 0 50px rgba(0,140,255,.18)}
.st-key-authcard [data-testid=stHorizontalBlock]{gap:0!important}
.auth-img{height:680px;background-size:cover;background-position:center;background-color:#0a2a52}
.st-key-authright{padding:30px 44px 24px 44px}
.auth-logo{text-align:center;font-size:58px;line-height:1.1}
.auth-logo img{height:84px}
.auth-brand{text-align:center;font-size:30px;font-weight:700;line-height:1.1}.auth-brand span{color:#3ddc84}
.auth-agency{text-align:center;font-size:12px;color:#d3e0ee;margin-bottom:22px}
.auth-title{text-align:center;font-size:28px;font-weight:700;color:#fff;margin:0}
.auth-sub{text-align:center;font-size:13px;color:#c9d6e6;margin-bottom:18px}
.auth-or{display:flex;align-items:center;gap:12px;color:#8ea6bf;font-size:12px;margin:6px 0 10px}
.auth-or:before,.auth-or:after{content:"";flex:1;border-top:1px solid #1d3a5a}
.st-key-authright [data-baseweb=input],.st-key-authright [data-baseweb=select]>div{background:#0b1f35!important;
  border:1px solid #1d3a5a!important;border-radius:10px!important}
.st-key-authright input{height:46px}
.st-key-authright div.stFormSubmitButton>button,.st-key-authright div.stButton>button{height:46px;border-radius:10px}
.st-key-authright div.stFormSubmitButton>button{background:linear-gradient(90deg,#58df57,#00bffb);color:#06210f;border:0;font-weight:700}
.st-key-forgot button{background:none!important;border:0!important;color:#3ddc84!important;font-weight:600!important;
  justify-content:flex-end;padding:0!important;height:auto!important;min-height:0!important}
.st-key-to_register button,.st-key-to_login button{background:none;border:0;color:#3ddc84;font-weight:600;padding:0;
  justify-content:flex-start;height:auto;min-height:0}
.switch-txt{text-align:right;color:#c9d6e6;font-size:13px;padding-top:4px}
.field-err{color:#ff6b6b;font-size:12.5px;margin:-8px 0 10px 4px;line-height:1.35}
""" + _icon_css("login_email", ICON_MAIL) + _icon_css("login_pw", ICON_LOCK) \
    + _icon_css("reg_name", ICON_USER) + _icon_css("reg_email", ICON_MAIL) + _icon_css("reg_pw", ICON_LOCK) \
    + _icon_css("reg_pw2", ICON_LOCK) + EXTRA_CSS + "</style>"


# ------------------------------------------------------------------ layout
def shell(title, subtitle, body):
    """Split-screen card: picture on the left, form (body callback) on the right."""
    st.markdown(AUTH_CSS, unsafe_allow_html=True)
    bg = _asset_uri("Login-bg.jpg", "Login-bg.png", "Login-bg.jpeg", "login_bg.png", "login_bg.jpg", "login_bg.jpeg", "login_bg.webp")
    bg_css = f"url('{bg}')" if bg else "linear-gradient(160deg,#0c2f5a,#0a6b4a)"
    logo = _asset_uri("Earth_logo.png", "Earth_logo.jpg", "logo.png", "logo.svg", "logo.webp")
    logo_html = f'<img src="{logo}">' if logo else "🌍"
    _, mid, _ = st.columns([1, 3.2, 1])
    with mid:
        with st.container(key="authcard"):
            left, right = st.columns([1.05, 1])
            left.markdown(f'<div class="auth-img" style="background-image:{bg_css}"></div>', unsafe_allow_html=True)
            with right:
                with st.container(key="authright"):
                    st.markdown(f'<div class="auth-logo">{logo_html}</div>'
                                '<div class="auth-brand">Earth<span>Scape</span></div>'
                                '<div class="auth-agency">Climate Agency</div>'
                                f'<div class="auth-title">{title}</div><div class="auth-sub">{subtitle}</div>',
                                unsafe_allow_html=True)
                    body()


# ------------------------------------------------------------------ login page
def _login_body(db):
    if st.session_state.pop("just_registered", False):
        st.success("Account created successfully. Please log in.")
    with st.form("login", border=False):
        email = st.text_input("Email Address", key="login_email", placeholder="Email Address", label_visibility="collapsed")
        email_err = st.empty()
        pw = st.text_input("Password", type="password", key="login_pw", placeholder="Password", label_visibility="collapsed")
        pw_err = st.empty()
        r1, r2 = st.columns(2, vertical_alignment="center")
        r1.checkbox("Remember Me", key="login_remember")
        forgot = r2.form_submit_button("Forgot Password?", key="forgot")
        submitted = st.form_submit_button("Login", key="login_btn", width="stretch")
    if forgot:
        st.info("Password reset is not available yet. Please contact your administrator.")
    if submitted:
        email_n = email.strip().lower()
        e_msg = validate_email(email_n)
        p_msg = None if pw else "Password is required."
        if e_msg:
            show_error(email_err, e_msg)
        if p_msg:
            show_error(pw_err, p_msg)
        if not e_msg and not p_msg:
            u = db.users.find_one({"email": email_n})
            if not u:                                   # not registered -> cannot log in
                show_error(email_err, "No account found with this email. Please sign up first.")
            elif not u.get("password"):                 # account created via Google
                show_error(pw_err, "This account uses Google sign-in. Please use 'Continue with Google'.")
            elif not check_pw(pw, u["password"]):
                show_error(pw_err, "Incorrect password. Please try again.")
            else:
                st.session_state["user"] = {"id": str(u["_id"]), "name": u["name"], "role": u["role"]}
                st.rerun()
    st.markdown('<div class="auth-or">OR</div>', unsafe_allow_html=True)
    st.button("Continue with Google", key="google", width="stretch",
              on_click=st.login, args=["google"])
    a, b = st.columns([1.5, 1], vertical_alignment="center")
    a.markdown('<div class="switch-txt">Don\'t have an account?</div>', unsafe_allow_html=True)
    if b.button("Sign Up", key="to_register"):
        st.session_state["auth_view"] = "register"
        st.rerun()


def _google_login_flow(db):
    """Google redirect ke baad st.user fill hota hai -> app session bana do."""
    if not st.user.get("is_logged_in"):
        return
    email = (st.user.get("email") or "").strip().lower()
    if not email or not st.user.get("email_verified", True):
        return
    u = db.users.find_one({"email": email})
    if not u:
        name = st.user.get("name") or email.split("@")[0]
        res = db.users.insert_one({"name": name, "email": email, "password": None,
                                   "role": "user", "provider": "google"})   # role signup.py wale default se match rakho
        u = {"_id": res.inserted_id, "name": name, "role": "user"}
    st.session_state["user"] = {"id": str(u["_id"]), "name": u["name"], "role": u["role"]}
    st.rerun()


# ------------------------------------------------------------------ public entry point
def login_page(db):
    _google_login_flow(db)
    shell("Welcome Back!", "Sign in to your account", lambda: _login_body(db))