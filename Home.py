"""
AI Documentation
----------------
AI tools used: Claude (Anthropic) for architecture design, code generation, and debugging.

Key prompts given:
1. "Design a multi-page Streamlit engineering suite with a separate engineering.py module
   containing OOP classes (Fluid, Pipe, PlaneWallConduction, NewtonCooling) for pipe flow
   and heat transfer calculations, each with docstrings and input validation via ValueError."
2. "Build a Pipe Flow Analyser page using the Darcy-Weisbach equation and an explicit
   (non-iterative) friction factor correlation, with an interactive pressure-drop-vs-flow-rate
   chart and CSV export."
3. "Build a Rock & Fluid Data Dashboard page that accepts an uploaded CSV, computes summary
   statistics, supports a porosity threshold filter, shows a histogram and a porosity-
   permeability crossplot, and offers a filtered-CSV download — all wrapped in error handling
   so a malformed or column-missing CSV shows a warning instead of crashing the app."

Most important thing manually fixed/verified: the Swamee-Jain friction-factor correlation
(an explicit approximation used in place of an iterative Colebrook solve) had to be manually
checked against a hand-calculated Moody-chart example to confirm accuracy, and the
Newton's-Law-of-Cooling time-to-target formula had to be manually verified to correctly
reject non-physical inputs (e.g. a target temperature outside the range between the initial
and ambient temperatures) rather than silently returning a negative or complex time.
"""

import streamlit as st

st.set_page_config(page_title="Fluid Flow & Heat Transfer Suite", page_icon="🛠️", layout="wide")

st.title("🛠️ Fluid Flow & Heat Transfer Engineering Suite")
st.subheader("A multi-module engineering calculation and data-analysis toolkit")

st.markdown(
    """
    **Instructions:** Use the sidebar (**Pages**) to navigate between modules:

    - **🚰 Pipe Flow Analyser** — velocity, Reynolds number, friction factor, and
      pressure drop for flow through a circular pipe, with an interactive
      pressure-drop-vs-flow-rate chart and CSV export.
    - **🔥 Heat Transfer Calculator** — steady-state conduction through a flat wall
      (Fourier's law) and transient lumped-capacitance cooling (Newton's Law of
      Cooling), with a live-updating cooling curve.
    - **🪨 Rock & Fluid Data Dashboard** — upload a CSV of rock/fluid sample data,
      view summary statistics, filter by porosity, view a histogram and a
      porosity-permeability crossplot, and download the filtered data.

    All engineering calculations are implemented as documented, validated classes in
    `engineering.py` (imported by each module) rather than inline in the page code,
    and every function includes error handling so invalid inputs show a warning
    message instead of crashing the app.
    """
)

st.info("👈 Select a module from the sidebar to get started.")
