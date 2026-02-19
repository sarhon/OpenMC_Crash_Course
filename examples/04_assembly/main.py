import openmc
import numpy as np
from pathlib import Path
import openmc_crash_course as occ

def run_assembly():
    """Step 4: Fuel Assembly.
    
    This example introduces:
    - Universes and Lattices
    - Complex geometry arrangement
    - Power distribution tallies
    """

    # 0. Setup directories
    script_dir = Path(__file__).parent
    xml_dir = script_dir / 'xml'
    output_dir = script_dir / 'output'
    xml_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # Configure Cross Sections
    import os
    default_xs = '/home/harrisonr/data/OpenMC_DATA/endfb-vii.1-hdf5/cross_sections.xml'
    openmc.config['cross_sections'] = os.environ.get('OPENMC_CROSS_SECTIONS', default_xs)

    # 1. Define Materials
    all_materials = occ.get_materials()
    uo2 = all_materials['uo2']
    zirc = all_materials['zirc']
    water = all_materials['water']

    materials = openmc.Materials([uo2, zirc, water])
    materials.cross_sections = openmc.config['cross_sections']
    materials.export_to_xml(xml_dir / 'materials.xml')

    # 2. Define Geometry
    pitch = 1.26
    size = 17
    wall_thickness = 0.2
    gap_thickness = 0.1
    assy_width = pitch * size + 2 * (wall_thickness + gap_thickness)
    
    # Create the assembly universe using the package helper
    # This automatically uses create_pin_cell_universe and create_assembly_lattice
    assy_univ = occ.create_assembly_universe(
        uo2, zirc, water, pitch, size, wall_thickness, gap_thickness
    )

    # Root geometry
    main_prism = openmc.model.RectangularPrism(width=assy_width, height=assy_width, boundary_type='reflective')
    main_cell = openmc.Cell(fill=assy_univ, region=-main_prism)
    
    root_universe = openmc.Universe(cells=[main_cell])
    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml(xml_dir / 'geometry.xml')

    # 3. Define Settings
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 1000
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box([-pitch*size/2, -pitch*size/2, -1], [pitch*size/2, pitch*size/2, 1]),
        constraints={'fissionable': True}
    )
    settings.run_mode = 'eigenvalue'
    settings.export_to_xml(xml_dir / 'settings.xml')

    # 4. Define Tallies
    # Tally power (fission rate) in each pin
    mesh = openmc.RegularMesh()
    mesh.dimension = [size, size]
    mesh.lower_left = [-pitch*size/2, -pitch*size/2]
    mesh.upper_right = [pitch*size/2, pitch*size/2]
    
    mesh_filter = openmc.MeshFilter(mesh)
    tally = openmc.Tally(name='pin_power')
    tally.filters = [mesh_filter]
    tally.scores = ['fission']
    
    tallies = openmc.Tallies([tally])
    tallies.export_to_xml(xml_dir / 'tallies.xml')

    # 5. Run OpenMC
    print("Running Assembly simulation...")
    openmc.run(cwd=xml_dir, output=False)

    # Move output files to output directory
    for file in xml_dir.glob('*.h5'):
        file.rename(output_dir / file.name)

if __name__ == "__main__":
    run_assembly()
