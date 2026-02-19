import openmc
from pathlib import Path
import openmc_crash_course as occ

def run_core():
    """Step 5: Reactor Core.
    
    This example introduces:
    - Large-scale core with ~177 fuel assemblies in a circular layout
    - Cylindrical steel reactor vessel (barrel)
    - Air region outside the vessel with square vacuum boundaries
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
    steel = all_materials['steel']
    air = all_materials['air']

    materials = openmc.Materials([uo2, zirc, water, steel, air])
    materials.export_to_xml(xml_dir / 'materials.xml')

    # 2. Define Geometry
    pitch = 1.26
    assy_size = 17
    wall_thickness = 0.2
    gap_thickness = 0.1
    barrel_thickness = 5.0
    assy_pitch = (pitch * assy_size) + 2 * (wall_thickness + gap_thickness)

    # Generate a circular core map targeting ~177 assemblies
    target_assemblies = 177
    grid_size = 17  # 17x17 grid is large enough to hold ~177 in a circle
    core_map, barrel_ir = occ.generate_circular_core_map(
        grid_size, assy_pitch, target_assemblies
    )
    num_assy = sum(sum(row) for row in core_map)
    print(f"Core layout: {grid_size}x{grid_size} grid with {num_assy} fuel assemblies")
    print(f"Barrel inner radius: {barrel_ir:.1f} cm")

    # Create the full core geometry with steel barrel and air
    geometry = occ.create_core_geometry(
        uo2, zirc, water, steel, air,
        core_map, pitch, assy_size,
        wall_thickness, gap_thickness,
        barrel_ir=barrel_ir, barrel_thickness=barrel_thickness
    )
    geometry.export_to_xml(xml_dir / 'geometry.xml')

    # 3. Define Settings
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 10
    settings.particles = 1000
    settings.source = openmc.IndependentSource(space=openmc.stats.Point((0, 0, 0)))
    settings.run_mode = 'eigenvalue'
    settings.export_to_xml(xml_dir / 'settings.xml')

    # 4. Define Tallies
    barrel_or = barrel_ir + barrel_thickness
    world_half = barrel_or + 10.0
    mesh = openmc.RegularMesh()
    mesh.dimension = [100, 100]
    mesh.lower_left = [-world_half, -world_half]
    mesh.upper_right = [world_half, world_half]

    mesh_filter = openmc.MeshFilter(mesh)
    tally = openmc.Tally(name='core_flux')
    tally.filters = [mesh_filter]
    tally.scores = ['flux']

    tallies = openmc.Tallies([tally])
    tallies.export_to_xml(xml_dir / 'tallies.xml')

    # 5. Run OpenMC
    print("Running Core simulation...")
    openmc.run(cwd=xml_dir, output=False)

    # Move output files to output directory
    for file in xml_dir.glob('*.h5'):
        file.rename(output_dir / file.name)

if __name__ == "__main__":
    run_core()
