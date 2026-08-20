"""
1_Pipe_Flow_Analyser.py
========================
Module A: Pipe Flow Analyser.

Lets the user pick a fluid (preset or custom), enter pipe geometry and a
flow rate, and see velocity, Reynolds number, friction factor, and
pressure drop. Also plots pressure drop vs a range of flow rates and lets
the user export results to CSV.
"""

import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from engineering import FLUID_LIBRARY, Fluid, Pipe

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="📐", layout="wide")
st.title("📐 Pipe Flow Analyser")
st.caption(
    "Steady, incompressible internal flow. Friction factor: laminar f = 64/Re "
    "(Re < 2300); turbulent via the Swamee-Jain approximation to Colebrook."
)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Fluid")

fluid_choice = st.sidebar.selectbox(
    "Fluid type",
    options=list(FLUID_LIBRARY.keys()) + ["Custom fluid..."],
    help="Pick a preset, or choose 'Custom fluid...' to enter your own properties.",
)

try:
    if fluid_choice == "Custom fluid...":
        st.sidebar.markdown("**Custom fluid properties**")
        custom_name = st.sidebar.text_input("Fluid name", value="My Fluid")
        density = st.sidebar.number_input(
            "Density (kg/m³)", min_value=0.0001, value=1000.0, step=10.0,
            help="Mass per unit volume of the fluid.",
        )
        viscosity = st.sidebar.number_input(
            "Dynamic viscosity (Pa·s)", min_value=1e-6, value=1.0e-3,
            step=1e-4, format="%.6f",
            help="Resistance of the fluid to shear/flow.",
        )
        fluid = Fluid(custom_name, density, viscosity)
    else:
        fluid = Fluid.from_library(fluid_choice)

    st.sidebar.caption(f"ρ = {fluid.density:g} kg/m³  |  μ = {fluid.viscosity:g} Pa·s")

    st.sidebar.header("Pipe geometry")
    diameter_mm = st.sidebar.number_input(
        "Internal diameter (mm)", min_value=1.0, value=50.0, step=1.0,
        help="Inner diameter of the pipe.",
    )
    length_m = st.sidebar.number_input(
        "Pipe length (m)", min_value=0.1, value=100.0, step=1.0,
        help="Total straight-line length of pipe.",
    )
    roughness_mm = st.sidebar.number_input(
        "Absolute roughness (mm)", min_value=0.0, value=0.045, step=0.005,
        format="%.4f",
        help="Internal surface roughness (e.g. ~0.045 mm for commercial steel, "
             "~0.0015 mm for drawn tubing, 0 for perfectly smooth).",
    )

    st.sidebar.header("Flow rate")
    flow_rate_lps = st.sidebar.number_input(
        "Flow rate (L/s)", min_value=0.01, value=5.0, step=0.5,
        help="Volumetric flow rate through the pipe.",
    )

    # Convert to SI
    diameter = diameter_mm / 1000.0
    roughness = roughness_mm / 1000.0
    flow_rate = flow_rate_lps / 1000.0  # L/s -> m^3/s

    pipe = Pipe(diameter=diameter, length=length_m, roughness=roughness, fluid=fluid)
    results = pipe.summary(flow_rate)

    # -----------------------------------------------------------------------
    # Metric display
    # -----------------------------------------------------------------------
    st.subheader("Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Velocity", f"{results['velocity_m_s']:.3f} m/s")
    c2.metric("Reynolds number", f"{results['reynolds_number']:.0f}")
    regime = "Laminar" if results["reynolds_number"] < 2300 else "Turbulent"
    c3.metric("Flow regime", regime)
    c4.metric("Pressure drop", f"{results['pressure_drop_Pa']/1000:.2f} kPa")

    st.caption(f"Darcy friction factor f = {results['friction_factor']:.5f}")

    # -----------------------------------------------------------------------
    # Pressure drop vs flow rate plot
    # -----------------------------------------------------------------------
    st.subheader("Pressure drop vs flow rate")

    q_max_lps = st.slider(
        "Plot flow-rate range up to (L/s)",
        min_value=flow_rate_lps * 0.5,
        max_value=flow_rate_lps * 5,
        value=flow_rate_lps * 2,
        help="Sets the upper bound of the flow-rate axis for the plot below.",
    )

    q_range_lps = np.linspace(0.01, q_max_lps, 100)
    dp_values = [pipe.pressure_drop(q / 1000.0) / 1000.0 for q in q_range_lps]  # kPa

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(q_range_lps, dp_values, color="#1f77b4", linewidth=2)
    ax.axvline(flow_rate_lps, color="crimson", linestyle="--", linewidth=1,
               label=f"Current: {flow_rate_lps:g} L/s")
    ax.set_xlabel("Flow rate (L/s)")
    ax.set_ylabel("Pressure drop (kPa)")
    ax.set_title("Pressure Drop vs Flow Rate")
    ax.grid(alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    # -----------------------------------------------------------------------
    # CSV export
    # -----------------------------------------------------------------------
    st.subheader("Export")

    export_df = pd.DataFrame({
        "flow_rate_L_s": q_range_lps,
        "flow_rate_m3_s": q_range_lps / 1000.0,
        "pressure_drop_kPa": dp_values,
    })

    single_point_df = pd.DataFrame([{
        "fluid": fluid.name,
        "diameter_mm": diameter_mm,
        "length_m": length_m,
        "roughness_mm": roughness_mm,
        "flow_rate_L_s": flow_rate_lps,
        "velocity_m_s": results["velocity_m_s"],
        "reynolds_number": results["reynolds_number"],
        "friction_factor": results["friction_factor"],
        "pressure_drop_Pa": results["pressure_drop_Pa"],
    }])

    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "⬇️ Download current result (CSV)",
            data=single_point_df.to_csv(index=False).encode("utf-8"),
            file_name="pipe_flow_result.csv",
            mime="text/csv",
        )
    with col_b:
        st.download_button(
            "⬇️ Download pressure-drop curve (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="pipe_flow_curve.csv",
            mime="text/csv",
        )

except ValueError as e:
    st.error(f"Input error: {e}")
