# Fluid Flow & Heat Transfer Engineering Suite

A multi-page Streamlit application providing three engineering calculation and analysis modules: a **Pipe Flow Analyser** (Darcy-Weisbach pressure drop, Reynolds number, and friction factor for pipe flow with fluid selection and CSV export), a **Heat Transfer Calculator** (steady-state Fourier conduction through a flat wall, and transient Newton's-Law-of-Cooling with an interactive cooling curve), and a **Rock & Fluid Data Dashboard** (CSV upload, summary statistics, porosity filtering, histogram and porosity-permeability crossplot, and filtered-CSV download). All engineering formulas are implemented as documented, input-validated OOP classes in `engineering.py`, imported by each page, with error handling throughout so invalid inputs show a warning instead of crashing the app.

**Live app:** [PASTE YOUR STREAMLIT CLOUD URL HERE AFTER DEPLOYING]

## Project structure
```
engineering.py                        # Fluid, Pipe, PlaneWallConduction, NewtonCooling classes
Home.py                               # Main entry point / landing page
pages/
  1_Pipe_Flow_Analyser.py             # Module A
  2_Heat_Transfer_Calculator.py       # Module B
  3_Rock_Fluid_Dashboard.py           # Module C
requirements.txt
```

## Running locally
```
pip install -r requirements.txt
streamlit run Home.py
```
