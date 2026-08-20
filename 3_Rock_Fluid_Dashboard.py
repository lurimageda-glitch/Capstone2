"""Module C: Rock & Fluid Data Dashboard.

Accepts a user-uploaded CSV of rock or fluid sample data, displays summary
statistics, allows filtering by a porosity threshold, produces a porosity
histogram and a porosity-permeability crossplot, and offers a filtered-CSV
download. All steps are wrapped in error handling so a malformed or
column-missing file shows a warning instead of crashing the app.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="🪨", layout="wide")
st.title("🪨 Rock & Fluid Data Dashboard")
st.markdown(
    "Upload a CSV of rock or fluid sample data (should include a `porosity` column, and "
    "ideally a `permeability` column) to view summary statistics, filter samples, and "
    "visualise the data. Example columns: `sample_id, porosity, permeability, lithology`."
)

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.warning(f"⚠️ Could not read the uploaded file as a CSV: {e}")
        st.stop()

    if df.empty:
        st.warning("⚠️ The uploaded file contains no rows of data.")
        st.stop()

    st.markdown("### Uploaded Data Preview")
    st.dataframe(df.head(20), use_container_width=True)

    st.markdown("### Summary Statistics")
    st.dataframe(df.describe(), use_container_width=True)

    porosity_col = next(
        (c for c in df.columns if c.strip().lower() in ("porosity", "phi")), None
    )

    if porosity_col is None:
        st.warning(
            "⚠️ No 'porosity' column found in the uploaded file — filtering and the "
            "porosity charts are unavailable. Only the preview and summary statistics "
            "above are shown."
        )
    else:
        if not pd.api.types.is_numeric_dtype(df[porosity_col]):
            st.warning(f"⚠️ The '{porosity_col}' column is not numeric — cannot filter or plot it.")
            st.stop()

        st.markdown("### Filter by Porosity")
        min_p, max_p = float(df[porosity_col].min()), float(df[porosity_col].max())
        if min_p == max_p:
            st.info(f"All samples have the same {porosity_col} value ({min_p}); filtering is not meaningful.")
            filtered = df
        else:
            threshold = st.slider(
                f"Show only samples where {porosity_col} > X", min_p, max_p, min_p
            )
            filtered = df[df[porosity_col] > threshold]
            st.write(f"Showing **{len(filtered)}** of **{len(df)}** samples with "
                     f"{porosity_col} > {threshold:.3f}")

        st.dataframe(filtered, use_container_width=True)

        if filtered.empty:
            st.warning("⚠️ No samples match the current filter — try lowering the threshold.")
        else:
            st.markdown("### Charts")
            c1, c2 = st.columns(2)

            with c1:
                fig1, ax1 = plt.subplots()
                ax1.hist(filtered[porosity_col].dropna(), bins=15, color="#1f5fa8", edgecolor="white")
                ax1.set_xlabel(porosity_col)
                ax1.set_ylabel("Count")
                ax1.set_title(f"{porosity_col.title()} Histogram")
                st.pyplot(fig1)

            with c2:
                perm_col = next(
                    (c for c in df.columns if c.strip().lower() in ("permeability", "perm", "k")), None
                )
                if perm_col and pd.api.types.is_numeric_dtype(df[perm_col]):
                    plot_data = filtered[[porosity_col, perm_col]].dropna()
                    plot_data = plot_data[plot_data[perm_col] > 0]  # log scale needs positive values
                    if plot_data.empty:
                        st.info(f"No positive '{perm_col}' values available to plot on a log scale.")
                    else:
                        fig2, ax2 = plt.subplots()
                        ax2.scatter(plot_data[porosity_col], plot_data[perm_col],
                                    color="#2e8b57", alpha=0.7)
                        ax2.set_xlabel(porosity_col)
                        ax2.set_ylabel(perm_col)
                        ax2.set_yscale("log")
                        ax2.set_title(f"{porosity_col.title()} vs {perm_col.title()} Crossplot")
                        st.pyplot(fig2)
                else:
                    st.info("No 'permeability' column found — crossplot unavailable. "
                            "Only the porosity histogram is shown.")

            csv_out = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download filtered data as CSV", csv_out, "filtered_rock_fluid_data.csv", "text/csv"
            )
else:
    st.info("Upload a CSV file above to get started.")
    st.markdown("**Example CSV format:**")
    example = pd.DataFrame({
        "sample_id": ["S-01", "S-02", "S-03"],
        "porosity": [0.18, 0.22, 0.15],
        "permeability": [120, 340, 45],
        "lithology": ["sandstone", "sandstone", "shale"],
    })
    st.dataframe(example, use_container_width=True)
