"""
3_Rock_Fluid_Data_Dashboard.py
================================
Module C: Rock & Fluid Data Dashboard.

Lets the user upload a CSV of rock/fluid sample data (e.g. porosity,
permeability), shows summary statistics, allows filtering by porosity
threshold, produces a porosity histogram and a porosity-permeability
crossplot, and lets the user download the filtered data.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="🪨", layout="wide")
st.title("🪨 Rock & Fluid Data Dashboard")
st.caption(
    "Upload a CSV of rock/core or fluid sample data to explore it interactively."
)


def find_column(df: pd.DataFrame, keywords: list) -> str | None:
    """
    Return the first column in df whose lowercased name contains any of the
    given keywords. Used to auto-detect likely porosity/permeability columns
    so the user doesn't have to rename their file. Returns None if no match.
    """
    for col in df.columns:
        low = col.lower()
        if any(kw in low for kw in keywords):
            return col
    return None


uploaded_file = st.file_uploader(
    "Upload rock/fluid data (CSV)",
    type=["csv"],
    help="A CSV with sample data — ideally including a porosity column "
         "(e.g. 'porosity' or 'phi') and a permeability column (e.g. "
         "'permeability' or 'perm').",
)

if uploaded_file is None:
    st.info(
        "👆 Upload a CSV to begin. Expected columns include something like "
        "'porosity' (fraction or %) and 'permeability' (mD). Don't have a "
        "file handy? Here's a tiny synthetic sample you can download and "
        "re-upload to try the dashboard."
    )
    rng = np.random.default_rng(42)
    n = 50
    demo_porosity = rng.uniform(0.05, 0.30, n)
    demo_perm = 10 ** (demo_porosity * 20 - 2) * rng.uniform(0.5, 1.5, n)
    demo_df = pd.DataFrame({
        "sample_id": range(1, n + 1),
        "porosity": demo_porosity.round(4),
        "permeability_mD": demo_perm.round(2),
        "depth_m": rng.uniform(1000, 3000, n).round(1),
    })
    st.download_button(
        "⬇️ Download sample demo CSV",
        data=demo_df.to_csv(index=False).encode("utf-8"),
        file_name="demo_rock_data.csv",
        mime="text/csv",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Load & validate the uploaded file
# ---------------------------------------------------------------------------
try:
    df = pd.read_csv(uploaded_file)
    if df.empty:
        st.error("The uploaded CSV appears to be empty.")
        st.stop()
except Exception as e:
    st.error(f"Could not read this file as a CSV: {e}")
    st.stop()

st.subheader("Preview")
st.dataframe(df.head(10), use_container_width=True)

st.subheader("Summary statistics")
numeric_df = df.select_dtypes(include=[np.number])
if numeric_df.empty:
    st.warning("No numeric columns detected in this file — filtering and plots need numeric data.")
    st.stop()
st.dataframe(numeric_df.describe().T, use_container_width=True)

# ---------------------------------------------------------------------------
# Column selection (auto-detected, user-overridable)
# ---------------------------------------------------------------------------
st.subheader("Column mapping")
num_cols = list(numeric_df.columns)

auto_poro = find_column(df, ["poro", "phi"])
auto_perm = find_column(df, ["perm", "k_md", "permeab"])

col1, col2 = st.columns(2)
with col1:
    poro_col = st.selectbox(
        "Porosity column",
        options=num_cols,
        index=num_cols.index(auto_poro) if auto_poro in num_cols else 0,
        help="Column representing rock porosity (as a fraction, e.g. 0.0-1.0, or %).",
    )
with col2:
    perm_col = st.selectbox(
        "Permeability column",
        options=num_cols,
        index=num_cols.index(auto_perm) if auto_perm in num_cols else min(1, len(num_cols) - 1),
        help="Column representing rock permeability (commonly in millidarcies, mD).",
    )

# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
st.subheader("Filter")
poro_min = float(df[poro_col].min())
poro_max = float(df[poro_col].max())

threshold = st.slider(
    f"Show only samples where '{poro_col}' >",
    min_value=poro_min,
    max_value=poro_max,
    value=poro_min,
    help="Drag to filter out low-porosity samples.",
)

filtered_df = df[df[poro_col] > threshold]
st.write(f"**{len(filtered_df)}** of **{len(df)}** samples match this filter.")
st.dataframe(filtered_df, use_container_width=True)

if filtered_df.empty:
    st.warning("No samples match the current filter — try lowering the threshold.")
    st.stop()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
st.subheader("Charts")
c1, c2 = st.columns(2)

with c1:
    fig1, ax1 = plt.subplots(figsize=(6, 4.5))
    ax1.hist(filtered_df[poro_col].dropna(), bins=20, color="#2ca02c", edgecolor="black", alpha=0.8)
    ax1.set_xlabel(poro_col)
    ax1.set_ylabel("Count")
    ax1.set_title(f"Histogram of {poro_col}")
    ax1.grid(alpha=0.3)
    st.pyplot(fig1)

with c2:
    can_use_log = (filtered_df[perm_col] > 0).all()
    use_log = False
    if can_use_log:
        use_log = st.checkbox("Log scale for permeability axis", value=True)

    fig2, ax2 = plt.subplots(figsize=(6, 4.5))
    ax2.scatter(filtered_df[poro_col], filtered_df[perm_col], color="#1f77b4", alpha=0.7, edgecolor="black")
    ax2.set_xlabel(poro_col)
    ax2.set_ylabel(perm_col)
    ax2.set_title(f"{poro_col} vs {perm_col} Crossplot")
    if use_log:
        ax2.set_yscale("log")
    ax2.grid(alpha=0.3, which="both")
    st.pyplot(fig2)

# ---------------------------------------------------------------------------
# Download filtered data
# ---------------------------------------------------------------------------
st.subheader("Export")
st.download_button(
    "⬇️ Download filtered data (CSV)",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_rock_fluid_data.csv",
    mime="text/csv",
)

