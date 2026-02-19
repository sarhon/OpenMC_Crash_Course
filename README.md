# OpenMC Crash Course

This project is a crash course for [OpenMC](https://openmc.org/).

## Installation

You can install this package in editable mode with:

```bash
pip install -e .
```

## Usage

After installation, you can run the crash course command:

```bash
openmc-crash-course
```

## Nuclear Reactor Theory Suite

This project includes a series of examples that build upon each other to teach nuclear reactor theory. You can find them in the `examples/` directory.

1.  **Infinite Medium**: Introduction to materials and $k_{\infty}$.
2.  **Infinite Pin Cell**: Introduction to geometry and spatial effects.
3.  **Finite Pin Cell**: Introduction to leakage and $k_{\text{eff}}$.
4.  **Fuel Assembly**: Introduction to lattices and universes.
5.  **Small Reactor Core**: Full system simulation.

To run an example:

```bash
cd examples/01_infinite_medium
python main.py
```

*Note: The examples are configured to use ENDF/B-VII.1 cross sections located at `/home/harrisonr/data/OpenMC_DATA/endfb-vii.1-hdf5/cross_sections.xml`. If your data is in a different location, please update the `openmc.config['cross_sections']` line in each `main.py` file or set the `OPENMC_CROSS_SECTIONS` environment variable.*
