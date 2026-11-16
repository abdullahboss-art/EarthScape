"""EarthScape - SIGN-UP page (same design as login.py).

Usage in app.py:
    from signup import register_page
    register_page(db)
"""
import streamlit as st

from Login import hash_pw, shell, show_error, validate_email, validate_name, validate_new_password


def _register_body(db):
    with st.form("register", border=False):
        name = st.text_input("Full name", key="reg_name", placeholder="Full Name", label_visibility="collapsed")
        name_err = st.empty()
        email = st.text_input("Email address", key="reg_email", placeholder="Email Address", label_visibility="collapsed")
        email_err = st.empty()
        pw = st.text_input("Password", type="password", key="reg_pw", placeholder="Password (min 8 characters)", label_visibility="collapsed")
        pw_err = st.empty()
        pw2 = st.text_input("Confirm password", type="password", key="reg_pw2", placeholder="Confirm Password", label_visibility="collapsed")
        pw2_err = st.empty()
        role = st.selectbox("Select role", ["analyst", "viewer"], key="reg_role", label_visibility="collapsed",
                            format_func=lambda r: {"analyst": "Analyst (upload + analyse)",
                                                   "viewer": "Viewer (read only)"}[r])
        submitted = st.form_submit_button("Sign Up", width="stretch")
    if submitted:
        name, email = name.strip(), email.strip().lower()
        errors = [(name_err, validate_name(name)),
                  (email_err, validate_email(email)),
                  (pw_err, validate_new_password(pw)),
                  (pw2_err, "Please confirm your password." if not pw2
                   else "Passwords do not match." if pw != pw2 else None)]
        failed = False
        for box, msg in errors:
            if msg:
                show_error(box, msg)
                failed = True
        if not failed and db.users.find_one({"email": email}):
            show_error(email_err, "This email is already registered. Please log in.")
            failed = True
        if not failed:
            if db.users.count_documents({}) == 0:
                role = "admin"          # first account = administrator
            db.users.insert_one({"name": name, "email": email, "password": hash_pw(pw), "role": role})
            st.session_state["just_registered"] = True
            st.session_state["login_email"] = email      # prefill the login form
            st.session_state["auth_view"] = "login"
            st.rerun()
    a, b = st.columns([1.5, 1])
    a.markdown('<div class="switch-txt">Already have an account?</div>', unsafe_allow_html=True)
    if b.button("Login", key="to_login"):
        st.session_state["auth_view"] = "login"
        st.rerun()


def register_page(db):
    shell("Create Account", "Join EarthScape today", lambda: _register_body(db))