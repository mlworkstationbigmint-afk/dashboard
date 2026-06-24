"""
Demo per-user authentication for the BigMint - AI Labs portal.

NOTE: this is front-end / demo-grade auth only (passwords are SHA-256 hashed,
no real backend or session server). It demonstrates per-user login for the
prototype and is NOT production-grade access control.
"""
import hashlib
import streamlit as st


def _h(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# username -> profile. Passwords below are the plain values for the demo;
# only the SHA-256 hash is stored here.
USERS = {
    "adani":   {"name": "Adani User",       "role": "Adani",   "hash": "49dda5e40cc5502a4640d5eb0a5189011e1eba0c190bd421bc9eb24f7fa51060"},  # Adani@2026
    "admin":   {"name": "Administrator",    "role": "Admin",   "hash": "a36aef5a11c4073fbe60314fc9df530a9d5f986533594d1f5190742ff9e0e408"},  # Admin@2026
    "analyst": {"name": "BigMint Analyst",  "role": "Analyst", "hash": "345982ba4e71cf6789b88de67e9b5f769ff011065010a273bae02fee9ccead97"},  # Analyst@2026
}

# Shown on the login screen so the demo is easy to access.
DEMO_CREDENTIALS = [
    ("adani",   "Adani@2026"),
    ("admin",   "Admin@2026"),
    ("analyst", "Analyst@2026"),
]


def authenticate(username: str, password: str):
    """Return the user profile dict on success, else None."""
    u = USERS.get(str(username).strip().lower())
    if u and _h(password) == u["hash"]:
        return {"username": str(username).strip().lower(), **u}
    return None


def logout():
    for k in ("user", "nav", "calc"):
        st.session_state.pop(k, None)
    st.rerun()
