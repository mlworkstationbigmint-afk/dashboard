# BigMint – AI Labs Steel Price Forecasting Model — Handoff

Standalone **Streamlit UI prototype** for Adani. Data is a static, cached snapshot of the
dashboard's existing forecast/accuracy files — no live backend.

## Run
```bash
# from the dashboard BASE folder (so .streamlit/config.toml + relative paths resolve)
cd C:\Users\Pc\Documents\dashboard
conda activate neuralforecast
streamlit run portal/app.py
```
Env = conda **`neuralforecast`**. Needs: streamlit, plotly, fpdf2, scikit-learn, openpyxl, pandas, numpy
(kaleido only for static PNG export). Console needs `PYTHONUTF8=1` for ₹ glyphs.

## Demo logins (per-user, SHA-256 hashed in auth.py — demo-grade only)
| User | Password | Role |
|------|----------|------|
| adani | Adani@2026 | Adani |
| admin | Admin@2026 | Admin |
| analyst | Analyst@2026 | Analyst |

## Locked decisions
- Streamlit UI-only prototype; per-user login; **12-week** horizon.
- Headline forecast line = **Ensemble (Weighted Mean)**.
- Title: "Steel Price Forecasting Model". Co-branding lives **only in the topbar** as logos (BigMint logo `|` Adani chip — separator is a pipe, not `×`); the "BigMint × Adani" text was removed everywhere else. Brand name is **BigMint** (never "Bigmint").
- Static snapshot data (no live connection).

## Six steel products (fixed)
HRC · HR Plate · Rebar BF Mumbai · Rebar IF Mumbai · Rebar IF Raipur · Structure (IF Raipur)

