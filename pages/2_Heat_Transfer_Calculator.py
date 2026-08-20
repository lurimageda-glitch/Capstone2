"""
2_Heat_Transfer_Calculator.py
==============================
Module B: Heat Transfer Calculator.

Two calculators in tabs:
  1. Steady-state 1D conduction through a flat wall (Fourier's Law).
  2. Newton's Law of Cooling: time to cool from T0 to a target
     temperature in a given ambient, plus a live temperature-vs-time plot.
"""

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from engineering import CoolingBody, FlatWall

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🔥", layout="wide")
st.title("🔥 Heat Transfer Calculator")

tab1, tab2 = st.tabs(["🧱 Conduction (Flat Wall)", "☕ Newton's Law of Cooling"])

# ---------------------------------------------------------------------------
# TAB 1: Steady-state conduction
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Steady-state conduction through a single-layer flat wall")
    st.markdown(
        "Fourier's Law: heat flows through the wall from the hot face to the "
        "cold face at a rate set by the material's thermal conductivity, the "
        "wall thickness, and the temperature difference: "
        "**q = k · (T_hot − T_cold) / thickness**."
    )

    col1, col2 = st.columns(2)
    with col1:
        thickness_mm = st.number_input(
            "Wall thickness (mm)", min_value=1.0, value=200.0, step=10.0,
            help="Distance the heat has to travel through the material, "
                 "hot face to cold face.",
        )
        k_wall = st.number_input(
            "Thermal conductivity, k (W/m·K)", min_value=0.001, value=0.7,
            step=0.05,
            help="Material property: how easily heat conducts through it. "
                 "Typical values — brick ≈ 0.7, glass ≈ 1.0, wood ≈ 0.15, "
                 "steel ≈ 45, still air ≈ 0.026.",
        )
        area_wall = st.number_input(
            "Wall area (m²)", min_value=0.01, value=10.0, step=1.0,
            help="Cross-sectional area through which heat flows (perpendicular "
                 "to the direction of heat travel).",
        )
    with col2:
        t_hot = st.number_input(
            "Hot-face temperature (°C)", value=25.0, step=1.0,
            help="Temperature on the warmer side of the wall.",
        )
        t_cold = st.number_input(
            "Cold-face temperature (°C)", value=5.0, step=1.0,
            help="Temperature on the cooler side of the wall.",
        )

    try:
        wall = FlatWall(thickness=thickness_mm / 1000.0, thermal_conductivity=k_wall, area=area_wall)
        q_flux = wall.heat_flux(t_hot, t_cold)
        q_rate = wall.heat_rate(t_hot, t_cold)

        st.subheader("Results")
        m1, m2 = st.columns(2)
        m1.metric("Heat flux, q", f"{q_flux:.2f} W/m²")
        m2.metric("Total heat transfer rate, Q", f"{q_rate:.1f} W")

        if t_hot < t_cold:
            st.info(
                "Note: hot-face temperature is lower than cold-face temperature, "
                "so heat is actually flowing in the reverse direction (negative flux)."
            )
    except ValueError as e:
        st.error(f"Input error: {e}")

# ---------------------------------------------------------------------------
# TAB 2: Newton's Law of Cooling
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Newton's Law of Cooling — time to reach a target temperature")
    st.markdown(
        "Lumped-capacitance model: a body of uniform temperature loses heat to "
        "its surroundings at a rate proportional to the temperature difference. "
        "**T(t) = T∞ + (T₀ − T∞)·e^(−k·t)**, where **k = h·A / (m·c)**."
    )

    col1, col2 = st.columns(2)
    with col1:
        h_coef = st.slider(
            "Convective heat transfer coefficient, h (W/m²·K)",
            min_value=1.0, max_value=200.0, value=10.0, step=1.0,
            help="How effectively the surrounding fluid carries heat away. "
                 "Still air ≈ 5–25, forced air ≈ 25–250, water ≈ 500+.",
        )
        area_body = st.slider(
            "Surface area exposed to ambient, A (m²)",
            min_value=0.001, max_value=2.0, value=0.05, step=0.001,
            help="The body's surface area in contact with the surrounding fluid.",
        )
        mass_body = st.slider(
            "Mass of the body, m (kg)",
            min_value=0.01, max_value=50.0, value=0.3, step=0.01,
            help="Total mass of the object being cooled.",
        )
        c_body = st.slider(
            "Specific heat capacity, c (J/kg·K)",
            min_value=100.0, max_value=5000.0, value=4186.0, step=10.0,
            help="Energy needed to raise 1 kg of the material by 1°C. "
                 "Water ≈ 4186, aluminium ≈ 900, steel ≈ 490.",
        )
    with col2:
        t0 = st.slider("Initial temperature, T₀ (°C)", min_value=-20.0, max_value=200.0, value=90.0, step=1.0,
                        help="Starting temperature of the body.")
        t_inf = st.slider("Ambient temperature, T∞ (°C)", min_value=-20.0, max_value=200.0, value=20.0, step=1.0,
                           help="Temperature of the surrounding environment, far from the body.")
        t_target = st.slider("Target temperature (°C)", min_value=-20.0, max_value=200.0, value=40.0, step=1.0,
                              help="The temperature you want the body to cool down to.")

    try:
        body = CoolingBody(h=h_coef, area=area_body, mass=mass_body, specific_heat=c_body)
        k_const = body.rate_constant()

        st.subheader("Results")
        m1, m2 = st.columns(2)
        m1.metric("Cooling-rate constant, k", f"{k_const:.6f} 1/s")

        try:
            t_reach = body.time_to_reach(t0, t_inf, t_target)
            m2.metric("Time to reach target", f"{t_reach:.1f} s ({t_reach/60:.2f} min)")

            # Live cooling curve, extending a bit past the target time
            t_end = t_reach * 1.5
            time_vals = np.linspace(0, t_end, 300)
            temp_vals = [body.temperature_at(t0, t_inf, t) for t in time_vals]

            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.plot(time_vals, temp_vals, color="#d62728", linewidth=2, label="Body temperature")
            ax.axhline(t_inf, color="gray", linestyle=":", label=f"Ambient T∞ = {t_inf:g} °C")
            ax.axhline(t_target, color="green", linestyle="--", label=f"Target = {t_target:g} °C")
            ax.axvline(t_reach, color="green", linestyle="--", alpha=0.5)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Temperature (°C)")
            ax.set_title("Cooling Curve — Newton's Law of Cooling")
            ax.grid(alpha=0.3)
            ax.legend()
            st.pyplot(fig)

        except ValueError as e:
            st.warning(f"Cannot compute time-to-target: {e}")

    except ValueError as e:
        st.error(f"Input error: {e}")
