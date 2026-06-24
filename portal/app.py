"""
BigMint - AI Labs : Steel Price Forecasting Model
Dedicated portal prototype (UI demo) for Adani.

Run:  streamlit run portal/app.py     (from the dashboard base folder)
"""
import os
import sys
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme
import auth
import data_loader as dl
from calculators import calc_import_price, calc_cost, calc_elasticity

BIGMINT_URL = "https://www.bigmint.co/"

st.set_page_config(
    page_title="BigMint - AI Labs | Steel Price Forecasting",
    layout="wide",
    initial_sidebar_state="collapsed",
)
theme.inject_css()


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
def login_screen():
    theme.render_topbar(None)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        with st.container(border=True):
            st.markdown("### Sign in")
            st.caption("Bigmint - AI Labs Steel Price Forecasting Model")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Sign in", use_container_width=True, type="primary"):
                profile = auth.authenticate(username, password)
                if profile:
                    st.session_state.user = profile
                    st.session_state.page = "Home"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            with st.expander("Demo credentials"):
                st.caption("Per-user demo access for this prototype:")
                for un, pw in auth.DEMO_CREDENTIALS:
                    st.write(f"`{un}`  /  `{pw}`")
    theme.footer()
    st.stop()


if "user" not in st.session_state:
    login_screen()

user = st.session_state.user
st.session_state.setdefault("page", "Home")
theme.render_topbar(user)


# ---------------------------------------------------------------------------
# TOP NAVIGATION (button-driven; page state is NOT a widget key)
# ---------------------------------------------------------------------------
NAV = [
    ("Home", "Home", "home"),
    ("Price Forecasting", "Forecasting", "trending_up"),
    ("Analyst Calls", "Analyst calls", "campaign"),
    ("Performance Dashboard", "Performance", "insights"),
    ("Calculators", "Calculators", "calculate"),
]


def top_nav():
    cols = st.columns([1, 1.35, 1.35, 1.3, 1.3, 1])
    for i, (name, label, mi) in enumerate(NAV):
        active = st.session_state.page == name
        if cols[i].button(f":material/{mi}: {label}", key=f"nav_{name}",
                          type="primary" if active else "secondary", use_container_width=True):
            st.session_state.page = name
            st.rerun()
    if cols[-1].button(":material/logout: Log out", key="nav_logout", use_container_width=True):
        auth.logout()


top_nav()
st.write("")


# ---------------------------------------------------------------------------
# CHART HELPERS
# ---------------------------------------------------------------------------
def _style_fig(fig, height=430, money=True):
    """Shared clean styling + a snap-to-point 'ball pointer' hover for all charts."""
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=30, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12.5)),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        hovermode="closest", dragmode=False, hoverdistance=80,
        font=dict(family="sans-serif", size=12, color="#334155"),
    )
    if money:
        fig.update_yaxes(tickprefix="Rs.", tickformat=",.0f")
    fig.update_yaxes(gridcolor="#eef2f7", zeroline=False, showline=False, automargin=True)
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)", showline=True, linecolor="#e2e8f0")
    return fig


def _dt(t):
    return t.to_pydatetime() if hasattr(t, "to_pydatetime") else t


def _spot_trace(dates, vals):
    import plotly.graph_objects as go
    return go.Scatter(
        x=[_dt(d) for d in dates], y=list(vals), name="Spot (actual)", mode="lines",
        line=dict(color=theme.SPOT_LINE, width=2.4, shape="spline", smoothing=0.4),
        hovertemplate="%{x|%d-%b-%y}<br><b>Spot Price: Rs.%{y:,.2f}</b><extra></extra>",
        hoverlabel=dict(bgcolor="white", bordercolor="#cfe0f5", font=dict(color=theme.SPOT_DARK)))


# custom Plotly.js layer: a halo+core "highlighter" ball that follows the hovered point
_HL_TEMPLATE = """
<div id="__DIV__" style="width:100%;height:__H__px;"></div>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script>
const fig = __FIGJSON__;
const gd = document.getElementById("__DIV__");
Plotly.newPlot(gd, fig.data, fig.layout, {displayModeBar:false, responsive:true});
function hexA(c,a){ if(!c) return 'rgba(225,43,32,'+a+')'; if(c[0]!=='#') return c; var h=c.slice(1); if(h.length===3){h=h.split('').map(function(x){return x+x;}).join('');} var n=parseInt(h,16); return 'rgba('+((n>>16)&255)+','+((n>>8)&255)+','+(n&255)+','+a+')'; }
gd.on('plotly_hover', function(d){ var p=d.points[0]; var col=(p.fullData.line&&p.fullData.line.color)||'#E12B20'; Plotly.restyle(gd, {x:[[p.x],[p.x]], y:[[p.y],[p.y]], 'marker.color':[hexA(col,0.20), col]}, [__HALO__,__CORE__]); });
gd.on('plotly_unhover', function(){ Plotly.restyle(gd, {x:[[],[]], y:[[],[]]}, [__HALO__,__CORE__]); });
</script>
"""


