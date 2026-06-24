"""
Static-snapshot data loader for the BigMint - AI Labs portal.

Reads the dashboard's existing files ONCE (cached) and reshapes the messy
multi-header sheets into tidy per-product frames. No live connection: the
@st.cache_data layer means each file is read a single time per session.

Sources (under the dashboard base folder, one level up from /portal):
  * accuracy_tables/forecast_forward.xlsx  - summary + 12-week forward path
  * accuracy_tables/Accuracy_Table_6.xlsx  - week-wise actual/forecast (6wk eval)
  * accuracy_tables/Accuracy_Table_16.xlsx - week-wise actual/forecast (16wk eval)
"""
import os
import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../dashboard
ACC_DIR = os.path.join(BASE, "accuracy_tables")
FF_PATH = os.path.join(ACC_DIR, "forecast_forward.xlsx")
ACC_PATHS = {
    "6-week":  os.path.join(ACC_DIR, "Accuracy_Table_6.xlsx"),
    "16-week": os.path.join(ACC_DIR, "Accuracy_Table_16.xlsx"),
}
HEADLINE_SHEET = "Ensemble_WgtMean"   # headline forecast line shown to Adani

# display name -> sheet/label used in the source files
STEEL_PRODUCTS = {
    "HRC":                   {"ff": "HRC",                 "acc": "HRC"},
    "HR Plate":              {"ff": "HR PLATE",            "acc": "HR PLATE"},
    "Rebar BF Mumbai":       {"ff": "REBAR BF MUMBAI",     "acc": "REBAR BF MUMBAI"},
    "Rebar IF Mumbai":       {"ff": "REBAR IF MUMBAI",     "acc": "REBAR IF MUMBAI"},
    "Rebar IF Raipur":       {"ff": "REBAR IF RAIPUR",     "acc": "REBAR IF RAIPUR"},
    "Structure (IF Raipur)": {"ff": "STRUCTURE IF RAIPUR", "acc": "STRUCTURE IF RAIPUR"},
}
# raw-material rows in the summary (everything that is not one of the six steel sheets)
STEEL_FF_LABELS = {v["ff"] for v in STEEL_PRODUCTS.values()}


def _num(s):
    return pd.to_numeric(
        s.astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.strip(),
        errors="coerce",
    )


@st.cache_data(show_spinner=False)
def load_summary() -> pd.DataFrame:
    """Forecast_forward 'Summary' sheet (already tidy)."""
    df = pd.read_excel(FF_PATH, sheet_name="Summary")
    df.columns = [str(c).strip() for c in df.columns]
    return df


@st.cache_data(show_spinner=False)
def load_forward(ff_sheet: str) -> pd.DataFrame:
    """12-week forward path for one product. Returns Date, Week, Forecast, Delta, Direction."""
    raw = pd.read_excel(FF_PATH, sheet_name=ff_sheet, header=None)
    # row 0 = title, row 1 = column names, row 2+ = weekly rows
    data = raw.iloc[2:, :5].copy()
    data.columns = ["Date", "Week", "Forecast", "Delta", "Direction"]
    data = data.dropna(subset=["Date"])
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Week"] = pd.to_numeric(data["Week"], errors="coerce").astype("Int64")
    data["Forecast"] = _num(data["Forecast"])
    data["Delta"] = _num(data["Delta"])
    data["Direction"] = data["Direction"].astype(str).str.strip()
    return data.dropna(subset=["Date", "Forecast"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_accuracy(window: str, acc_label: str) -> pd.DataFrame:
    """Week-wise Actual/Forecast for one product from an accuracy table.

    Returns Date, Actual, Forecast, Delta, DeltaPct, PredDir, ActualDir, Hit.
    """
    path = ACC_PATHS[window]
    raw = pd.read_excel(path, sheet_name=HEADLINE_SHEET, header=None)

    # locate the product's block start column from the product-label row (row 0)
    labels = [str(x).strip() if pd.notna(x) else "" for x in raw.iloc[0].tolist()]
    if acc_label not in labels:
        return pd.DataFrame(columns=["Date", "Actual", "Forecast"])
    start = labels.index(acc_label)

    dates = pd.to_datetime(raw.iloc[3:, 0], errors="coerce")
    actual = _num(raw.iloc[3:, start])
    forecast = _num(raw.iloc[3:, start + 1])
    df = pd.DataFrame({"Date": dates.values, "Actual": actual.values, "Forecast": forecast.values})
    df = df.dropna(subset=["Date"]).dropna(subset=["Actual", "Forecast"], how="all").reset_index(drop=True)

    df["Delta"] = df["Forecast"] - df["Actual"]
    df["DeltaPct"] = (df["Delta"] / df["Actual"]) * 100
    prev_actual = df["Actual"].shift(1)
    df["PredDir"] = (df["Forecast"] > prev_actual).map({True: "Up", False: "Down"})
    df["ActualDir"] = (df["Actual"] > prev_actual).map({True: "Up", False: "Down"})
    df.loc[df.index[0], ["PredDir", "ActualDir"]] = "Flat"
    df["Hit"] = df["PredDir"] == df["ActualDir"]
    return df


def accuracy_kpis(df: pd.DataFrame) -> dict:
    """Compute MAPA (absolute accuracy), directional accuracy and avg delta over a frame."""
    if df.empty:
        return {"mapa": None, "dir_acc": None, "avg_delta": None}
    valid = df.dropna(subset=["Actual", "Forecast"])
    mape = (valid["Delta"].abs() / valid["Actual"]).mean() * 100
    rows = valid.iloc[1:]   # first row has no previous reference
    dir_acc = rows["Hit"].mean() * 100 if len(rows) else None
    return {
        "mapa": 100 - mape,
        "dir_acc": dir_acc,
        "avg_delta": valid["DeltaPct"].mean(),
    }


def summary_row(summary: pd.DataFrame, ff_label: str):
    """Return the summary row (dict) for a product label, or None."""
    m = summary[summary["Product"].astype(str).str.strip() == ff_label]
    return m.iloc[0].to_dict() if not m.empty else None
