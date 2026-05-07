import os

import openmc

settings_obj = openmc.Settings(
    particles = 100_000,
    batches = 120,
    inactive = 20,
    # source_rejection_fraction = 0.01,
    temperature = {'method': 'interpolation'}
)

uo2 = openmc.Material(name="uo2")   #atomic
uo2.add_nuclide("U235", percent=0.2)
uo2.add_nuclide("U238", percent=0.8)
uo2.add_nuclide("O16",  percent=2.0)

iron = openmc.Material(name="iron")
iron.add_element("Fe", percent=1.0)

water = openmc.Material(name="water")
water.add_nuclide("H1", percent=1.0)
water.add_nuclide("O16", percent=2.0)

materials_obj  = openmc.Materials([uo2, iron, water])
# print(os.environ.get("$OPENMC_CROSS_SECTIONS"))
# materials_obj.cross_sections = os.environ.get("MSR_DAKOTA_XS_DATA")
materials_obj.cross_sections = "/home/harrison/data/openmc-xs/endfb-vii.1-hdf5/cross_sections.xml"

# Surfaces
inner_surf  =  openmc.ZCylinder(name="inner", r=0.25)
outer_surf  =  openmc.ZCylinder(name="outer", r=0.3125)
top_surf    =  openmc.ZPlane(name="top", z0=10.0)
bottom_surf =  openmc.ZPlane(name="bottom", z0=-10.0)

pitch = 1.0
half_pitch = 0.5 * pitch
unit_positive_x  =   openmc.XPlane(half_pitch)
unit_negative_x  =  openmc.XPlane(-half_pitch)
unit_positive_y  =   openmc.YPlane(half_pitch)
unit_negative_y  =  openmc.YPlane(-half_pitch)

num_cell_xy = 9
half_num_cell_xy = num_cell_xy * 0.5

world_positive_x  =   openmc.XPlane(half_num_cell_xy*pitch)
world_negative_x  =  openmc.XPlane(-half_num_cell_xy*pitch)
world_positive_y  =   openmc.YPlane(half_num_cell_xy*pitch)
world_negative_y  =  openmc.YPlane(-half_num_cell_xy*pitch)

# Regions
center_region    = -inner_surf & -top_surf & +bottom_surf
wall_region      = +inner_surf & -outer_surf & -top_surf & +bottom_surf
moderator_region = +outer_surf & -unit_positive_x & +unit_negative_x & -unit_positive_y & +unit_negative_y & -top_surf & +bottom_surf
world_region     = +world_negative_x & -world_positive_x & +world_negative_y & -world_positive_y & -top_surf & +bottom_surf

# Set starting neutron source to all fissionable materials
# settings_obj.source = openmc.IndependentSource(
#     space=openmc.stats.Box(
#         (-half_num_cell_xy*pitch, -half_num_cell_xy*pitch, -10.0),
#         (half_num_cell_xy*pitch, half_num_cell_xy*pitch, 10.0),
#     ),
#     constraints={'fissionable': True},
# )

# Cells
center_cell = openmc.Cell(name="center", region=center_region)
center_cell.fill = uo2

wall_cell = openmc.Cell(name="wall", region=wall_region)
wall_cell.fill = iron

moderator_cell = openmc.Cell(name="moderator", region=moderator_region)
moderator_cell.fill = water

# Boundary Conditions
world_negative_x.boundary_type = 'vacuum'
world_positive_x.boundary_type = 'vacuum'
world_negative_y.boundary_type = 'vacuum'
world_positive_y.boundary_type = 'vacuum'

top_surf.boundary_type = 'reflective'
bottom_surf.boundary_type = 'reflective'

# Unit Universe
uu = openmc.Universe(
    name="unit_universe",
    cells=[center_cell, wall_cell, moderator_cell],
)

# Lattice Definition
lattice = openmc.RectLattice()
lattice.lower_left = (-half_num_cell_xy*pitch, -half_num_cell_xy*pitch)
lattice.pitch = (pitch, pitch)
lattice.universes = [
    [uu for _ in range(num_cell_xy)]
    for _ in range(num_cell_xy)
]

world_cell = openmc.Cell(name="world", region=world_region)
world_cell.fill = lattice

root_universe = openmc.Universe(
    name="root_universe",
    cells=[world_cell],
)

# Geometry Object
geometry_obj = openmc.Geometry(root_universe)

# Flux Mesh
flux_mesh = openmc.RegularMesh()
flux_mesh.dimension = (100, 100, 1)
flux_mesh.lower_left = (-half_num_cell_xy*pitch, -half_num_cell_xy*pitch, -10.0)
flux_mesh.upper_right = (half_num_cell_xy*pitch, half_num_cell_xy*pitch, 10.0)

# Flux Map Tally
flux_tally = openmc.Tally(name="flux_map")
flux_tally.filters = [openmc.MeshFilter(flux_mesh)]
flux_tally.scores = ["flux"]

# Three Group Flux Map Tally
energy_filter = openmc.EnergyFilter([0.0, 0.625, 100_000.0, 20_000_000.0])

group_flux_tally = openmc.Tally(name="three_group_flux_map")
group_flux_tally.filters = [openmc.MeshFilter(flux_mesh), energy_filter]
group_flux_tally.scores = ["flux"]

# Tallies Object
tallies_obj = openmc.Tallies([flux_tally, group_flux_tally])

# Define Model Object
model = openmc.Model(
    geometry=geometry_obj,
    materials=materials_obj,
    settings = settings_obj,
    tallies=tallies_obj
)

# Make a directory for the XML
case_name="tallies_case"
os.makedirs(f'./{case_name}', exist_ok=True)

# Export the XML
model.export_to_model_xml(f'./{case_name}/model.xml')

import psutil
cores = psutil.cpu_count(logical=False)
openmc.run(
    threads=cores,
    cwd = f'./{case_name}/',
    path_input='./model.xml',
    geometry_debug=False
)
