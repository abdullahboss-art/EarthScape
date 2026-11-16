"""Support & Feedback page for EarthScape.

app.py mein:
    from support_page import support_page
    PAGES = {..., "Support & Feedback": lambda u: support_page(db, u), ...}

Email ke liye .streamlit/secrets.toml (support_page.py / app.py wale folder mein):
    [smtp]
    host     = "smtp.gmail.com"
    port     = 465
    user     = "your-email@gmail.com"
    password = "YOUR_NEW_GMAIL_APP_PASSWORD"
    to       = "your-email@gmail.com"
"""

import base64
import datetime
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import streamlit as st


SUPPORT_EMAIL = "abdullahmusharraf576@gmail.com"

BASE_DIR = Path(__file__).resolve().parent
GLOBE_IMG = BASE_DIR / "assets" / "support_globe.png"
SECRETS_FILE = BASE_DIR / ".streamlit" / "secrets.toml"

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


# =========================
# FAQS
# =========================

FAQS = [
    (
        "How to upload data?",
        "Open **Data Upload**, drag and drop a CSV / Excel / JSON file, "
        "then press *Upload & analyse*.",
    ),
    (
        "What data formats are supported?",
        "CSV, XLSX and JSON with at least date, station and temperature columns.",
    ),
    (
        "How to set up alerts?",
        "Alert limits are set by an administrator in **Alerts / Settings**. "
        "New readings above a limit create alerts automatically.",
    ),
    (
        "Is my data secure?",
        "Yes. Data is stored in our database and only logged-in users "
        "can access it, based on their role.",
    ),
]


# =========================
# CSS DESIGN
# =========================

CSS = """
<style>
.st-key-card_faq,
.st-key-card_contact {
    background: linear-gradient(160deg, rgba(12,36,64,.92), rgba(6,20,36,.92));
    border: 1px solid #1b4a73;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 0 24px rgba(0,120,220,.12);
}
.es-card-title {
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 12px;
}
.st-key-card_faq [data-testid=stExpander] {
    background: rgba(10,32,54,.85);
    border: 1px solid #173f63;
    border-radius: 12px;
    margin-bottom: 8px;
}
.st-key-card_faq [data-testid=stExpander] summary {
    padding: .55rem .8rem;
    color: #e6f0fb;
}
.es-muted {
    color: #8ea6bf;
    font-size: 13px;
    margin-top: 10px;
}
.es-banner {
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    gap: 16px;
    min-height: 130px;
    margin-top: 18px;
    padding: 20px 24px;
    border-radius: 16px;
    border: 1px solid #1b4a73;
    background: linear-gradient(160deg, rgba(12,36,64,.92), rgba(6,20,36,.92));
}
.es-banner .ic { font-size: 44px; }
.es-banner b { display: block; font-size: 20px; color: #fff; }
.es-banner span { color: #9db4cc; }
.es-banner img {
    position: absolute;
    right: -10px;
    bottom: -30px;
    height: 190px;
    pointer-events: none;
}
</style>
"""


# =========================
# SMTP CONFIGURATION
# =========================

def _read_toml(path):
    try:
        import tomllib as t  # Python 3.11+
    except ImportError:
        import tomli as t  # Python < 3.11: pip install tomli
    with open(path, "rb") as f:
        return t.load(f)


def _smtp_cfg():
    """Returns (cfg, error).

    Pehle st.secrets try karta hai, phir support_page.py wale folder ki
    .streamlit/secrets.toml seedha parh leta hai.
    """
    cfg = None

    try:
        cfg = dict(st.secrets["smtp"])
    except Exception:
        cfg = None

    if cfg is None:
        if not SECRETS_FILE.exists():
            # backticks zaroori hain, warna markdown backslash kha jata hai
            return None, f"File nahi mili: `{SECRETS_FILE}` -> is jagah secrets.toml banayein."
        try:
            cfg = dict(_read_toml(SECRETS_FILE).get("smtp", {}))
        except Exception as e:
            return None, f"File mili (`{SECRETS_FILE}`) lekin parh nahi saka: {type(e).__name__}: {e}"

    if not (cfg.get("user") and cfg.get("password")):
        return None, f"[smtp] section mein user/password nahi mile (keys: {list(cfg)})"

    # Gmail app password spaces ke saath bhi chalta hai
    cfg["password"] = str(cfg["password"]).replace(" ", "")
    return cfg, None


