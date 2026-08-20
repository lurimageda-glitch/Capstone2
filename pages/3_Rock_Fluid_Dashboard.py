"""
pages/3_Rock_Fluid_Dashboard.py
=================================
Module C: Rock & Fluid Data Dashboard.

Lets the user upload a CSV of rock or fluid core data, view summary
statistics, filter interactively (e.g. by a porosity threshold), see a
porosity histogram and a porosity-permeability crossplot, and download
the filtered subset as a new CSV.

This module is deliberately flexible about column names -- it tries to
auto-detect a porosity and a permeability column (case-insensitively) so
it works with real, messy field data, but always lets the user override
the detected columns manually.
"""

import io

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="🪨", layout="wide")
st.title("🪨 Module C — Rock & Fluid Data Dashboard")
st.caption(
    "Upload a CSV of core/log/fluid-sample data to explore it: summary "
    "statistics, interactive filtering, a porosity histogram, a "
    "porosity-permeability crossplot, and a filtered-data download."
)


def _guess_column(columns, keywords):
    """
    Best-effort guess of which dataframe column matches a physical
    property, based on keyword matching in the column name.

    Parameters
    ----------
    columns : list of str
        Candidate column names from the uploaded dataframe.
    keywords : list of str
        Lower-case keywords to search for (e.g. ["poro"]).

    Returns
    -------
    str or None
        The first matching column name, or None if nothing matches.
    """
    for col in columns:
        lower = col.lower()
        if any(kw in lower for kw in keywords):
            return col
    return None


uploaded_file = st.file_uploader(
    "Upload a CSV file of rock or fluid data",
    type=["csv"],
    help="Any CSV works. If it has porosity/permeability-like column "
         "names they'll be auto-detected below; otherwise pick them manually.",
)

st.caption(
    "Don't have a file handy? A sample dataset is included in the repo at "
    "`sample_data/sample_rock_data.csv` -- download it from GitHub and "
    "upload it here to try the dashboard."
)

if uploaded_file is None:
    st.info("👆 Upload a CSV to get started.")
    st.stop()

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
try:
    df = pd.read_csv(uploaded_file)
except Exception as err:
    st.error(f"Could not read that file as a CSV: {err}")
    st.stop()

if df.empty:
    st.error("The uploaded file was read successfully but contains no rows.")
    st.stop()

st.success(f"Loaded {len(df):,} rows x {len(df.columns)} columns.")

with st.expander("Preview raw data", expanded=True):
    st.dataframe(df.head(20), use_container_width=True)

st.subheader("Summary statistics")
numeric_df = df.select_dtypes(include="number")
if numeric_df.empty:
    st.warning("No numeric columns were found, so summary statistics can't be computed.")
else:
    st.dataframe(numeric_df.describe().T, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Column selection for plots/filtering
# ---------------------------------------------------------------------------
st.subheader("Filtering & charts")

numeric_cols = list(numeric_df.columns)
if len(numeric_cols) < 1:
    st.warning("Need at least one numeric column to filter or chart. Stopping here.")
    st.stop()

guessed_poro = _guess_column(numeric_cols, ["poro"])
guessed_perm = _guess_column(numeric_cols, ["perm"])

c1, c2 = st.columns(2)
with c1:
    poro_col = st.selectbox(
        "Porosity column",
        numeric_cols,
        index=numeric_cols.index(guessed_poro) if guessed_poro in numeric_cols else 0,
    )
with c2:
    perm_options = ["(none)"] + numeric_cols
    default_perm_idx = perm_options.index(guessed_perm) if guessed_perm in perm_options else 0
    perm_col = st.selectbox("Permeability column (optional, for crossplot)", perm_options, index=default_perm_idx)

# ---------------------------------------------------------------------------
# Interactive filter
# ---------------------------------------------------------------------------
min_val = float(df[poro_col].min())
max_val = float(df[poro_col].max())
threshold = st.slider(
    f"Show only samples where '{poro_col}' >",
    min_value=min_val,
    max_value=max_val,
    value=min_val,
)
filtered_df = df[df[poro_col] > threshold].copy()
st.write(f"**{len(filtered_df):,}** of **{len(df):,}** rows match the filter (`{poro_col} > {threshold:.3g}`).")

if filtered_df.empty:
    st.warning("No rows match the current filter -- loosen the threshold to see charts and enable the download.")
else:
    # -----------------------------------------------------------------
    # Charts
    # -----------------------------------------------------------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(f"**{poro_col} histogram**")
        hist_data = filtered_df[poro_col].dropna()
        bins = min(30, max(5, int(len(hist_data) ** 0.5)))
        counts, bin_edges = pd.cut(hist_data, bins=bins, retbins=True)
        hist_df = counts.value_counts().sort_index()
        hist_plot_df = pd.DataFrame(
            {"count": hist_df.values},
            index=[f"{iv.left:.2f}-{iv.right:.2f}" for iv in hist_df.index],
        )
        st.bar_chart(hist_plot_df)

    with chart_col2:
        if perm_col != "(none)":
            st.markdown(f"**{poro_col} vs {perm_col} crossplot**")
            st.scatter_chart(filtered_df, x=poro_col, y=perm_col)
        else:
            st.info("Pick a permeability column above to see a crossplot.")

    st.divider()

    # -----------------------------------------------------------------
    # Download
    # -----------------------------------------------------------------
    st.subheader("Export filtered data")
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_buffer.getvalue(),
        file_name="filtered_rock_fluid_data.csv",
        mime="text/csv",
    )

    with st.expander("Show filtered data table"):
        st.dataframe(filtered_df, use_container_width=True)
