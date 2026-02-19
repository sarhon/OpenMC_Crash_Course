# OpenMC Crash Course: Nuclear Reactor Theory Suite

This directory contains a series of examples that build upon each other to teach nuclear reactor theory using OpenMC.

## Logical Progression

1.  **Infinite Medium (`01_infinite_medium/main.py`)**: 
    - Introduction to Materials, Cross Sections, and basic tallies.
    - Calculating $k_{\infty}$ and looking at energy-dependent fluxes.
2.  **Infinite Pin Cell (`02_infinite_pincell/main.py`)**:
    - Introduction to Geometry (Surfaces, Cells, Universes).
    - Periodic boundary conditions.
    - Understanding resonance escape and spatial self-shielding.
3.  **Finite Pin Cell (`03_finite_pincell/main.py`)**:
    - Vacuum boundary conditions and leakage.
    - Calculating $k_{\text{eff}}$ vs $k_{\infty}$ ($L$).
4.  **Fuel Assembly (`04_assembly/main.py`)**:
    - Complex geometries using Universes and Lattices.
    - Power distribution and local peaking.
5.  **Small Reactor Core (`05_core/main.py`)**:
    - Putting it all together: multiple assemblies, reflector, and criticality search.