def _render_with_highlighter(fig, height=430, dom_id="chart"):
    """Render a Plotly figure via a custom JS layer that adds a hover-following ball."""
    import plotly.graph_objects as go
    fig.update_layout(autosize=True)
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", hoverinfo="skip", showlegend=False,
                             marker=dict(size=20, color="rgba(225,43,32,0.18)")))
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", hoverinfo="skip", showlegend=False,
                             marker=dict(size=9, color=theme.FORECAST_LINE, line=dict(width=2, color="#ffffff"))))
    halo_idx, core_idx = len(fig.data) - 2, len(fig.data) - 1
    html = (_HL_TEMPLATE.replace("__DIV__", dom_id).replace("__H__", str(height))
            .replace("__FIGJSON__", fig.to_json())
            .replace("__HALO__", str(halo_idx)).replace("__CORE__", str(core_idx)))
    components.html(html, height=height + 12)


def forecast_chart(acc, fwd):
    """Light-blue actual spot + bold red dashed model forecast (history fit + 12-week ahead)."""
    hist = acc.dropna(subset=["Actual"]).tail(26).copy()
    if hist.empty:
        st.info("No historical spot series available for this product.")
        return
    try:
        import plotly.graph_objects as go
        fc_dates = list(hist["Date"]) + list(fwd["Date"])
        fc_vals = list(hist["Forecast"]) + list(fwd["Forecast"])
        fig = go.Figure()
        fig.add_trace(_spot_trace(hist["Date"], hist["Actual"]))
        fig.add_trace(go.Scatter(
            x=[_dt(d) for d in fc_dates], y=fc_vals, name="Forecast", mode="lines+markers",
            line=dict(color=theme.FORECAST_LINE, width=2.8, dash="dash", shape="spline", smoothing=0.4),
            marker=dict(size=5, color=theme.FORECAST_LINE, line=dict(width=4, color=theme.FORECAST_HALO)),
            hovertemplate="%{x|%d-%b-%y}<br><b>Forecast Price: Rs.%{y:,.2f}</b><extra></extra>",
            hoverlabel=dict(bgcolor="white", bordercolor="#f3c2bd", font=dict(color=theme.FORECAST_LINE))))
        _render_with_highlighter(_style_fig(fig), height=430, dom_id="fc_chart")
    except Exception:
        h = hist.set_index("Date")[["Actual", "Forecast"]]
        f = fwd.set_index("Date")[["Forecast"]].rename(columns={"Forecast": "Forecast (12-wk)"})
        st.line_chart(pd.concat([h, f], axis=1))


def perf_chart(view):
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(_spot_trace(view["Date"], view["Actual"]))
        fig.add_trace(go.Scatter(
            x=[_dt(d) for d in view["Date"]], y=list(view["Forecast"]), name="Forecast",
            mode="lines+markers", line=dict(color=theme.FORECAST_LINE, width=2.6, dash="dash"),
            marker=dict(size=6, color=theme.FORECAST_LINE, line=dict(width=4, color=theme.FORECAST_HALO)),
            hovertemplate="%{x|%d-%b-%y}<br><b>Forecast Price: Rs.%{y:,.2f}</b><extra></extra>",
            hoverlabel=dict(bgcolor="white", bordercolor="#f3c2bd", font=dict(color=theme.FORECAST_LINE))))
        _render_with_highlighter(_style_fig(fig, height=320), height=320, dom_id="perf_chart")
    except Exception:
        st.line_chart(view.set_index("Date")[["Actual", "Forecast"]])


def delta_bar(view):
    try:
        import plotly.graph_objects as go
        colors = [theme.DANGER if d > 0 else theme.SUCCESS for d in view["Delta"]]
        fig = go.Figure(go.Bar(x=view["Date"], y=view["Delta"], marker_color=colors,
                               hovertemplate="Rs.%{y:,.0f}<extra>Forecast - Spot</extra>"))
        fig.update_layout(height=200, margin=dict(l=8, r=8, t=8, b=8),
                          plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", dragmode=False,
                          hovermode="x unified", bargap=0.35,
                          hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0"),
                          font=dict(size=11, color="#334155"))
        fig.update_yaxes(tickprefix="Rs.", tickformat=",.0f", gridcolor="#eef2f7", zeroline=True, zerolinecolor="#cbd5e1")
        fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        st.bar_chart(view.set_index("Date")[["Delta"]])


