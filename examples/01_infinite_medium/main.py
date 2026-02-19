import openmc
import numpy as np
from pathlib import Path
import openmc_crash_course as occ

def run_infinite_medium():
    """Step 1: Infinite Medium - Calculating k-infinity.
    
    This example introduces:
    - Defining materials
    - Setting up an infinite geometry
    - Running a criticality calculation
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
    water = all_materials['water']

    # Combine into materials collection
    materials = openmc.Materials([uo2, water])
    materials.export_to_xml(xml_dir / 'materials.xml')

    # 2. Define Geometry
    # In an infinite medium, we just have one cell that covers all space
    # and has reflective (or periodic) boundary conditions.
    
    # Create a box with reflective boundaries
    prism = openmc.model.RectangularPrism(width=10, height=10, boundary_type='reflective')
    z_min = openmc.ZPlane(z0=-5, boundary_type='reflective')
    z_max = openmc.ZPlane(z0=5, boundary_type='reflective')
    
    # Define fuel region as the prism
    fuel_cell = openmc.Cell(fill=uo2, region=-prism & +z_min & -z_max)
    
    # Geometry setup
    root_universe = openmc.Universe(cells=[fuel_cell])
    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml(xml_dir / 'geometry.xml')

    # 3. Define Settings
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 1000
    
    # Starting source in the center
    settings.source = openmc.IndependentSource(space=openmc.stats.Point((0, 0, 0)))
    settings.run_mode = 'eigenvalue'
    settings.export_to_xml(xml_dir / 'settings.xml')

    # 4. (Optional) Define Tallies
    # Let's tally the flux by energy
    tally = openmc.Tally(name='flux_tally')
    energy_filter = openmc.EnergyFilter(np.logspace(-3, 7, 101))
    tally.filters = [energy_filter]
    tally.scores = ['flux']

    tallies = openmc.Tallies([tally])
    tallies.export_to_xml(xml_dir / 'tallies.xml')

    # 5. Run OpenMC
    print("Running Infinite Medium simulation...")
    openmc.run(cwd=xml_dir, output=False)

    # Move output files to output directory
    for file in xml_dir.glob('*.h5'):
        file.rename(output_dir / file.name)

if __name__ == "__main__":
    run_infinite_medium()
