"""
pages/1_Pipe_Flow_Analyser.py
==============================
Module A: Pipe Flow Analyser.

Lets the user pick a fluid (from a small built-in library or fully
user-defined), enter pipe geometry and a flow rate, and see velocity,
Reynolds number, friction factor and pressure drop. Also draws an
interactive pressure-drop-vs-flow-rate curve and offers a CSV export of
that curve.

All the actual physics lives in `engineering.py` (Fluid, Pipe classes) --
this file is presentation/UI only, which keeps the OOP engine reusable
and independently testable.
"""

import io

import numpy as np
import pandas as pd
import streamlit as st

from engineering import Fluid, Pipe

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="🌊", layout="wide")
st.title("🌊 Module A — Pipe Flow Analyser")
st.caption(
    "Steady, incompressible, single-phase flow in a circular pipe. "
    "Friction factor from the Colebrook (Swamee-Jain) correlation for "
    "turbulent flow, or the exact laminar solution f = 64/Re."
)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Fluid")
fluid_choice = st.sidebar.selectbox(
    "Fluid type",
    list(Fluid.LIBRARY.keys()) + ["User-defined"],
    help="Pick a built-in fluid (properties auto-populate) or define your own.",
)

if fluid_choice == "User-defined":
    fluid_name = st.sidebar.text_input("Fluid name", value="My fluid")
    density = st.sidebar.number_input(
        "Density, rho (kg/m^3)", min_value=0.01, value=1000.0, step=1.0
    )
    viscosity = st.sidebar.number_input(
        "Dynamic viscosity, mu (Pa.s)", min_value=1e-6, value=1.0e-3,
        step=1e-4, format="%.6f",
    )
else:
    props = Fluid.LIBRARY[fluid_choice]
    fluid_name = fluid_choice
    density = st.sidebar.number_input(
        "Density, rho (kg/m^3)", value=float(props["density"]), step=1.0,
        help="Auto-populated from the library; feel free to override.",
    )
    viscosity = st.sidebar.number_input(
        "Dynamic viscosity, mu (Pa.s)", value=float(props["viscosity"]),
        step=1e-4, format="%.6f",
        help="Auto-populated from the library; feel free to override.",
    )

st.sidebar.header("Pipe geometry")
diameter_mm = st.sidebar.number_input(
    "Internal diameter, D (mm)", min_value=1.0, value=100.0, step=5.0
)
length_m = st.sidebar.number_input(
    "Pipe length, L (m)", min_value=0.1, value=50.0, step=1.0
)
roughness_mm = st.sidebar.number_input(
    "Absolute roughness, epsilon (mm)", min_value=0.0, value=0.045, step=0.005,
    format="%.4f",
    help="e.g. commercial steel ~0.045 mm, PVC ~0.0015 mm, cast iron ~0.26 mm.",
)

st.sidebar.header("Flow rate")
flow_lpm = st.sidebar.number_input(
    "Volumetric flow rate, Q (L/min)", min_value=0.1, value=500.0, step=10.0
)

# ---------------------------------------------------------------------------
# Build model objects and calculate
# ---------------------------------------------------------------------------
try:
    fluid = Fluid(fluid_name, density, viscosity)
    pipe = Pipe(diameter_mm / 1000.0, length_m, roughness_mm / 1000.0, fluid)
    flow_m3s = flow_lpm / 60000.0  # L/min -> m^3/s

    results = pipe.summary(flow_m3s)

    st.subheader("Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Velocity", f"{results['velocity_m_s']:.3f} m/s")
    c2.metric("Reynolds number", f"{results['reynolds_number']:.0f}", results["flow_regime"])
    c3.metric("Friction factor (Darcy)", f"{results['friction_factor']:.4f}")
    c4.metric("Pressure drop", f"{results['pressure_drop_pa'] / 1000:.2f} kPa")

    with st.expander("Show pressure drop in other units"):
        dp_pa = results["pressure_drop_pa"]
        st.write(f"- {dp_pa:,.1f} Pa")
        st.write(f"- {dp_pa / 1000:,.3f} kPa")
        st.write(f"- {dp_pa / 6894.76:,.4f} psi")
        st.write(f"- {dp_pa / 9806.65:,.3f} m of water head")

    st.divider()

    # -----------------------------------------------------------------
    # Interactive plot: pressure drop vs flow rate
    # -----------------------------------------------------------------
    st.subheader("Pressure drop vs. flow rate")
    max_q = st.slider(
        "Maximum flow rate to plot (L/min)",
        min_value=float(flow_lpm),
        max_value=float(flow_lpm) * 5,
        value=float(flow_lpm) * 2,
    )
    q_range_lpm = np.linspace(max(0.01, flow_lpm * 0.02), max_q, 60)
    dp_values = []
    for q in q_range_lpm:
        try:
            dp_values.append(pipe.pressure_drop(q / 60000.0) / 1000.0)  # kPa
        except ValueError:
            dp_values.append(np.nan)

    plot_df = pd.DataFrame({"Flow rate (L/min)": q_range_lpm, "Pressure drop (kPa)": dp_values})
    st.line_chart(plot_df, x="Flow rate (L/min)", y="Pressure drop (kPa)")

    st.divider()

    # -----------------------------------------------------------------
    # CSV export
    # -----------------------------------------------------------------
    st.subheader("Export")
    export_df = plot_df.copy()
    export_df.insert(0, "Fluid", fluid.name)
    export_df["Pipe diameter (mm)"] = diameter_mm
    export_df["Pipe length (m)"] = length_m
    export_df["Roughness (mm)"] = roughness_mm

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="⬇️ Download pressure-drop curve as CSV",
        data=csv_buffer.getvalue(),
        file_name="pipe_flow_pressure_drop_curve.csv",
        mime="text/csv",
    )

    with st.expander("Show underlying data table"):
        st.dataframe(export_df, use_container_width=True)

except ValueError as err:
    st.error(f"Input error: {err}")

with st.expander("ℹ️ How this is calculated"):
    st.markdown(
        r"""
- **Velocity:** $V = Q / A$, where $A = \pi D^2 / 4$.
- **Reynolds number:** $Re = \rho V D / \mu$.
- **Friction factor:**
  - Laminar ($Re < 2300$): $f = 64 / Re$ (exact).
  - Turbulent: Swamee-Jain explicit approximation to Colebrook,
    $f = 0.25 \left[ \log_{10}\left(\frac{\epsilon/D}{3.7} + \frac{5.74}{Re^{0.9}}\right) \right]^{-2}$.
- **Pressure drop (Darcy-Weisbach):** $\Delta P = f \dfrac{L}{D} \dfrac{\rho V^2}{2}$.
        """
    )

