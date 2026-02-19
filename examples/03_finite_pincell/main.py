import openmc
import numpy as np
from pathlib import Path
import openmc_crash_course as occ

def run_finite_pincell():
    """Step 3: Finite Pin Cell.
    
    This example introduces:
    - Vacuum boundary conditions
    - Leakage and k-effective
    - Difference between k-inf and k-eff
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
    height = 100.0
    geometry = occ.create_finite_pincell_geometry(uo2, zirc, water, pitch, height)
    geometry.export_to_xml(xml_dir / 'geometry.xml')

    # 3. Define Settings
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 1000
    
    # Starting source uniformly distributed in the fuel
    lower_left = (-pitch/2, -pitch/2, -height/2)
    upper_right = (pitch/2, pitch/2, height/2)
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box(lower_left, upper_right),
        constraints={'fissionable': True}
    )
    settings.run_mode = 'eigenvalue'
    settings.export_to_xml(xml_dir / 'settings.xml')

    # 4. Define Tallies
    # Tally the total leakage
    leakage_tally = openmc.Tally(name='leakage')
    
    # Find the boundary surfaces by name
    surfaces = {s.name: s for s in geometry.get_all_surfaces().values()}
    boundary_surfaces = [
        surfaces['min_x'], surfaces['max_x'],
        surfaces['min_y'], surfaces['max_y'],
        surfaces['z_min'], surfaces['z_max']
    ]
    
    surface_filter = openmc.SurfaceFilter(boundary_surfaces)
    leakage_tally.filters = [surface_filter]
    leakage_tally.scores = ['current']
    
    # We also want to tally the absorption to calculate k-inf manually if desired
    abs_tally = openmc.Tally(name='absorption')
    abs_tally.scores = ['absorption', 'fission']
    
    tallies = openmc.Tallies([leakage_tally, abs_tally])
    tallies.export_to_xml(xml_dir / 'tallies.xml')

    # 5. Run OpenMC
    print("Running Finite Pin Cell simulation...")
    openmc.run(cwd=xml_dir, output=False)

    # Move output files to output directory
    for file in xml_dir.glob('*.h5'):
        file.rename(output_dir / file.name)

if __name__ == "__main__":
    run_finite_pincell()
