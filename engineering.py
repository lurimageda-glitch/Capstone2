"""
engineering.py

Core engineering classes for the Fluid Flow & Heat Transfer Engineering Suite.

Provides:
- Fluid: fluid properties (density, viscosity), with presets for water/air/crude oil
- Pipe: circular pipe flow calculations (velocity, Reynolds number, friction factor,
  pressure drop via Darcy-Weisbach with the Swamee-Jain friction correlation)
- PlaneWallConduction: steady-state single-layer conduction (Fourier's law)
- NewtonCooling: transient lumped-capacitance cooling (Newton's Law of Cooling)

All classes validate their inputs and raise ValueError with a descriptive message
on invalid (non-physical) input, so calling UI code can catch ValueError and show
a warning instead of crashing.
"""

import math


class Fluid:
    """Represents a fluid with density and dynamic viscosity properties."""

    _PRESETS = {
        "water": {"density": 998.0, "viscosity": 0.001002},       # kg/m3, Pa.s @ ~20C
        "air": {"density": 1.204, "viscosity": 1.825e-5},         # kg/m3, Pa.s @ ~20C
        "crude oil": {"density": 870.0, "viscosity": 0.008},      # kg/m3, Pa.s (typical medium crude)
    }

    def __init__(self, name: str, density: float, viscosity: float):
        """Create a fluid.

        Args:
            name: display name of the fluid.
            density: fluid density in kg/m^3.
            viscosity: dynamic viscosity in Pa.s.

        Raises:
            ValueError: if density or viscosity is not a positive number.
        """
        if density is None or density <= 0:
            raise ValueError("Fluid density must be a positive number (kg/m3).")
        if viscosity is None or viscosity <= 0:
            raise ValueError("Fluid viscosity must be a positive number (Pa.s).")
        self.name = name
        self.density = float(density)
        self.viscosity = float(viscosity)

    @classmethod
    def from_name(cls, name: str, density: float = None, viscosity: float = None):
        """Build a Fluid from a preset name ('water', 'air', 'crude oil'), or from
        user-supplied density/viscosity for any other name (user-defined fluid).

        Raises:
            ValueError: if an unrecognised name is given without density/viscosity.
        """
        key = name.strip().lower()
        if key in cls._PRESETS:
            props = cls._PRESETS[key]
            return cls(name.title(), props["density"], props["viscosity"])
        if density is None or viscosity is None:
            raise ValueError(
                f"'{name}' is not a preset fluid. Provide density and viscosity for a user-defined fluid."
            )
        return cls(name, density, viscosity)

    def __repr__(self):
        return f"Fluid({self.name}, density={self.density} kg/m3, viscosity={self.viscosity} Pa.s)"


class Pipe:
    """Represents a circular pipe and provides steady, incompressible flow calculations."""

    def __init__(self, diameter: float, length: float, roughness: float):
        """
        Args:
            diameter: internal pipe diameter (m).
            length: pipe length (m).
            roughness: absolute (average) internal pipe roughness (m).

        Raises:
            ValueError: if diameter or length is not positive, or roughness is negative.
        """
        if diameter is None or diameter <= 0:
            raise ValueError("Pipe diameter must be a positive number (m).")
        if length is None or length <= 0:
            raise ValueError("Pipe length must be a positive number (m).")
        if roughness is None or roughness < 0:
            raise ValueError("Pipe roughness cannot be negative (m).")
        self.diameter = float(diameter)
        self.length = float(length)
        self.roughness = float(roughness)

    def area(self) -> float:
        """Cross-sectional flow area (m^2)."""
        return math.pi * (self.diameter ** 2) / 4.0

    def velocity(self, flow_rate: float) -> float:
        """Mean flow velocity (m/s) for a given volumetric flow rate (m^3/s).

        Raises:
            ValueError: if flow_rate is not positive.
        """
        if flow_rate is None or flow_rate <= 0:
            raise ValueError("Flow rate must be a positive number (m3/s).")
        return flow_rate / self.area()

    def reynolds_number(self, fluid: Fluid, flow_rate: float) -> float:
        """Reynolds number, Re = rho * v * D / mu, for the given fluid and flow rate."""
        v = self.velocity(flow_rate)
        return fluid.density * v * self.diameter / fluid.viscosity

    def friction_factor(self, fluid: Fluid, flow_rate: float) -> float:
        """Darcy (Moody) friction factor.

        Uses f = 64/Re for laminar flow (Re < 2300), and the Swamee-Jain explicit
        approximation to the Colebrook equation for turbulent flow (an explicit,
        non-iterative substitute that is accurate to within ~1% of Colebrook for
        4000 < Re < 1e8 and 1e-6 < relative roughness < 5e-2).
        """
        Re = self.reynolds_number(fluid, flow_rate)
        if Re < 2300:
            return 64.0 / Re
        rel_rough = self.roughness / self.diameter
        denom = math.log10(rel_rough / 3.7 + 5.74 / (Re ** 0.9))
        return 0.25 / (denom ** 2)

    def pressure_drop(self, fluid: Fluid, flow_rate: float) -> float:
        """Pressure drop (Pa) along the pipe length, via the Darcy-Weisbach equation:
        dP = f * (L/D) * (rho * v^2 / 2)
        """
        f = self.friction_factor(fluid, flow_rate)
        v = self.velocity(flow_rate)
        return f * (self.length / self.diameter) * (fluid.density * v ** 2 / 2.0)