# ---------------------------------------------------------------------------
# PAGE: HOME
# ---------------------------------------------------------------------------
def page_home():
    st.markdown("## Bigmint - AI Labs Steel Price Forecasting Model")
    st.markdown(f"Welcome, **{user['name']}**. Six steel products, 12-week Ensemble forecasts and week-wise accuracy.")
    st.write("")

    summary = dl.load_summary()
    last_dates = pd.to_datetime(summary["Last actual date"], errors="coerce").dropna()
    last_update = last_dates.max().strftime("%d %b %Y") if not last_dates.empty else "-"
    mapas = []
    for _, meta in dl.STEEL_PRODUCTS.items():
        acc = dl.load_accuracy("6-week", meta["acc"]).dropna(subset=["Actual", "Forecast"]).tail(16)
        k = dl.accuracy_kpis(acc)
        if k["mapa"] is not None:
            mapas.append(k["mapa"])
    avg_mapa = sum(mapas) / len(mapas) if mapas else None

    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(theme.kpi_card("Steel products", "6", "tracked weekly", theme.icon("factory")), unsafe_allow_html=True)
    s2.markdown(theme.kpi_card("Forecast horizon", "12 wk", "Ensemble Wgt-Mean", theme.icon("trending")), unsafe_allow_html=True)
    s3.markdown(theme.kpi_card("Avg absolute accuracy", f"{avg_mapa:.1f}%" if avg_mapa else "-", "MAPA, last 16 wk", theme.icon("target")), unsafe_allow_html=True)
    s4.markdown(theme.kpi_card("Last actual", last_update, "most recent assessment", theme.icon("calendar")), unsafe_allow_html=True)

    st.write("")
    theme.section_title("Modules", theme.icon("home"))
    c1, c2, c3 = st.columns(3)
    cards = [
        (c1, "Price forecasting", "Spot vs 12-week forecast for six steel products, plus the raw-material feed.", theme.icon("trending"), "Price Forecasting"),
        (c2, "Analyst calls", "Monthly market-outlook calls, key insights and downloadable decks.", theme.icon("mic"), "Analyst Calls"),
        (c3, "Performance", "Week-wise accuracy: spot, forecast, delta and direction.", theme.icon("gauge"), "Performance Dashboard"),
    ]
    for col, title, desc, ic, target in cards:
        with col:
            st.markdown(theme.module_card(title, desc, ic), unsafe_allow_html=True)
            if st.button(f"Open {title.split()[0].lower()}", key=f"home_{target}", use_container_width=True):
                st.session_state.page = target
                st.rerun()

    st.write("")
    cc1, cc2 = st.columns([2, 1])
    with cc1:
        st.markdown(theme.module_card("Calculators",
                    "Import vs landed-cost, production cost & margin, and price-elasticity tools.",
                    theme.icon("calculator")), unsafe_allow_html=True)
    with cc2:
        st.write("")
        if st.button("Open calculators", key="home_calc", use_container_width=True, type="primary"):
            st.session_state.page = "Calculators"
            st.rerun()
    theme.footer()


