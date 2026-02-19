# OpenMC Crash Course

This project is a crash course for [OpenMC](https://openmc.org/).

## Prerequisites

### Nuclear Data

OpenMC requires nuclear cross section data to run. You must download and configure cross sections before running any examples.

#### Download Cross Sections

Download pre-generated nuclear data libraries from the official OpenMC website [here](https://openmc.org/data/).

Available libraries include:
- **ENDF/B-VII.1** (recommended, ~2 GB) - Most widely used and validated
- **ENDF/B-VIII.0** (~2.5 GB) - Newer evaluations with improvements
- **JEFF-3.3** - European joint evaluated data
- **TENDL** - TALYS-based evaluated data

**Steps:**
1. Download the archive file (`.tar.gz` or `.zip`) for your chosen library
2. Extract it to a location of your choice (e.g., `~/data/OpenMC_DATA/`)
   ```bash
   tar -xzf endfb-vii.1-hdf5.tar.gz -C ~/data/OpenMC_DATA/
   ```

#### Configure Environment Variable

Set the `OPENMC_CROSS_SECTIONS` environment variable to point to the `cross_sections.xml` file in your extracted library:

```bash
# For bash/zsh (add to ~/.bashrc or ~/.zshrc for persistence)
export OPENMC_CROSS_SECTIONS=~/data/OpenMC_DATA/endfb-vii.1-hdf5/cross_sections.xml

# For fish (add to ~/.config/fish/config.fish)
set -x OPENMC_CROSS_SECTIONS ~/data/OpenMC_DATA/endfb-vii.1-hdf5/cross_sections.xml
```

**Important:** Replace the path above with the actual location where you extracted the data.

#### Managing Multiple Cross Section Libraries (Optional)

If you have multiple cross section versions, this repository includes a convenient configuration file:

```bash
# 1. Copy the template
cp .openmc_xs_config.sh.template .openmc_xs_config.sh

# 2. Edit .openmc_xs_config.sh and update OPENMC_DATA_DIR to your path

# 3a. Source it manually each time you need it (temporary, per-session):
source .openmc_xs_config.sh
xs-endfb71    # Select your library

# OR

# 3b. Add to your shell config file (persistent, loads automatically):
# For zsh (most common on macOS, also used with Oh My Zsh):
echo "source $(pwd)/.openmc_xs_config.sh" >> ~/.zshrc
echo "xs-endfb71    # Set default library" >> ~/.zshrc
source ~/.zshrc

# OR for bash (Linux/WSL):
echo "source $(pwd)/.openmc_xs_config.sh" >> ~/.bashrc
echo "xs-endfb71    # Set default library" >> ~/.bashrc
source ~/.bashrc
```

**Using the library switcher:**

```bash
xs-endfb71    # Switch to ENDF/B-VII.1
xs-endfb80    # Switch to ENDF/B-VIII.0
xs-tendl      # Switch to TENDL 2017
xs-show       # Show current library
```

Or manually set it in each terminal session:

```bash
export OPENMC_CROSS_SECTIONS=~/data/OpenMC_DATA/endfb-vii.1-hdf5/cross_sections.xml
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
