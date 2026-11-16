"""EarthScape - Backup & Security page.
Encrypted backups (Fernet: AES-128 + HMAC), restore, and automatic daily backup.
Key: [security] backup_key in .streamlit/secrets.toml, otherwise data/backup.key (created automatically).
"""
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from bson import json_util
from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parent
BACKUP_DIR = ROOT / "data" / "backups"
KEY_FILE = ROOT / "data" / "backup.key"
COLLECTIONS = ["records", "alerts", "thresholds", "settings", "uploads", "stations", "report_log", "feedback",
               "users", "alert_rules", "permissions", "pipeline_jobs", "pipeline_results", "satellite_images"]
KEEP = 7            # sirf latest 7 backups rakhe jate hain
AUTO_HOURS = 24     # itne ghante se purana backup ho to naya khud ban jata hai


def _fernet():
    key = None
    try:
        key = (st.secrets["security"]["backup_key"] or "").encode() or None
    except Exception:
        pass
    if key is None:
        if not KEY_FILE.exists():
            KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            KEY_FILE.write_bytes(Fernet.generate_key())
        key = KEY_FILE.read_bytes()
    return Fernet(key)


def _files():
    return sorted(BACKUP_DIR.glob("*.esbak")) if BACKUP_DIR.exists() else []


def create_backup(db):
    now = datetime.datetime.utcnow()
    data = {c: list(db[c].find({})) for c in COLLECTIONS}
    raw = json_util.dumps({"version": 1, "created": now.isoformat(), "data": data}).encode("utf-8")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKUP_DIR / f"earthscape_{now:%Y%m%d_%H%M%S}.esbak"
    path.write_bytes(_fernet().encrypt(raw))
    for old in _files()[:-KEEP]:
        old.unlink()
    return path


def restore_backup(db, token):
    """Raises InvalidToken if the key is wrong or the file is damaged."""
    payload = json_util.loads(_fernet().decrypt(token).decode("utf-8"))
    for name, docs in payload["data"].items():
        if name not in COLLECTIONS:
            continue
        db[name].delete_many({})
        if docs:
            db[name].insert_many(docs)
    try:
        import analytics
        analytics._cache.update(n=None, df=None)     # dashboard cache refresh
    except Exception:
        pass
    return {k: len(v) for k, v in payload["data"].items()}


def auto_backup(db, hours=AUTO_HOURS):
    """app.py har run par bulata hai; sirf tab backup banta hai jab purana ho chuka ho."""
    try:
        files = _files()
        if db.records.estimated_document_count() == 0:
            return None
        if files and (datetime.datetime.now().timestamp() - files[-1].stat().st_mtime) < hours * 3600:
            return None
        return create_backup(db)
    except Exception:
        return None


def backup_page(db, user):
    st.title("🛡️ Backup & Security")
    files = _files()
    c = st.columns(3)
    c[0].metric("Backups stored", len(files))
    c[1].metric("Last backup", datetime.datetime.fromtimestamp(files[-1].stat().st_mtime).strftime("%d %b %H:%M") if files else "never")
    c[2].metric("Encryption", "Fernet (AES-128)")

    with st.container(border=True):
        st.subheader("Create backup")
        st.caption(f"A new encrypted backup is also created automatically every {AUTO_HOURS} hours "
                   f"(latest {KEEP} are kept). Backups are saved in data/backups.")
        if st.button("Create backup now", type="primary"):
            p = create_backup(db)
            st.success(f"Saved {p.name} ({p.stat().st_size / 1024:,.0f} KB)")
            st.rerun()
        if files:
            st.dataframe(pd.DataFrame([{"File": f.name, "Size (KB)": round(f.stat().st_size / 1024),
                                        "Created": datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d %b %Y %H:%M")}
                                       for f in reversed(files)]), width="stretch", hide_index=True)
            pick = st.selectbox("Download", [f.name for f in reversed(files)])
            st.download_button("Download encrypted backup", (BACKUP_DIR / pick).read_bytes(), pick,
                               "application/octet-stream")

    with st.container(border=True):
        st.subheader("Restore")
        st.warning("Restoring replaces the current data with the backup. The backup key must be the same one used to create it.")
        src = st.radio("Restore from", ["A stored backup", "An uploaded .esbak file"], horizontal=True)
        token = None
        if src == "A stored backup" and files:
            token = (BACKUP_DIR / st.selectbox("Backup", [f.name for f in reversed(files)], key="rs_pick")).read_bytes()
        elif src != "A stored backup":
            up = st.file_uploader("Backup file", type=["esbak"])
            token = up.getvalue() if up else None
        ok = st.checkbox("I understand that current data will be replaced")
        if st.button("Restore", disabled=not (token and ok)):
            try:
                st.success("Restored: " + ", ".join(f"{k} {v}" for k, v in restore_backup(db, token).items() if v))
            except InvalidToken:
                st.error("Cannot decrypt: wrong key or damaged file.")
            except Exception as e:
                st.error(str(e))

    with st.container(border=True):
        st.subheader("Security status")
        rows = [("Passwords", "✅ stored as PBKDF2 hashes"),
                ("Access control", "✅ role-based (Roles & Permissions page)"),
                ("Backups", "✅ encrypted (Fernet) and rotated"),
                ("Backup key", "✅ in secrets.toml [security]" if _has_secret_key() else "⚠️ data/backup.key (keep it safe, never share or zip it)"),
                ("Encryption in transit", "⚪ enable HTTPS when deploying: streamlit run app.py --server.sslCertFile cert.pem --server.sslKeyFile key.pem; MongoDB: tls=true")]
        st.table(pd.DataFrame(rows, columns=["Item", "Status"]).set_index("Item"))


def _has_secret_key():
    try:
        return bool(st.secrets["security"]["backup_key"])
    except Exception:
        return False
