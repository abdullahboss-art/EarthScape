"""Google login helper (Streamlit st.login) - EarthScape app ke MongoDB users se jodta hai.

Zaroorat:
    pip install "streamlit[auth]"
    .streamlit/secrets.toml mein [auth] + [auth.google] section
"""
import datetime
import re

import streamlit as st


def google_button(label="Continue with Google", key="google_login"):
    """Login.py / signup.py mein kahin bhi ye button lagayein."""
    st.button(label, key=key, icon=":material/login:",
              on_click=st.login, args=["google"], use_container_width=True)


def google_user_to_session(db):
    """Agar Google se login ho chuka hai to DB ka user dhoondo (ya naya banao)
    aur st.session_state['user'] set karo. True return karta hai agar set hua."""
    if not st.user.is_logged_in:
        return False

    email = (st.user.get("email") or "").strip().lower()
    if not email or st.user.get("email_verified") is False:
        st.error("Google account ki email verified nahi hai.")
        return False

    doc = db.users.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}})
    if not doc:
        name = st.user.get("name") or email.split("@")[0]
        res = db.users.insert_one({
            "name": name,
            "email": email,
            "role": "viewer",              # naya Google user hamesha viewer; admin baad mein role badle
            "provider": "google",
            "created": datetime.datetime.utcnow(),
        })
        doc = db.users.find_one({"_id": res.inserted_id})

    st.session_state["user"] = {
        "id": str(doc["_id"]),
        "name": doc.get("name") or email.split("@")[0],
        "email": email,
        "role": doc.get("role", "viewer"),
    }
    return True


def google_logout_if_needed():
    """App ke Logout button par call karein, warna Google session zinda rehta hai
    aur user foran dobara login ho jata hai."""
    if st.user.is_logged_in:
        st.logout()