# ---------------------------------------------------------------------------
# PAGE: PRICE FORECASTING
# ---------------------------------------------------------------------------
def page_forecasting():
    st.markdown("## Price forecasting")
    tab_steel, tab_raw = st.tabs(["Steel price forecast", "Raw-material price forecast"])

    with tab_steel:
        product = st.segmented_control("Product", list(dl.STEEL_PRODUCTS.keys()),
                                       default="HRC", key="fc_prod", label_visibility="collapsed")
        product = product or "HRC"
        meta = dl.STEEL_PRODUCTS[product]
        summary = dl.load_summary()
        row = dl.summary_row(summary, meta["ff"])
        fwd = dl.load_forward(meta["ff"])

        if row:
            last_actual = row.get("Last actual (Rs./ton)", row.get("Last actual (₹/ton)"))
            last_date = pd.to_datetime(row.get("Last actual date"), errors="coerce")
            ld = last_date.strftime("%d %b %Y") if pd.notna(last_date) else "-"
            nextwk = row.get("Next-wk forecast")
            p12 = row.get("+12wk forecast")
            top3 = row.get("Top-3 models (direction)", "")

            k1, k2, k3 = st.columns(3)
            k1.markdown(theme.kpi_card("Last actual spot", f"Rs.{last_actual:,.0f}", ld, theme.icon("rupee")), unsafe_allow_html=True)
            k2.markdown(theme.kpi_card("Next-week forecast", f"Rs.{nextwk:,.0f}", theme.direction_chip(row.get("Next-wk dir", "")), theme.icon("clock")), unsafe_allow_html=True)
            k3.markdown(theme.kpi_card("+12-week forecast", f"Rs.{p12:,.0f}", theme.direction_chip(row.get("+12wk dir", "")), theme.icon("trending")), unsafe_allow_html=True)
            st.markdown(f"<div class='bm-footnote'>Model agreement (top-3 by direction): <b>{top3}</b></div>", unsafe_allow_html=True)
        else:
            last_actual, last_date = None, None

        st.write("")
        theme.section_title("Spot vs forecast (12-week ahead)", theme.icon("trending"))
        acc_hist = dl.load_accuracy("16-week", meta["acc"])
        forecast_chart(acc_hist, fwd)
        st.markdown("<div class='bm-footnote'>Light blue = actual spot. Red dashed = model forecast "
                    "(historical fit + 12-week ahead). Hover any point for its price.</div>",
                    unsafe_allow_html=True)

        theme.section_title("12-week forecast path", theme.icon("calendar"))
        rows_html = "".join(
            f"<tr><td>W{int(r.Week)}</td><td>{r.Date:%d %b %Y}</td>"
            f"<td class='bm-r'>Rs.{r.Forecast:,.0f}</td>"
            f"<td class='bm-r'>{'+' if r.Delta>=0 else ''}{r.Delta:,.0f}</td>"
            f"<td class='bm-c'>{theme.direction_chip(r.Direction)}</td></tr>"
            for r in fwd.itertuples()
        )
        st.markdown(
            "<table class='bm-table'><thead><tr><th>Week</th><th>Date</th>"
            "<th class='bm-r'>Forecast (Rs./t)</th><th class='bm-r'>&Delta; vs last actual</th>"
            "<th class='bm-c'>Direction</th></tr></thead>"
            f"<tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='bm-footnote'>Headline line = Ensemble (Weighted Mean). "
                    "See the <b>Calculators</b> tab for the Import vs Landed-Cost tool.</div>", unsafe_allow_html=True)

    with tab_raw:
        theme.section_title("Raw-material price forecast", theme.icon("trending"))
        st.write("Raw-material forecasts are published on the BigMint subscriber platform. "
                 "Products currently covered in the model include:")
        summary = dl.load_summary()
        raw = summary[~summary["Product"].astype(str).str.strip().isin(dl.STEEL_FF_LABELS)]
        show_cols = [c for c in ["Product", "Last actual date", "Next-wk dir", "+12wk dir"] if c in raw.columns]
        st.dataframe(raw[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
        st.write("")
        st.markdown(f"<div class='bm-link-btn'><a href='{BIGMINT_URL}' target='_blank'>"
                    "Open BigMint raw-material forecasts &nbsp;&rarr;</a></div>", unsafe_allow_html=True)
    theme.footer()


# ---------------------------------------------------------------------------
# PAGE: ANALYST CALLS  (placeholder)
# ---------------------------------------------------------------------------
def page_analyst():
    st.markdown("## Analyst calls / meets")
    st.info("Placeholder module - monthly call summaries and decks will be published here. "
            "Content and uploads to be wired in a later phase.", icon=":material/info:")
    placeholders = [
        ("June 2026", "Market outlook call", "Flat-to-soft HRC into Q3; raw-material support easing as iron-ore and coking-coal cool."),
        ("May 2026", "Market outlook call", "Rebar firm on monsoon-led restocking; scrap stable. Key insights and downloadable deck."),
        ("April 2026", "Market outlook call", "Q1 review and forward view across flats and longs."),
    ]
    for month, title, summary in placeholders:
        with st.container(border=True):
            top = st.columns([5, 1])
            top[0].markdown(f"**{month} &mdash; {title}**", unsafe_allow_html=True)
            top[1].markdown("<div style='text-align:right;color:#64748b;font-size:12px;'>PPT / PDF</div>", unsafe_allow_html=True)
            st.write(summary)
            b1, b2, _ = st.columns([1, 1, 4])
            b1.button("Download PDF", key=f"pdf_{month}", disabled=True, icon=":material/picture_as_pdf:")
            b2.button("Download PPT", key=f"ppt_{month}", disabled=True, icon=":material/slideshow:")
    if user["role"] == "Admin":
        st.caption("Admin: upload workflow for new calls will appear here in a later phase.")
    theme.footer()


# ---------------------------------------------------------------------------
# PAGE: PERFORMANCE DASHBOARD
# ---------------------------------------------------------------------------
def page_performance():
    st.markdown("## Performance dashboard")
    c1, c2 = st.columns([3, 1])
    with c1:
        product = st.segmented_control("Product", list(dl.STEEL_PRODUCTS.keys()),
                                       default="HRC", key="perf_prod", label_visibility="collapsed")
    with c2:
        window = st.segmented_control("Window", ["6-week", "16-week"], default="6-week",
                                      key="perf_win", label_visibility="collapsed")
    product = product or "HRC"
    window = window or "6-week"
    meta = dl.STEEL_PRODUCTS[product]

    df = dl.load_accuracy(window, meta["acc"])
    if df.empty:
        st.warning("No accuracy data found for this product.")
        theme.footer()
        return
    view = df.dropna(subset=["Actual", "Forecast"]).tail(16).reset_index(drop=True)
    kpis = dl.accuracy_kpis(view)

    k1, k2, k3 = st.columns(3)
    k1.markdown(theme.kpi_card("Absolute accuracy (MAPA)",
                f"{kpis['mapa']:.1f}%" if kpis['mapa'] is not None else "-", "100 - mean abs % error", theme.icon("target")), unsafe_allow_html=True)
    k2.markdown(theme.kpi_card("Directional accuracy",
                f"{kpis['dir_acc']:.0f}%" if kpis['dir_acc'] is not None else "-", "correct up/down calls", theme.icon("gauge")), unsafe_allow_html=True)
    k3.markdown(theme.kpi_card("Average delta",
                f"{kpis['avg_delta']:+.1f}%" if kpis['avg_delta'] is not None else "-", "forecast vs spot", theme.icon("trending")), unsafe_allow_html=True)

    st.write("")
    theme.section_title("Actual vs forecast", theme.icon("trending"))
    perf_chart(view)
    theme.section_title("Weekly delta (forecast - spot)", theme.icon("insights") if False else theme.icon("gauge"))
    delta_bar(view)

    theme.section_title("Week-wise detail", theme.icon("calendar"))
    rows_html = ""
    for i, r in enumerate(view.itertuples(), start=1):
        rows_html += (
            f"<tr><td>W{i}</td><td>{r.Date:%d %b %Y}</td>"
            f"<td class='bm-r'>Rs.{r.Actual:,.0f}</td>"
            f"<td class='bm-r'>Rs.{r.Forecast:,.0f}</td>"
            f"<td class='bm-r'>{'+' if r.Delta>=0 else ''}{r.Delta:,.0f} ({r.DeltaPct:+.1f}%)</td>"
            f"<td class='bm-c'>{theme.direction_chip(r.PredDir)}</td></tr>"
        )
    st.markdown(
        "<table class='bm-table'><thead><tr><th>Week</th><th>Date</th>"
        "<th class='bm-r'>Spot</th><th class='bm-r'>Forecast</th>"
        "<th class='bm-r'>Delta</th><th class='bm-c'>Direction</th></tr></thead>"
        f"<tbody>{rows_html}</tbody></table>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='bm-footnote'>Delta = Forecast - Spot. Direction = model's predicted move vs the prior week's spot.</div>",
                unsafe_allow_html=True)
    theme.footer()


# ---------------------------------------------------------------------------
# PAGE: CALCULATORS
# ---------------------------------------------------------------------------
def page_calculators():
    st.markdown("## Calculators")
    t1, t2, t3 = st.tabs(["Import vs Landed Cost (HRC)", "Production Cost & Margin", "Price Elasticity (HRC)"])
    with t1:
        calc_import_price.render()
    with t2:
        calc_cost.render()
    with t3:
        calc_elasticity.render()
    theme.footer()


# ---------------------------------------------------------------------------
# DISPATCH
# ---------------------------------------------------------------------------
PAGES = {
    "Home": page_home,
    "Price Forecasting": page_forecasting,
    "Analyst Calls": page_analyst,
    "Performance Dashboard": page_performance,
    "Calculators": page_calculators,
}
PAGES.get(st.session_state.page, page_home)()
