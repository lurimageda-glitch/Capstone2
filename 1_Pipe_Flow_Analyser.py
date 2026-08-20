"""Module A: Pipe Flow Analyser.

Calculates velocity, Reynolds number, friction factor, and pressure drop for
steady incompressible flow through a circular pipe, using the Darcy-Weisbach
equation. Provides an interactive pressure-drop-vs-flow-rate chart and CSV export.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from engineering import Fluid, Pipe

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="🚰", layout="wide")
st.title("🚰 Pipe Flow Analyser")
st.markdown(
    "Calculates velocity, Reynolds number, friction factor, and pressure drop for flow "
    "through a circular pipe, using the **Darcy-Weisbach equation** with the "
    "**Swamee-Jain** friction-factor correlation. Use the sidebar to set the fluid, "
    "pipe geometry, and flow rate."
)

st.sidebar.header("Fluid")
fluid_choice = st.sidebar.selectbox("Fluid type", ["Water", "Air", "Crude Oil", "User-defined"])

st.sidebar.header("Pipe Geometry")
D = st.sidebar.slider("Diameter, D (m)", min_value=0.01, max_value=1.0, value=0.10, step=0.01,
                       help="Internal pipe diameter.")
L = st.sidebar.slider("Length, L (m)", min_value=1.0, max_value=1000.0, value=100.0, step=1.0,
                       help="Total pipe length.")
rough = st.sidebar.number_input(
    "Absolute roughness, ε (m)", min_value=0.0, value=0.000045, step=0.00001, format="%.6f",
    help="Typical: commercial steel ≈0.000045 m, PVC ≈0.0000015 m, cast iron ≈0.00026 m"
)

st.sidebar.header("Flow")
Q = st.sidebar.slider("Flow rate, Q (m³/s)", min_value=0.0001, max_value=0.5, value=0.0100, step=0.0001,
                       format="%.4f", help="Volumetric flow rate through the pipe.")

try:
    if fluid_choice == "User-defined":
        density = st.sidebar.number_input("Density (kg/m³)", min_value=0.0, value=1000.0)
        viscosity = st.sidebar.number_input(
            "Dynamic viscosity (Pa·s)", min_value=0.0, value=0.00100, step=0.0001, format="%.5f"
        )
        fluid = Fluid.from_name("User Fluid", density=density, viscosity=viscosity)
    else:
        fluid = Fluid.from_name(fluid_choice)
        st.sidebar.caption(f"ρ = {fluid.density} kg/m³   μ = {fluid.viscosity} Pa·s")

    pipe = Pipe(D, L, rough)

    v = pipe.velocity(Q)
    Re = pipe.reynolds_number(fluid, Q)
    f = pipe.friction_factor(fluid, Q)
    dP = pipe.pressure_drop(fluid, Q)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Velocity", f"{v:.3f} m/s")
    col2.metric("Reynolds Number", f"{Re:,.0f}")
    col3.metric("Friction Factor", f"{f:.4f}")
    col4.metric("Pressure Drop", f"{dP:,.0f} Pa")

    flow_type = "Laminar" if Re < 2300 else ("Transitional" if Re < 4000 else "Turbulent")
    st.info(f"Flow regime: **{flow_type}** (Re = {Re:,.0f})")

    st.markdown("### Pressure Drop vs Flow Rate")
    Q_range = np.linspace(max(Q * 0.1, 1e-6), Q * 3, 40)
    dP_range = [pipe.pressure_drop(fluid, q) for q in Q_range]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(Q_range, dP_range, color="#1f5fa8", linewidth=2)
    ax.axvline(Q, color="red", linestyle="--", label=f"Current Q = {Q:.4f} m³/s")
    ax.set_xlabel("Flow rate, Q (m³/s)")
    ax.set_ylabel("Pressure drop, ΔP (Pa)")
    ax.set_title("Pressure Drop vs Flow Rate")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    st.markdown("### Results Table")
    df = pd.DataFrame({"Flow rate (m3/s)": Q_range, "Pressure drop (Pa)": dP_range})
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download results as CSV", csv, "pipe_flow_results.csv", "text/csv")

except ValueError as e:
    st.warning(f"⚠️ Invalid input: {e}")
    st.info("Please correct the sidebar inputs to see results.")
