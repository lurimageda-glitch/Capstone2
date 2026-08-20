"""
pages/2_Heat_Transfer_Calculator.py
=====================================
Module B: Heat Transfer Calculator.

Two calculations:
  1. Steady-state 1-D conduction through a single-layer flat wall
     (Fourier's Law) -- `engineering.PlaneWall`.
  2. Newton's Law of Cooling: time to cool an object from T0 to a target
     temperature in an ambient fluid, plus a live temperature-vs-time
     cooling curve -- `engineering.NewtonCooling`.

UI only lives here; the physics lives in engineering.py.
"""

import numpy as np
import pandas as pd
import streamlit as st

from engineering import NewtonCooling, PlaneWall

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🔥", layout="wide")
st.title("🔥 Module B — Heat Transfer Calculator")

tab1, tab2 = st.tabs(["🧱 Conduction through a flat wall", "🌡️ Newton's Law of Cooling"])

# ---------------------------------------------------------------------------
# TAB 1 — Steady-state conduction (Fourier's Law)
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Steady-state conduction through a flat wall")
    st.write(
        "Fourier's Law for a single, homogeneous layer at steady state: "
        "heat flows from the hot face to the cold face at a rate that "
        "depends on the material's conductivity, the wall's geometry, "
        "and the temperature difference across it."
    )

    colL, colR = st.columns(2)
    with colL:
        thickness_cm = st.number_input(
            "Wall thickness, L (cm)",
            min_value=0.1, value=10.0, step=0.5,
            help="Distance the heat has to travel through the material, from hot face to cold face.",
        )
        area_m2 = st.number_input(
            "Wall area, A (m^2)",
            min_value=0.01, value=2.0, step=0.1,
            help="Cross-sectional area of the wall, perpendicular to the direction of heat flow.",
        )
    with colR:
        k = st.number_input(
            "Thermal conductivity, k (W/m.K)",
            min_value=0.001, value=0.8, step=0.05,
            help="Material property. Examples: brick ~0.7, glass ~1.0, "
                 "wood ~0.15, steel ~45, still air ~0.026 (all W/m.K).",
        )
        t_hot = st.number_input("Hot-side surface temperature, T_hot (deg C)", value=25.0, step=1.0)
        t_cold = st.number_input("Cold-side surface temperature, T_cold (deg C)", value=5.0, step=1.0)

    try:
        wall = PlaneWall(thickness_cm / 100.0, area_m2, k)
        q = wall.heat_rate(t_hot, t_cold)
        r = wall.thermal_resistance()

        m1, m2 = st.columns(2)
        m1.metric("Heat transfer rate, Q", f"{q:.2f} W")
        m2.metric("Thermal resistance, R", f"{r:.4f} K/W")

        if q < 0:
            st.warning(
                "Q is negative, meaning heat is actually flowing from the "
                "'cold' side to the 'hot' side as you've defined them -- "
                "double-check which face is warmer."
            )
    except ValueError as err:
        st.error(f"Input error: {err}")

    with st.expander("ℹ️ How this is calculated"):
        st.markdown(
            r"""
Fourier's Law (single layer, steady state):
$$Q = k \, A \, \frac{T_{hot} - T_{cold}}{L}$$

Thermal resistance analogy (like Ohm's Law for heat):
$$R = \frac{L}{k A}, \qquad Q = \frac{T_{hot}-T_{cold}}{R}$$
            """
        )

# ---------------------------------------------------------------------------
# TAB 2 — Newton's Law of Cooling
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Newton's Law of Cooling (lumped-capacitance model)")
    st.write(
        "Models an object that is small/conductive enough to be treated "
        "as a single uniform temperature (a 'lump'), losing heat to a "
        "cooler ambient fluid by convection. Good for small, well-stirred "
        "or highly conductive objects; a poor model for large solids with "
        "strong internal temperature gradients."
    )

    colA, colB = st.columns(2)
    with colA:
        t0 = st.number_input(
            "Initial temperature, T0 (deg C)", value=90.0, step=1.0,
            help="Temperature of the object at time t = 0.",
        )
        t_inf = st.number_input(
            "Ambient temperature, T_inf (deg C)", value=20.0, step=1.0,
            help="Temperature of the surrounding fluid, far from the object -- what it will eventually reach.",
        )
        t_target = st.slider(
            "Target temperature, T_target (deg C)",
            min_value=float(min(t0, t_inf) + 0.1),
            max_value=float(max(t0, t_inf) - 0.1),
            value=float((t0 + t_inf) / 2),
            help="Temperature you want to know the time-to-reach for. Must be strictly between T_inf and T0.",
        )
    with colB:
        h = st.number_input(
            "Convective coefficient, h (W/m^2.K)",
            min_value=0.1, value=15.0, step=1.0,
            help="How effectively the ambient fluid carries heat away. "
                 "Examples: still air ~5-25, forced air ~25-250, water ~500-10000 (all W/m^2.K).",
        )
        area_cool_m2 = st.number_input(
            "Surface area exposed to fluid, A (m^2)",
            min_value=0.001, value=0.05, step=0.01,
            help="Total surface area through which the object loses heat to the ambient fluid.",
        )
        mass_kg = st.number_input(
            "Object mass, m (kg)", min_value=0.001, value=0.5, step=0.05,
            help="Mass of the object being cooled.",
        )
        c_p = st.number_input(
            "Specific heat, c (J/kg.K)", min_value=1.0, value=450.0, step=10.0,
            help="Material property. Examples: water 4186, aluminium ~900, steel ~450, glass ~840 (all J/kg.K).",
        )

    try:
        model = NewtonCooling(h, area_cool_m2, mass_kg, c_p)
        tau = model.tau
        t_reach = model.time_to_reach(t0, t_inf, t_target)

        m1, m2 = st.columns(2)
        m1.metric("Thermal time constant, tau", f"{tau:.1f} s ({tau/60:.2f} min)")
        m2.metric(f"Time to reach {t_target:.1f} deg C", f"{t_reach:.1f} s ({t_reach/60:.2f} min)")

        st.markdown("**Cooling curve**")
        t_end = st.slider(
            "Plot duration (multiples of the time constant, tau)",
            min_value=1.0, max_value=8.0, value=4.0, step=0.5,
        )
        time_vals = np.linspace(0, t_end * tau, 200)
        temp_vals = [model.temperature_at(t0, t_inf, t) for t in time_vals]
        curve_df = pd.DataFrame({"Time (s)": time_vals, "Temperature (deg C)": temp_vals})
        st.line_chart(curve_df, x="Time (s)", y="Temperature (deg C)")
        st.caption(
            "The curve updates live as you move any slider or input above -- "
            "it is recomputed from the current tau and target every rerun."
        )

    except ValueError as err:
        st.error(f"Input error: {err}")

    with st.expander("ℹ️ How this is calculated"):
        st.markdown(
            r"""
Lumped-capacitance energy balance: $m c \dfrac{dT}{dt} = -hA(T - T_\infty)$

Solution:
$$T(t) = T_\infty + (T_0 - T_\infty)\, e^{-t/\tau}, \qquad \tau = \frac{mc}{hA}$$

Time to reach a target temperature (solve the above for $t$):
$$t = -\tau \ln\left(\frac{T_{target}-T_\infty}{T_0-T_\infty}\right)$$
            """
        )
