# OpenMC Crash Course

This project is a crash course for [OpenMC](https://openmc.org/).

## Prerequisites

### Nuclear Data

OpenMC requires nuclear cross section data to run. You must download and configure cross sections before running any examples.

#### Download Cross Sections

The easiest way to get cross section data is using the official OpenMC script:

```bash
# Download ENDF/B-VII.1 data (recommended, ~2 GB)
openmc-get-nndc-data

# Or for ENDF/B-VIII.0 data (~2.5 GB)
openmc-get-endf-data
```

This will download the data to `~/.local/share/openmc/` by default.

#### Configure Environment Variable

Set the `OPENMC_CROSS_SECTIONS` environment variable to point to your `cross_sections.xml` file:

```bash
# For bash/zsh (add to ~/.bashrc or ~/.zshrc for persistence)
export OPENMC_CROSS_SECTIONS=~/.local/share/openmc/cross_sections.xml

# For fish (add to ~/.config/fish/config.fish)
set -x OPENMC_CROSS_SECTIONS ~/.local/share/openmc/cross_sections.xml
```

Or if you downloaded data to a custom location:

```bash
export OPENMC_CROSS_SECTIONS=/path/to/your/cross_sections.xml
```

**Verify your setup:**

```bash
echo $OPENMC_CROSS_SECTIONS  # Should print the path to cross_sections.xml
```

## Installation

Install this package in editable mode:

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