## File map  (everything under `dashboard/portal/`)
| File | What it does |
|------|--------------|
| `app.py` | Entry: page config, auth gate, top nav, 5 pages, chart helpers |
| `theme.py` | Brand palette, CSS, icons, topbar, KPI/card/table helpers |
| `auth.py` | Demo users + `authenticate()` / `logout()` |
| `data_loader.py` | Cached readers for forecast_forward + accuracy tables |
| `calculators/calc_import_price.py` | Import vs Landed Cost (HRC) |
| `calculators/calc_cost.py` | Production Cost & Margin |
| `calculators/calc_elasticity.py` | Price Elasticity (HRC, Ridge model) |
| `calculators/HRC - Copy.csv` | Calculators' own dataset (last date 25-Jan-26) |
| `assets/bigmint_logo.png` | Top-bar BigMint logo (wordmark fallback if absent) |
| `assets/adani_logo.png` | Co-brand Adani logo, white chip in topbar (auto-trimmed; gradient-text 'adani' fallback if absent) |
| `assets/adani_logo_orig.png` | Untrimmed original Adani logo (backup; safe to delete) |
| `../.streamlit/config.toml` | Streamlit theme (primaryColor #EE4E24 — orange accent for buttons/tabs; **untracked in git**) |

## Modules
- **Home** — overview stats + module cards.
- **Price forecasting** — Steel only: product selector + KPI strip, then a **Graphical view / Tabular view** tab pair (Graphical = spot-vs-forecast chart; Tabular = one continuous *Actual vs Forecast* table, history flowing into the 12-wk-ahead forecast), then a **Forecast rationale** section (placeholder, per-product via `RATIONALES`). (Raw-material tab removed earlier.)
- **Analyst calls** — PLACEHOLDER cards (no real content yet).
- **Performance dashboard** — product selector only (window toggle removed); reads **all rows** of `Accuracy_Table_6`. MAPA / directional / avg-delta KPIs, actual-vs-forecast chart + weekly-delta (Rs.) bars + **weekly accuracy % line** + **weekly directional-accuracy bars** + week-wise table.
- **Calculators** — 3 tools in tabs.

## "Edit X → go here"
- Brand colours/logo → `theme.py` palette + `.streamlit/config.toml`; co-brand logos → `theme.py` `_logo_html` / `_adani_logo_html` + `render_topbar`
- Tab + segmented-selector accent (orange) → `theme.py` `inject_css()` tab/segmented CSS block (overrides primaryColor for those elements only)
- Nav items / page wiring → `app.py` `NAV` list + `PAGES` dict
- Home module cards (clickable) → `app.py` `page_home()` `modules` list + `theme.py` `.st-key-homemod_*` CSS
- Log out button (header top-right, primary) → `app.py` header `st.columns([6,1])` block (key `logout_top`)
- Chart look / lines / hover ball → `app.py` `_style_fig`, `_spot_trace`, `forecast_chart`, `perf_chart`, `delta_bar`, `accuracy_chart`, `directional_accuracy_bar`, `_render_with_highlighter`; colours in `theme.py` (`SPOT_LINE`, `FORECAST_LINE`, `FORECAST_HALO`)
- Products → `data_loader.py` `STEEL_PRODUCTS`
- Users → `auth.py` `USERS` + `DEMO_CREDENTIALS`
- Analyst content → `app.py` `page_analyst()` placeholders
- Forecast rationale text → `app.py` `RATIONALES` dict (add a key per product name; `_default` is the placeholder shown until then)
- Forecasting Graphical/Tabular tabs → `app.py` `page_forecasting()` `st.tabs([...])` block
- History window (chart + historical table, kept in sync) → `app.py` `HIST_WEEKS` constant (currently 26)
- Data parsing → `data_loader.py`
- Direction Up/Down/Flat + flat threshold (500) → `data_loader.py` `direction_flag()` / `FLAT_THRESHOLD`

## Data sources (read once, cached)
- `accuracy_tables/forecast_forward.xlsx` — `Summary` (per product: last actual, next-wk & +12wk forecast + dir; a `Top-3 models (direction)` column exists but is **no longer displayed** — see changelog) and per-product sheets (12-wk path: Date, Week, Forecast, Δ, Direction).
- `accuracy_tables/Accuracy_Table_6.xlsx` / `_16.xlsx` — week-wise Actual/Forecast (sheet `Ensemble_WgtMean`); `_6`/`_16` = 6/16-wk eval window. Stored MAE/MAPA/Delta/Directional cols are sparse → derive Delta/Direction from Actual/Forecast (Up/Down/Flat via `direction_flag`, ±500 Rs./ton dead-band ⇒ Flat).

## Gotchas (don't re-break these)
- **Nav**: current page = `st.session_state.page` (a plain key, NOT a widget key). Nav is `st.button`s (active = `type="primary"`). NEVER bind a widget `key` to the nav and then mutate it → raises "cannot be modified after the widget is instantiated". **Log out** is a separate primary `st.button` (key `logout_top`) in the header columns, not in the nav row.
- **Charts**: rendered via a custom `components.html` Plotly.js layer (CDN `plotly-2.35.2`) to get the **hover-following highlighter ball** (Plotly can't enlarge the hovered marker natively). `_render_with_highlighter()` adds halo+core marker traces moved on `plotly_hover`. → **needs internet (CDN)**; for offline, bundle plotly.js locally.
- Chart hover = `hovermode="closest"` (unified looked janky). Pass plotly **layout-scalar dates as python datetime** via `_dt()` (pandas Timestamp breaks JSON serialization); `fig.to_json()` handles trace dates.
- Forecast chart = light-blue actual + **red dashed** forecast (history fit + 12-wk) with red ball+pink halo. Colours: `SPOT_LINE #5E92D6`, `FORECAST_LINE #E12B20`.
- **Calculators**: each exposes `render()`; their CSS had `div.stButton>button` overrides removed so they don't clobber nav buttons; PDF export uses `_pdf_bytes()` (fpdf/fpdf2-safe); a malformed `header{...}` CSS block was fixed.
- Logo blue is `#024CA1` (= theme PRIMARY) so it blends into the bar.
- **Accent = orange**: `primaryColor` is now `#EE4E24` (ACCENT orange) in config.toml — it natively drives **primary buttons (Sign in / Log out / active nav) + tab highlights + segmented selected state** orange. The **brand topbar stays blue** because it uses the `PRIMARY` (#024CA1) constant in `theme.py` CSS, *not* `primaryColor`. **Tabs** are now styled as **segmented pills** (not underline): the default `tab-highlight`/`tab-border` are hidden and the active tab is a white pill with orange text/`box-shadow` (`button[data-baseweb="tab"][aria-selected="true"]`); the grey track is `div[data-baseweb="tab-list"]`. The segmented selector (Product) still gets orange via `stBaseButton-segmented_controlActive`. If tabs look wrong after a Streamlit upgrade, re-check those `data-baseweb="tab*"` selectors. (Was previously blue buttons + CSS-only orange underline-tabs; accent flipped + tabs re-styled 2026-06-26.)

## Changelog (prototype iterations)
### 2026-06-26
- **Forecasting Tabular view → one continuous Actual-vs-Forecast table** — single table with cols **Date | Actual | Forecast | Δ (Actual − Forecast) | Direction**, history flowing straight into the 12-week-ahead forecast:
  - **History rows** (top): Actual + Forecast + Δ filled; **Direction left blank**. Window = shared `HIST_WEEKS` constant (= 26), the *same window as the chart* — `forecast_chart` and the table both `tail(HIST_WEEKS)` so the table mirrors the graph (verified: equal row counts for all 6 products). `acc_hist = load_accuracy("16-week", …)`, filtered `dropna(["Actual"])` to match the chart exactly.
  - **Forecast rows** (bottom, from `fwd`): **Actual + Δ blank**, Forecast + Direction filled; tinted with `.bm-fc-row` (faint orange band, mirrors the chart's shaded forecast region). **Week column** and the old **"Δ vs last actual" column** are gone.
  - `acc_hist` load hoisted above the tabs (was inside the Graphical tab) so both tabs share it. Footnote notes the top-N history window + that shaded rows are the forecast. → `app.py` `page_forecasting()`, `theme.py` (`.bm-fc-row`).
- **Forecasting chart + tabs restyle (modern look, bigger, no edge-clipping)** —
  - *Tabs → segmented pills*: `theme.py` tab CSS rewritten from underline-tabs to a **pill/segmented control** on a grey track (`div[data-baseweb="tab-list"]` = inline-flex rounded `#e9edf4` bg; active tab = white pill + orange text + shadow; `tab-highlight`/`tab-border` hidden). Applies to **all** `st.tabs` (forecasting + calculators).
  - *Chart bigger + same footprint as table*: `forecast_chart` height 430 → **500**; forecast-path table uses new **`.bm-table-lg`** variant (15px, padding 14/13px, uppercase header) so the two tabs feel equal-sized.
  - *"Cut from the sides" fix*: `_HL_TEMPLATE` now resets iframe `html,body` margins and adds a **`ResizeObserver` + window-resize** handler calling `Plotly.Plots.resize(gd)` (re-fits on tab-switch / window resize); `_style_fig` margins widened (l14/r22/t38/b14) + x-axis `automargin`; edge markers/halo set `cliponaxis=False` so they don't clip at the plot border.
  - *Modern styling*: actual-spot line now has a soft blue **area fill** (`_spot_trace(..., fill=True)`, `fill="tozeroy"` over a padded y-range so it reads as a band, not a block to zero); a dotted **divider** (`add_vline`) + faint orange **shaded band** (`add_vrect`) + "12-wk ahead" annotation mark where the forward forecast begins. Verified `fig.to_json()` still serializes (datetimes via `_dt()`). → `app.py` (`_style_fig`, `_spot_trace`, `_HL_TEMPLATE`, `_render_with_highlighter`, `forecast_chart`), `theme.py`.
- **Price forecasting — Graphical/Tabular tabs + Rationale section** — the spot-vs-forecast **chart** and the **12-week forecast-path table** are now split into two `st.tabs(["Graphical view", "Tabular view"])` (Graphical is the default/first tab; flip the order in `page_forecasting()` if Tabular should lead). Below the tabs, a new **"Forecast rationale"** section renders per-product commentary from a module-level `RATIONALES` dict (currently a single `"_default"` **placeholder** with Demand / Supply & cost / Trade & sentiment / Net-view stub bullets) — real analyst text to be supplied later by adding entries keyed by product name. New `notes` icon added to `theme.py` `_ICON_PATHS` for the section heading. → `app.py` `page_forecasting()` + `RATIONALES`, `theme.py`.
- **MAPA now averaged over the full series (82 wk), not last 16** — the **Home** overview KPI ("Avg absolute accuracy") was computing MAPA on `.tail(16)` of each product and labelled "MAPA, last 16 wk". Removed the `.tail(16)` cap so it averages the full series; label is now dynamic `f"MAPA, {n_weeks}-wk avg"` (currently 82). The **Performance** page already read all rows (no cap) — added the week count to its MAPA sublabel (`f"100 - mean abs % error · {len(view)} wk"`). Week count is computed from the data (`Accuracy_Table_6` = 82 rows/product), not hardcoded, so it self-updates. → `app.py` `page_home()` + `page_performance()`.
- **Accent flipped to orange** — `primaryColor` in `.streamlit/config.toml` changed `#024CA1` (blue) → `#EE4E24` (orange ACCENT) so **primary buttons (Sign in / Log out / active nav) and tab highlights** all render orange natively, not just via the version-fragile CSS overrides. The brand **topbar stays blue** (uses the `PRIMARY` constant in `theme.py`, independent of `primaryColor`). See updated "Accent = orange" gotcha. NB: `.streamlit/config.toml` is **untracked in git** — this change lives only in the working tree.
- **Footer co-brand separator `|` → `-`** — footer now reads "© BigMint - Adani · AI Labs" (the `&nbsp;|&nbsp;` before the bigmint.co link is a separate list separator, left as-is). → `theme.py` `footer()`.
- **Home — Performance card description lengthened** — was a 2-line blurb ("Week-wise accuracy: spot, forecast, delta and direction.") which left its "Open →" CTA higher than the other three 3-line cards. Expanded to "Week-wise accuracy: spot vs forecast, weekly delta, MAPA and directional hit-rate." so it wraps to ~3 lines and the CTAs align across the row. → `app.py` `page_home()` `modules` list.
- **Co-brand text removed; topbar separator `×` → `|`** — the "BigMint × Adani" co-brand string now appears **only in the topbar** (as the two logos). Topbar divider between BigMint logo and the Adani chip changed from `&times;` to a pipe `|` (`render_topbar()` in `theme.py`; `.bm-cobrand-x` styling unchanged — class name kept as the CSS hook). Removed the co-brand text from: browser tab `page_title` → "Steel Price Forecasting Model", login caption → "Steel Price Forecasting Model", Home header → "## Steel Price Forecasting Model" (all `app.py`). **Footer keeps the co-branding** (separator later finalized to `-` — see the footer entry above): "© BigMint - Adani · AI Labs" (`theme.py` `footer()`). → `theme.py`, `app.py`.

### 2026-06-25
- **Analyst Calls** — added a third **Download Video** button (`:material/videocam:`) per call card beside PDF/PPT; row layout now `st.columns([1,1,1,3])`, corner label "PDF / PPT / Video". All three remain **disabled placeholders** (no real files wired yet). → `app.py` `page_analyst()`.
- **Performance dashboard** — added two full-width charts below the Rs. delta bar (both read the same `view` frame; wired in `page_performance()` after `delta_bar`):
  - **Weekly forecast accuracy (%)** — `accuracy_chart()`: green spline line of `100 − |DeltaPct|`, %-suffixed y-axis, hover-ball.
  - **Weekly directional accuracy** — `directional_accuracy_bar()`: diverging bars per week, green "up" = correct directional call, red "down" = wrong (first week neutral — no prior reference, matching the KPI's `iloc[1:]` logic); hover shows predicted vs actual.
- **Direction flags (Up/Down/Flat), flat threshold = 500** — new `direction_flag(delta, thr=500)` + `FLAT_THRESHOLD = 500.0` in `data_loader.py`; a **±500 Rs./ton dead-band ⇒ Flat**. Applied in: `load_accuracy` `PredDir`/`ActualDir` (change vs prior week's spot), `load_forward` `Direction` (derived from `Delta`, replacing the value read from the file), and the forecasting-page **Next-wk / +12-wk KPI chips** (recomputed in `page_forecasting()` from `forecast − last actual`). Directional-accuracy KPI sublabel → "correct up/down/flat calls".
- **Log out button** — moved out of the nav row into the **top-right of the header** and restyled `type="primary"` to match the Sign-in button. Header is now `st.columns([6,1], vertical_alignment="center")`: brand bar (hcol1) + Log out (hcol2, key `logout_top`). Nav row trimmed to the 5 page buttons (old `nav_logout` removed). → `app.py` header block + `top_nav()`.
- **Tabs + segmented-selector accent → orange** — targeted CSS in `theme.py` `inject_css()` so the **active tab** (label + underline) and **active segmented selector** (Product/Window) render in `ACCENT` (#EE4E24); brand bar, primary buttons and `primaryColor` (#024CA1) stay blue. Selectors (verified vs Streamlit 1.58 bundle): `button[data-baseweb="tab"][aria-selected="true"]`, `div[data-baseweb="tab-highlight"]`, `button[data-testid="stBaseButton-segmented_controlActive"]` (+ its `p`). NB: these were **not** orange before — fresh accent, not a revert.
- **Performance dashboard — data source simplified** — removed the 6/16-week window toggle; the section now always reads **`Accuracy_Table_6`** and shows **all rows** (dropped the `.tail(16)` cap), so KPIs/charts/table span the full series. Direction column still uses the ±500 up/down/flat `direction_flag`; Actual/Forecast come straight from the sheet. `Accuracy_Table_16` is now unused by the app (file + `ACC_PATHS["16-week"]` left in place, just not referenced). → `app.py` `page_performance()`.
- **Performance week-wise table — Direction column removed** — dropped the Direction chip column (header, per-row cell, and the footnote line); the table now shows **Week / Date / Spot / Forecast / Delta**. The up/down/flat `direction_flag` logic is unchanged and still feeds the directional-accuracy KPI + the weekly directional-accuracy chart. → `app.py` `page_performance()`.
- **Co-branding → BigMint × Adani** — topbar now renders BigMint logo **×** Adani logo (Adani sits in a white chip via `_adani_logo_html()`, which loads `assets/adani_logo.png` or falls back to a gradient-text "adani"). Page title, login caption, home header and footer all read "BigMint × Adani". Also fixed brand-name casing **Bigmint → BigMint** (login caption + home header in `app.py`; the wordmark fallback in `theme.py`). → `theme.py` (`_adani_logo_html`, `render_topbar`, CSS `.bm-adani-chip` / `.bm-cobrand-x`, footer) + `app.py`. The official `adani_logo.png` is now in place and **auto-trimmed** (1402×854 → 1108×452; untrimmed original kept as `adani_logo_orig.png`), so the topbar shows the real Adani logo (fallback no longer used).
- **Removed model-architecture mentions (NHITS / NBEATSx / TFT / …)** — dropped the "Model agreement (top-3 by direction)" footnote and the `top3` read in `page_forecasting()`. These names were never hardcoded in the app; they came only from the data's `Top-3 models (direction)` column, which still exists in `forecast_forward.xlsx` but is no longer surfaced anywhere in the UI. → `app.py`.
- **Removed Raw-material price forecast section** — deleted the second tab in `page_forecasting()`; the page is now **steel-only with no tab wrapper** (steel content rendered directly under the page). Cleaned up the now-orphaned `BIGMINT_URL` (`app.py`) and `STEEL_FF_LABELS` (`data_loader.py`), and dropped "plus the raw-material feed" from the Home "Price forecasting" card. (Unrelated "raw material" wording in the analyst market-commentary placeholder and the cost calculator's cost categories was left as-is.) → `app.py`, `data_loader.py`.
- **Home modules → uniform clickable card-buttons** — replaced the three HTML `module_card`s + separate "Open" buttons **and** the standalone Calculators card/button with **four equal clickable card-buttons in one row** (`st.columns(4)`): Price Forecasting / Analyst Calls / Performance / Calculators. Each whole card is a single `st.button` (material icon + **bold title** + description) that navigates on click — no more separate "Open" button. Styled via `div[class*="st-key-homemod_"]` CSS in `theme.py`, scoped by Streamlit's per-key container class (≥1.39; running 1.58) so nav/logout/other buttons are untouched. `theme.module_card()` is now unused but left in place. → `app.py` `page_home()` + `theme.py`.

## Pending / not done
- Analyst Calls: real summaries + PPT/PDF/**video** + upload workflow (PDF/PPT/Video buttons exist but are disabled placeholders).
- Horizon tabs (Short/Medium/Long/Weekly) from the reference — NOT added (locked to 12-wk).
- Calculators' inner styling still original (lighter look than the rest).