class PlaneWallConduction:
    """Steady-state 1-D conduction through a single homogeneous flat wall (Fourier's law)."""

    def __init__(self, k: float, area: float, thickness: float):
        """
        Args:
            k: thermal conductivity of the wall material (W/m.K).
            area: cross-sectional area normal to the heat flow direction (m^2).
            thickness: wall thickness in the direction of heat flow (m).

        Raises:
            ValueError: if k, area, or thickness is not a positive number.
        """
        if k is None or k <= 0:
            raise ValueError("Thermal conductivity k must be a positive number (W/m.K).")
        if area is None or area <= 0:
            raise ValueError("Area must be a positive number (m2).")
        if thickness is None or thickness <= 0:
            raise ValueError("Wall thickness must be a positive number (m).")
        self.k = float(k)
        self.area = float(area)
        self.thickness = float(thickness)

    def heat_rate(self, T1: float, T2: float) -> float:
        """Steady-state conduction heat rate Q (W) via Fourier's law:
        Q = k * A * (T1 - T2) / L
        where T1 is the hot-side surface temperature and T2 the cold-side (same units, e.g. degC).
        A negative result means heat actually flows from side 2 to side 1.
        """
        return self.k * self.area * (T1 - T2) / self.thickness


class NewtonCooling:
    """Lumped-capacitance transient cooling/heating model (Newton's Law of Cooling)."""

    def __init__(self, h: float, area: float, mass: float, specific_heat: float):
        """
        Args:
            h: convective heat transfer coefficient between the body and ambient fluid (W/m2.K).
            area: surface area of the body exposed to the ambient fluid (m2).
            mass: mass of the cooling/heating body (kg).
            specific_heat: specific heat capacity of the body material (J/kg.K).

        Raises:
            ValueError: if any parameter is not a positive number.
        """
        if h is None or h <= 0:
            raise ValueError("Convection coefficient h must be a positive number (W/m2.K).")
        if area is None or area <= 0:
            raise ValueError("Surface area must be a positive number (m2).")
        if mass is None or mass <= 0:
            raise ValueError("Mass must be a positive number (kg).")
        if specific_heat is None or specific_heat <= 0:
            raise ValueError("Specific heat must be a positive number (J/kg.K).")
        self.h = float(h)
        self.area = float(area)
        self.mass = float(mass)
        self.specific_heat = float(specific_heat)

    def _tau(self) -> float:
        """Thermal time constant, tau = (m * cp) / (h * A), in seconds."""
        return (self.mass * self.specific_heat) / (self.h * self.area)

    def temperature_at(self, t: float, T0: float, T_inf: float) -> float:
        """Body temperature at time t (s), given initial temperature T0 and ambient T_inf:
        T(t) = T_inf + (T0 - T_inf) * exp(-t / tau)

        Raises:
            ValueError: if t is negative.
        """
        if t is None or t < 0:
            raise ValueError("Time must be a non-negative number (s).")
        return T_inf + (T0 - T_inf) * math.exp(-t / self._tau())

    def time_to_reach(self, T0: float, T_target: float, T_inf: float) -> float:
        """Time (s) required for the body to cool/heat from T0 to T_target in ambient T_inf.

        Raises:
            ValueError: if T0 equals T_inf (no driving force), if T_target is not strictly
                between T0 and T_inf, or if T_target equals T_inf (would take infinite time).
        """
        if T0 == T_inf:
            raise ValueError(
                "Initial temperature equals ambient temperature: there is no driving force for heat transfer."
            )
        lo, hi = sorted([T0, T_inf])
        if not (lo < T_target < hi):
            raise ValueError(
                "Target temperature must lie strictly between the initial and ambient temperatures."
            )
        ratio = (T_target - T_inf) / (T0 - T_inf)
        return -self._tau() * math.log(ratio)