# =========================
# SEND EMAIL
# =========================

def _send(cfg, msg):
    host = cfg.get("host", "smtp.gmail.com")
    port = int(cfg.get("port", 465))

    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20) as s:
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)


def send_support_email(cfg, user_email, user_name, message):
    """1) Support inbox ko message (Reply-To = user)  2) User ko confirmation copy."""
    to_addr = cfg.get("to", SUPPORT_EMAIL)

    support_msg = EmailMessage()
    support_msg["Subject"] = f"[EarthScape Support] Message from {user_name}"
    support_msg["From"] = cfg["user"]
    support_msg["To"] = to_addr
    support_msg["Reply-To"] = user_email
    support_msg.set_content(f"From: {user_name} <{user_email}>\n\n{message}")
    _send(cfg, support_msg)

    confirmation_msg = EmailMessage()
    confirmation_msg["Subject"] = "We received your message - EarthScape Climate Agency"
    confirmation_msg["From"] = cfg["user"]
    confirmation_msg["To"] = user_email
    confirmation_msg.set_content(
        f"Hi {user_name},\n\n"
        "Thanks for contacting EarthScape Support. "
        "We received your message and will get back to you soon.\n\n"
        f"Your message:\n{message}\n\n"
        "- EarthScape Climate Agency"
    )
    try:
        _send(cfg, confirmation_msg)
    except Exception:
        pass  # confirmation fail ho to bhi support email chali gayi hai


# =========================
# GLOBE IMAGE
# =========================

def _globe_html():
    if not GLOBE_IMG.exists():
        return ""
    b64 = base64.b64encode(GLOBE_IMG.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}" alt="EarthScape Globe">'


# =========================
# SUPPORT & FEEDBACK PAGE
# =========================

def support_page(db, user):
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Support & Feedback")

    left, right = st.columns(2, gap="large")

    # ---------- LEFT: FAQ ----------
    with left:
        with st.container(key="card_faq"):
            st.markdown(
                "<div class='es-card-title'>Frequently Asked Questions</div>",
                unsafe_allow_html=True,
            )
            for question, answer in FAQS:
                with st.expander(question):
                    st.write(answer)

    # ---------- RIGHT: CONTACT ----------
    with right:
        with st.container(key="card_contact"):
            st.markdown(
                "<div class='es-card-title'>Contact Us</div>",
                unsafe_allow_html=True,
            )

            with st.form("support_form", clear_on_submit=True, border=False):
                email = st.text_input("Email", placeholder="you@example.com")
                message = st.text_area(
                    "Message", height=140, placeholder="Tell us how we can help..."
                )
                sent = st.form_submit_button("Send Message", type="primary")

            if sent:
                email = email.strip()
                message = message.strip()

                if not EMAIL_RE.match(email):
                    st.error("Please enter a valid email address.")
                elif len(message) < 5:
                    st.error("Please write a message (at least 5 characters).")
                else:
                    db.feedback.insert_one({
                        "name": user["name"],
                        "email": email,
                        "type": "support",
                        "message": message,
                        "time": datetime.datetime.utcnow(),
                    })

                    cfg, err = _smtp_cfg()

                    if not cfg:
                        st.warning(
                            "Message saved, but email is not configured yet "
                            "(add [smtp] in .streamlit/secrets.toml)."
                        )
                        st.error(f"Secrets problem: {err}")
                    else:
                        try:
                            with st.spinner("Sending..."):
                                send_support_email(cfg, email, user["name"], message)
                            st.success(
                                "Thanks! Your message has been sent. "
                                "A confirmation was emailed to you."
                            )
                        except Exception as e:
                            st.error(f"Message saved, but the email could not be sent: {e}")

            st.markdown(
                f"<div class='es-muted'>Or email: {SUPPORT_EMAIL}</div>",
                unsafe_allow_html=True,
            )

    # ---------- BOTTOM BANNER ----------
    # NOTE: HTML ek hi string mein, bina indentation / blank lines ke.
    # Warna markdown isay code block bana deta hai.
    banner_html = (
        "<div class='es-banner'>"
        "<div class='ic'>🎧</div>"
        "<div>"
        "<b>We're here to help!</b>"
        "<span>Get in touch for any questions or suggestions.</span>"
        "</div>"
        f"{_globe_html()}"
        "</div>"
    )
    st.markdown(banner_html, unsafe_allow_html=True)