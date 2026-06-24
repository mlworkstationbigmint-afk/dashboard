"""
BigMint - AI Labs portal: brand theme, CSS and shared UI helpers.
Colours sampled from the bigmint.co logo/site (blue + orange accent).
"""
import os
import base64
import streamlit as st

# ---- Brand palette ----
PRIMARY      = "#024CA1"   # BigMint blue (logo bg -> seamless top bar)
PRIMARY_DARK = "#023A7A"
PRIMARY_SOFT = "#EAF1FB"
ACCENT       = "#EE4E24"   # orange / red CTA accent
SUCCESS      = "#1F9D55"   # up
DANGER       = "#D8382B"   # down
NEUTRAL      = "#64748B"   # flat / muted
BG_SOFT      = "#F4F6FA"

# chart line colours (actual = light blue, forecast = bold red w/ soft halo)
SPOT_LINE     = "#5E92D6"
SPOT_DARK     = "#1F5FA8"
FORECAST_LINE = "#E12B20"
FORECAST_HALO = "rgba(225,43,32,0.16)"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH  = os.path.join(ASSETS_DIR, "bigmint_logo.png")


def _logo_html(height: int = 30) -> str:
    if os.path.exists(LOGO_PATH):
        try:
            with open(LOGO_PATH, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"<img src='data:image/png;base64,{b64}' style='height:{height}px;display:block;'/>"
        except Exception:
            pass
    return ("<span style='font-weight:800;font-size:22px;letter-spacing:.6px;color:#fff;'>BIGMINT</span>")


def inject_css():
    st.markdown(f"""
<style>
.stApp {{ background-color: {BG_SOFT}; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 2rem; max-width: 1180px; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
#MainMenu, footer {{ visibility: hidden; }}
section[data-testid="stSidebar"], div[data-testid="collapsedControl"] {{ display: none !important; }}

/* ---------- top brand bar ---------- */
.bm-topbar {{
    background: {PRIMARY}; border-radius: 12px; padding: 13px 22px;
    display: flex; align-items: center; justify-content: space-between;
    margin: 0 0 14px 0; box-shadow: 0 2px 10px rgba(2,76,161,.18);
}}
.bm-topbar-l {{ display:flex; align-items:center; gap:14px; }}
.bm-portal-title {{ color:#fff; font-size:15px; font-weight:600; opacity:.96;
    border-left:1px solid rgba(255,255,255,.4); padding-left:14px; }}
.bm-topbar-r {{ color:#cfe0f5; font-size:12.5px; text-align:right; line-height:1.4; }}
.bm-topbar-r b {{ color:#fff; }}

/* ---------- nav pills (st.button based) ---------- */
div[data-testid="stHorizontalBlock"] {{ align-items: stretch; }}
.stButton > button {{ border-radius: 9px; font-weight: 600; transition: all .15s ease; }}
.stButton > button[kind="secondary"] {{
    background:#fff; border:1px solid #dbe3ee; color:#334155;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color:{PRIMARY}; color:{PRIMARY}; background:{PRIMARY_SOFT};
}}
.stButton > button[kind="primary"] {{ box-shadow:0 2px 8px rgba(2,76,161,.25); }}

/* ---------- direction chips ---------- */
.dir-chip {{ font-size:12px; font-weight:600; padding:3px 10px; border-radius:20px; white-space:nowrap; display:inline-block; }}
.dir-up   {{ background:#e7f6ee; color:{SUCCESS}; }}
.dir-down {{ background:#fbe9e7; color:{DANGER}; }}
.dir-flat {{ background:#eef1f5; color:{NEUTRAL}; }}

/* ---------- cards / KPIs ---------- */
.bm-card {{ background:#fff; border:1px solid #e8edf3; border-radius:14px; padding:16px 18px; height:100%;
    box-shadow:0 1px 2px rgba(16,24,40,.04); transition:transform .18s ease, box-shadow .18s ease; }}
.bm-card:hover {{ transform:translateY(-2px); box-shadow:0 8px 22px rgba(2,76,161,.10); }}
.bm-kpi-top {{ display:flex; align-items:center; gap:8px; margin-bottom:6px; }}
.bm-kpi-icon {{ width:30px;height:30px;border-radius:8px;background:{PRIMARY_SOFT};color:{PRIMARY};
    display:flex;align-items:center;justify-content:center;font-size:17px; }}
.bm-kpi-label {{ color:{NEUTRAL}; font-size:13px; font-weight:500; }}
.bm-kpi-value {{ font-size:26px; font-weight:700; color:#0f172a; line-height:1.15; }}
.bm-kpi-sub {{ font-size:12.5px; color:{NEUTRAL}; margin-top:4px; }}
.bm-card h4 {{ margin:2px 0 4px 0; color:{PRIMARY_DARK}; font-size:16px; }}
.bm-card .bm-desc {{ color:{NEUTRAL}; font-size:13px; }}

/* section heading */
.bm-h {{ font-size:15px; font-weight:600; color:{PRIMARY_DARK}; margin:6px 0 6px 0;
    display:flex; align-items:center; gap:8px; }}

/* ---------- tables ---------- */
.bm-table {{ width:100%; border-collapse:collapse; font-size:13.5px; background:#fff;
    border:1px solid #e8edf3; border-radius:12px; overflow:hidden; }}
.bm-table thead th {{ background:{PRIMARY_SOFT}; color:{PRIMARY_DARK}; font-weight:600;
    padding:10px 12px; text-align:left; }}
.bm-table tbody td {{ padding:9px 12px; border-top:1px solid #eef2f7; color:#334155; }}
.bm-table tbody tr:hover {{ background:#f7faff; }}
.bm-r {{ text-align:right; font-variant-numeric:tabular-nums; }}
.bm-c {{ text-align:center; }}

/* tabs */
button[data-baseweb="tab"] {{ font-size:15px; font-weight:600; }}
div[data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid #e2e8f0; }}

/* links / footer */
.bm-link-btn a {{ display:inline-block; background:{ACCENT}; color:#fff!important; text-decoration:none;
    padding:11px 20px; border-radius:9px; font-weight:600; font-size:14px; box-shadow:0 2px 8px rgba(238,78,36,.25); }}
.bm-link-btn a:hover {{ filter:brightness(.95); }}
.bm-footnote {{ color:{NEUTRAL}; font-size:12px; margin-top:8px; }}
.bm-footer {{ margin-top:26px; padding-top:14px; border-top:1px solid #e2e8f0; color:{NEUTRAL};
    font-size:12px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
.bm-footer a {{ color:{PRIMARY}; text-decoration:none; }}
</style>
""", unsafe_allow_html=True)


_ICON_PATHS = {
    "home":       "<path d='M3 11l9-8 9 8'/><path d='M5 10v10h14V10'/>",
    "trending":   "<path d='M3 17l6-6 4 4 8-8'/><path d='M21 8V14M21 8h-6' stroke-linejoin='round'/>",
    "mic":        "<rect x='9' y='3' width='6' height='11' rx='3'/><path d='M5 11a7 7 0 0 0 14 0'/><path d='M12 18v3'/>",
    "gauge":      "<path d='M3 14a9 9 0 0 1 18 0'/><path d='M12 14l4-3'/>",
    "calculator": "<rect x='5' y='3' width='14' height='18' rx='2'/><path d='M8 7h8'/><path d='M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01M8 18h.01M12 18h.01M16 18h.01'/>",
    "rupee":      "<path d='M7 4h10M7 8h10M16 4c0 5-4 6-9 6 4 0 7 4 7 8'/>",
    "calendar":   "<rect x='4' y='5' width='16' height='16' rx='2'/><path d='M16 3v4M8 3v4M4 11h16'/>",
    "clock":      "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>",
    "factory":    "<path d='M3 21V9l6 4V9l6 4V9l6 4v8z'/>",
    "target":     "<circle cx='12' cy='12' r='8'/><circle cx='12' cy='12' r='3'/>",
}


def icon(name: str, size: int = 18) -> str:
    p = _ICON_PATHS.get(name, "")
    return (f"<svg viewBox='0 0 24 24' width='{size}' height='{size}' fill='none' "
            f"stroke='currentColor' stroke-width='2' stroke-linecap='round' "
            f"stroke-linejoin='round'>{p}</svg>")


def render_topbar(user: dict | None = None):
    right = ""
    if user:
        right = f"Signed in as <b>{user['name']}</b><br>{user['role']} access"
    st.markdown(
        f"<div class='bm-topbar'>"
        f"<div class='bm-topbar-l'>{_logo_html()}"
        f"<span class='bm-portal-title'>AI Labs &mdash; Steel Price Forecasting Model</span></div>"
        f"<div class='bm-topbar-r'>{right}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def direction_chip(direction: str) -> str:
    d = str(direction).strip().lower()
    if d in ("up", "rise", "rising"):
        return "<span class='dir-chip dir-up'>&#9650; Up</span>"
    if d in ("down", "fall", "falling"):
        return "<span class='dir-chip dir-down'>&#9660; Down</span>"
    return "<span class='dir-chip dir-flat'>&rarr; Flat</span>"


def arrow(direction: str) -> str:
    d = str(direction).strip().lower()
    if d == "up":
        return f"<span style='color:{SUCCESS};font-weight:700;'>&#9650;</span>"
    if d == "down":
        return f"<span style='color:{DANGER};font-weight:700;'>&#9660;</span>"
    return f"<span style='color:{NEUTRAL};font-weight:700;'>&rarr;</span>"


def kpi_card(label: str, value: str, sub: str = "", icon: str = "") -> str:
    icon_html = f"<span class='bm-kpi-icon'>{icon}</span>" if icon else ""
    sub_html = f"<div class='bm-kpi-sub'>{sub}</div>" if sub else ""
    return (f"<div class='bm-card'><div class='bm-kpi-top'>{icon_html}"
            f"<span class='bm-kpi-label'>{label}</span></div>"
            f"<div class='bm-kpi-value'>{value}</div>{sub_html}</div>")


def module_card(title: str, desc: str, icon: str = "") -> str:
    icon_html = f"<span class='bm-kpi-icon' style='width:34px;height:34px;font-size:19px;'>{icon}</span>" if icon else ""
    return (f"<div class='bm-card'><div class='bm-kpi-top'>{icon_html}"
            f"<h4 style='margin:0;'>{title}</h4></div>"
            f"<div class='bm-desc'>{desc}</div></div>")


def section_title(text: str, icon: str = ""):
    ic = f"{icon} " if icon else ""
    st.markdown(f"<div class='bm-h'>{ic}{text}</div>", unsafe_allow_html=True)


def footer():
    st.markdown(
        "<div class='bm-footer'>"
        "<span>AI-generated forecasts are indicative. Prototype build &mdash; data shown is a static snapshot.</span>"
        "<span>&copy; BigMint &middot; AI Labs &nbsp;|&nbsp; <a href='https://www.bigmint.co/' target='_blank'>bigmint.co</a></span>"
        "</div>",
        unsafe_allow_html=True,
    )
