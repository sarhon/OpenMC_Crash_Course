import openmc
import numpy as np
from pathlib import Path
import openmc_crash_course as occ

def run_infinite_pincell():
    """Step 2: Infinite Pin Cell.
    
    This example introduces:
    - Surfaces and Cells
    - Periodic boundary conditions
    - Multi-material cells and universes
    """

    # 0. Setup directories
    script_dir = Path(__file__).parent
    xml_dir = script_dir / 'xml'
    output_dir = script_dir / 'output'
    xml_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # Configure Cross Sections
    # OpenMC will automatically use the OPENMC_CROSS_SECTIONS environment variable
    # If not set, you'll get an error - see README.md for setup instructions

    # 1. Define Materials
    all_materials = occ.get_materials()
    uo2 = all_materials['uo2']
    zirc = all_materials['zirc']
    water = all_materials['water']

    materials = openmc.Materials([uo2, zirc, water])
    materials.export_to_xml(xml_dir / 'materials.xml')

    # 2. Define Geometry
    pitch = 1.26
    geometry = occ.create_infinite_pincell_geometry(uo2, zirc, water, pitch)
    geometry.export_to_xml(xml_dir / 'geometry.xml')

    # Get cells for tallies
    cells = {cell.name: cell for cell in geometry.get_all_cells().values()}
    fuel = cells['fuel']
    moderator = cells['moderator']

    # 3. Define Settings
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 1000
    
    # Starting source uniformly distributed in the fuel
    lower_left = (-pitch/2, -pitch/2, -1e6)
    upper_right = (pitch/2, pitch/2, 1e6)
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(lower_left, upper_right),
        constraints={'fissionable': True}
    )
    settings.run_mode = 'eigenvalue'
    settings.export_to_xml(xml_dir / 'settings.xml')

    # 4. Define Tallies
    # Let's tally the flux in the fuel vs moderator to see self-shielding
    fuel_filter = openmc.CellFilter([fuel])
    moderator_filter = openmc.CellFilter([moderator])
    energy_filter = openmc.EnergyFilter(np.logspace(-3, 7, 101))

    fuel_tally = openmc.Tally(name='fuel_flux')
    fuel_tally.filters = [fuel_filter, energy_filter]
    fuel_tally.scores = ['flux']

    mod_tally = openmc.Tally(name='mod_flux')
    mod_tally.filters = [moderator_filter, energy_filter]
    mod_tally.scores = ['flux']

    tallies = openmc.Tallies([fuel_tally, mod_tally])
    tallies.export_to_xml(xml_dir / 'tallies.xml')

    # 5. Run OpenMC
    print("Running Infinite Pin Cell simulation...")
    openmc.run(cwd=xml_dir, output=False)

    # Move output files to output directory
    for file in xml_dir.glob('*.h5'):
        file.rename(output_dir / file.name)

if __name__ == "__main__":
    run_infinite_pincell()
