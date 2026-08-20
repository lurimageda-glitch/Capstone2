"""Module B: Heat Transfer Calculator.

Two independent calculators:
1. Steady-state conduction through a single-layer flat wall (Fourier's law).
2. Transient lumped-capacitance cooling (Newton's Law of Cooling), including
   time-to-target and a live-updating temperature-vs-time cooling curve.
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from engineering import PlaneWallConduction, NewtonCooling

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🔥", layout="wide")
st.title("🔥 Heat Transfer Calculator")
st.markdown(
    "Two calculators: **(1)** steady-state conduction through a single-layer flat wall "
    "(Fourier's law), and **(2)** transient cooling of a lumped body in an ambient fluid "
    "(Newton's Law of Cooling)."
)

tab1, tab2 = st.tabs(["🧱 Conduction (Fourier's Law)", "❄️ Newton's Law of Cooling"])

# ----------------------------------------------------------------------------
# Tab 1: Conduction
# ----------------------------------------------------------------------------
with tab1:
    st.subheader("Steady-State Conduction Through a Flat Wall")
    st.caption("Q = k · A · (T₁ − T₂) / L — the rate of heat flow through a single solid layer.")

    c1, c2 = st.columns(2)
    with c1:
        k = st.number_input(
            "Thermal conductivity, k (W/m·K)", min_value=0.0, value=1.0, step=0.1,
            help="How well the wall material conducts heat. Concrete ≈1.0, brick ≈0.7, "
                 "fibreglass insulation ≈0.04, steel ≈50, copper ≈400"
        )
        A_wall = st.number_input("Cross-sectional area, A (m²)", min_value=0.0, value=2.0, step=0.1)
        L_wall = st.number_input("Wall thickness, L (m)", min_value=0.0, value=0.20, step=0.01)
    with c2:
        T1 = st.number_input("Hot-side surface temperature, T₁ (°C)", value=80.0)
        T2 = st.number_input("Cold-side surface temperature, T₂ (°C)", value=20.0)

    try:
        wall = PlaneWallConduction(k, A_wall, L_wall)
        Q_cond = wall.heat_rate(T1, T2)
        st.metric("Heat Transfer Rate, Q", f"{Q_cond:,.2f} W")
        if Q_cond < 0:
            st.warning("Q is negative — this means heat actually flows from side 2 to side 1 "
                       "(T₂ is hotter than T₁ as entered).")
    except ValueError as e:
        st.warning(f"⚠️ Invalid input: {e}")

# ----------------------------------------------------------------------------
# Tab 2: Newton's Law of Cooling
# ----------------------------------------------------------------------------
with tab2:
    st.subheader("Newton's Law of Cooling")
    st.caption(
        "Models the temperature of a body over time as it exchanges heat by convection "
        "with an ambient fluid: T(t) = T∞ + (T₀ − T∞)·e^(−t/τ), where τ = m·cp/(h·A)."
    )

    c1, c2 = st.columns(2)
    with c1:
        h = st.slider(
            "Convection coefficient, h (W/m²·K)", min_value=1.0, max_value=1000.0, value=15.0,
            help="How effectively the surrounding fluid removes heat. Still air ≈5-25, "
                 "forced air ≈25-250, water (natural) ≈100-1000, water (forced) ≈500-10000"
        )
        area_c = st.slider(
            "Surface area exposed to fluid, A (m²)", min_value=0.01, max_value=5.0, value=0.50, step=0.01
        )
        mass = st.slider("Mass of body, m (kg)", min_value=0.01, max_value=50.0, value=1.0, step=0.01)
        cp = st.slider(
            "Specific heat capacity, cp (J/kg·K)", min_value=100.0, max_value=5000.0, value=4186.0, step=10.0,
            help="Water ≈4186, steel ≈490, aluminium ≈900, air ≈1005"
        )
    with c2:
        T0 = st.slider("Initial body temperature, T₀ (°C)", min_value=-50.0, max_value=300.0, value=90.0,
                        help="The starting temperature of the body before it begins cooling/heating.")
        T_target = st.slider("Target temperature, T_target (°C)", min_value=-50.0, max_value=300.0, value=30.0,
                              help="The temperature you want the body to reach.")
        T_inf = st.slider("Ambient (surrounding fluid) temperature, T∞ (°C)", min_value=-50.0, max_value=300.0,
                           value=20.0, help="The constant temperature of the surrounding fluid far from the body.")

    try:
        cooler = NewtonCooling(h, area_c, mass, cp)
        t_needed = cooler.time_to_reach(T0, T_target, T_inf)
        st.metric("Time to reach target temperature", f"{t_needed:,.1f} s  ({t_needed/60:,.2f} min)")

        t_max = t_needed * 1.5 if t_needed > 0 else 100
        t_range = np.linspace(0, t_max, 150)
        T_range = [cooler.temperature_at(t, T0, T_inf) for t in t_range]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(t_range, T_range, color="#d62728", linewidth=2, label="Body temperature")
        ax.axhline(T_target, color="gray", linestyle="--", label=f"Target = {T_target}°C")
        ax.axhline(T_inf, color="lightblue", linestyle=":", label=f"Ambient = {T_inf}°C")
        ax.axvline(t_needed, color="green", linestyle=":", label=f"t = {t_needed:.1f} s")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("Temperature vs Time — Cooling Curve")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        st.pyplot(fig)

        st.markdown("#### Cooling Curve Data")
        df = pd.DataFrame({"Time (s)": t_range, "Temperature (C)": T_range})
        st.dataframe(df, use_container_width=True)

    except ValueError as e:
        st.warning(f"⚠️ Invalid input: {e}")
        st.info("Check that the target temperature lies strictly between the initial and "
                "ambient temperatures (e.g. cooling: T∞ < T_target < T₀).")
