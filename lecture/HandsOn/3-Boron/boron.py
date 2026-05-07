import os

import numpy as np
import openmc

settings_obj = openmc.Settings(
    particles = 100_000,
    batches = 220,
    inactive = 20,
    # source_rejection_fraction = 0.01,
    temperature = {'method': 'interpolation'}
)

enrich_wo = 0.20  # 20 w/o U235 (HALEU)
u235_ao = (enrich_wo / 235) / (enrich_wo / 235 + (1 - enrich_wo) / 238)

uo2 = openmc.Material(name="uo2")
uo2.add_nuclide("U235", u235_ao)
uo2.add_nuclide("U238", 1.0 - u235_ao)
uo2.add_nuclide("O16",  2.0)
uo2.set_density("g/cm3", 10.4)          # ~95% theoretical density
uo2.temperature = 900.0                 # K, average fuel temperature at HFP

zr = openmc.Material(name="zr")
zr.add_element("Zr", 1.0)
zr.set_density("g/cm3", 6.55)
zr.temperature = 600.0                  # K, cladding temperature at HFP



# Surfaces
inner_radius = 1.03
thickness = 0.125
outer_radius = inner_radius + thickness
inner_surf  =  openmc.ZCylinder(name="inner", r=inner_radius)
outer_surf  =  openmc.ZCylinder(name="outer", r=outer_radius)
top_surf    =  openmc.ZPlane(name="top", z0=10.0)
bottom_surf =  openmc.ZPlane(name="bottom", z0=-10.0)

pitch = 5.0
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

# Cells
center_cell = openmc.Cell(name="center", region=center_region)
center_cell.fill = uo2

wall_cell = openmc.Cell(name="wall", region=wall_region)
wall_cell.fill = zr

# Boundary Conditions
world_negative_x.boundary_type = 'vacuum'
world_positive_x.boundary_type = 'vacuum'
world_negative_y.boundary_type = 'vacuum'
world_positive_y.boundary_type = 'vacuum'

top_surf.boundary_type = 'reflective'
bottom_surf.boundary_type = 'reflective'

# Initial Source — neutrons distributed across all fuel pins
source = openmc.IndependentSource(
    space=openmc.stats.Box(
        lower_left=(-half_num_cell_xy * pitch, -half_num_cell_xy * pitch, -10.0),
        upper_right=( half_num_cell_xy * pitch,  half_num_cell_xy * pitch,  10.0),
    ),
    constraints={'fissionable': True},
    energy=openmc.stats.Watt(),
    particle='neutron'
)
settings_obj.source = [source]

pure_water = openmc.Material()
pure_water.add_nuclide("H1",  2.0)
pure_water.add_nuclide("O16", 1.0)
pure_water.set_density("g/cm3", 0.71)

boric_acid = openmc.Material()
boric_acid.add_nuclide("H1",  3.0)
boric_acid.add_nuclide("O16", 3.0)
boric_acid.add_element("B",   1.0)
boric_acid.set_density("g/cm3", 1.44)

# Geometry — moderator_cell.fill is the only thing that changes per case
moderator_cell = openmc.Cell(name="moderator", region=moderator_region)

uu = openmc.Universe(
    name="unit_universe",
    cells=[center_cell, wall_cell, moderator_cell],
)

lattice = openmc.RectLattice()
lattice.lower_left = (-half_num_cell_xy*pitch, -half_num_cell_xy*pitch)
lattice.pitch = (pitch, pitch)
lattice.universes = [
    [uu for _ in range(num_cell_xy)]
    for _ in range(num_cell_xy)
]

world_cell = openmc.Cell(name="world", region=world_region)
world_cell.fill = lattice

root_universe = openmc.Universe(name="root_universe", cells=[world_cell])
geometry_obj = openmc.Geometry(root_universe)

# Moderator Absorption Rate Tally (single scalar — sum over all moderator cells)
moderator_abs_tally = openmc.Tally(name="moderator_absorption")
moderator_abs_tally.filters = [openmc.CellFilter([moderator_cell.id])]
moderator_abs_tally.scores = ["absorption"]
tallies_obj = openmc.Tallies([moderator_abs_tally])

import psutil
cores = psutil.cpu_count(logical=False)

borons = np.linspace(500, 1300, 9)
for boron_ppm in borons:
    concentration = boron_ppm * 1e-6 * (61.832 / 10.811)  # ppm B → H3BO3 weight fraction

    water = openmc.Material.mix_materials(
        [pure_water, boric_acid],
        [1.0 - concentration, concentration],
        'wo',
        name="borated_water"
    )
    water.set_density("g/cm3", 0.71)  # at ~155 bar, ~580 K
    water.temperature = 580.0         # K, average coolant temperature at HFP
    water.add_s_alpha_beta("c_H_in_H2O")

    moderator_cell.fill = water

    materials_obj = openmc.Materials([uo2, zr, water])
    materials_obj.cross_sections = "/home/harrison/data/openmc-xs/endfb-vii.1-hdf5/cross_sections.xml"

    model = openmc.Model(
        geometry=geometry_obj,
        materials=materials_obj,
        settings=settings_obj,
        tallies=tallies_obj
    )

    case_name = f"case/{boron_ppm}"
    os.makedirs(f'./{case_name}', exist_ok=True)
    model.export_to_model_xml(f'./{case_name}/model.xml')

    print('Running', case_name)
    openmc.run(
        threads=cores,
        cwd=f'./{case_name}/',
        path_input='./model.xml',
        geometry_debug=False,
        output=False
    )
