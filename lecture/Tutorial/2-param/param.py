import os

import numpy as np
import openmc

import psutil
cores = psutil.cpu_count(logical=False)

settings_obj = openmc.Settings(
    particles = 10_000,
    batches = 120,
    inactive = 20,
    temperature = {'method': 'interpolation'}
)

uo2 = openmc.Material(name="uo2")   #atomic
uo2.add_nuclide("U235", percent=0.2)
uo2.add_nuclide("U238", percent=0.8)
uo2.add_nuclide("O16",  percent=2.0)
iron = openmc.Material(name="iron")
iron.add_element("Fe", percent=1.0)

materials_obj  = openmc.Materials([uo2, iron])
# print(os.environ.get("$OPENMC_CROSS_SECTIONS"))
# materials_obj.cross_sections = os.environ.get("MSR_DAKOTA_XS_DATA")
materials_obj.cross_sections = "/home/harrison/data/openmc-xs/endfb-vii.1-hdf5/cross_sections.xml"

radii = np.linspace(0.1, 1.0, 10)

for idx, radius in enumerate(radii):
    case_name = f"case/{radius:.2F}"

    # Surfaces
    inner_surf  =  openmc.ZCylinder(name="inner", r=radius)
    outer_surf  =  openmc.ZCylinder(name="outer", r=2.0)
    top_surf    =  openmc.ZPlane(name="top", z0=10.0)
    bottom_surf =  openmc.ZPlane(name="bottom", z0=-10.0)

    # Regions
    center_region = -inner_surf & -top_surf & +bottom_surf
    wall_region   = +inner_surf & -outer_surf & -top_surf & +bottom_surf

    # Cells
    center_cell = openmc.Cell(name="center", region=center_region)
    center_cell.fill = uo2

    wall_cell = openmc.Cell(name="wall", region=wall_region)
    wall_cell.fill = iron

    # Boundary Conditions
    outer_surf.boundary_type = 'vacuum'
    top_surf.boundary_type = 'vacuum'
    bottom_surf.boundary_type = 'vacuum'

    # Root Universe
    root_universe = openmc.Universe(
        name="root_universe",
        cells=[center_cell, wall_cell]
    )

    # Geometry Object
    geometry_obj = openmc.Geometry(root_universe)



    # Define Model Object
    model = openmc.Model(
        geometry=geometry_obj,
        materials=materials_obj,
        settings = settings_obj
    )

    # Make a directory for the XML
    os.makedirs(f"./{case_name}", exist_ok=True)

    # Export the XML
    model.export_to_model_xml(f'./{case_name}/model.xml')

    # Run OpenMC
    openmc.run(
        threads=cores,
        cwd = case_name,
        path_input='./model.xml',
        geometry_debug=False
    )
