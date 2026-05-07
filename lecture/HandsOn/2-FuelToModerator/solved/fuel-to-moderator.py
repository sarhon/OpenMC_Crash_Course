import os

import numpy as np
import openmc
import psutil

cores = psutil.cpu_count(logical=False)

leu = openmc.Material(name='leu')
enrichment = 0.10
leu.add_nuclide('U235', enrichment, percent_type='wo')
leu.add_nuclide('U238', 1.0 - enrichment, percent_type='wo')
leu.set_density('g/cm3', 10.0)
leu.temperature = 900 # K

moderator = openmc.Material(name='moderator')
moderator.add_nuclide('H1', 2.0, percent_type='ao')
moderator.add_nuclide('O16', 1.0, percent_type='ao')
moderator.set_density('g/cm3', 1.0)
moderator.temperature = 900 # K

materials = openmc.Materials([leu, moderator])
materials.cross_sections = "/home/harrison/data/openmc-xs/endfb-vii.1-hdf5/cross_sections.xml"

settings = openmc.Settings()
settings.batches = 220
settings.inactive = 20
settings.particles = 10_000
settings.run_mode = 'eigenvalue'
settings.temperature = {'method': 'interpolation'}

fuel_to_moderators = np.linspace(0.05, 0.5, 10)

cell_length = 2.0
half_cell_length = 0.5 * cell_length

world_positive_x  =   openmc.XPlane(half_cell_length, boundary_type='reflective')
world_negative_x  =  openmc.XPlane(-half_cell_length, boundary_type='reflective')
world_positive_y  =   openmc.YPlane(half_cell_length, boundary_type='reflective')
world_negative_y  =  openmc.YPlane(-half_cell_length, boundary_type='reflective')

top = openmc.ZPlane(half_cell_length, boundary_type='reflective')
bottom = openmc.ZPlane(-half_cell_length, boundary_type='reflective')

for f2m in fuel_to_moderators:
    case_name = f'{f2m:.2F}'
    fuel_length = np.sqrt(f2m * cell_length**2 / (1.0 + f2m))

    half_fuel_length = 0.5 * fuel_length

    fuel_positive_x = openmc.XPlane(half_fuel_length)
    fuel_negative_x = openmc.XPlane(-half_fuel_length)
    fuel_positive_y = openmc.YPlane(half_fuel_length)
    fuel_negative_y = openmc.YPlane(-half_fuel_length)
    fuel_region = -fuel_positive_x & + fuel_negative_x & -fuel_positive_y & +fuel_negative_y


    fuel_cell = openmc.Cell(
        name='fuel',
        region=fuel_region & -top & +bottom,
        fill=leu
    )

    moderator_region = ~fuel_region & -world_positive_x & + world_negative_x & -world_positive_y & +world_negative_y
    moderator_cell = openmc.Cell(
        name='moderator',
        region=moderator_region & -top & +bottom,
        fill=moderator
    )

    universe = openmc.Universe(cells=[fuel_cell, moderator_cell])
    geometry = openmc.Geometry(universe)

    model = openmc.Model(
        materials=materials,
        geometry=geometry,
        settings=settings
    )

    # Make a directory for the XML
    # os.makedirs(f'./cases/{case_name}', exist_ok=True)

    # Export the XML
    model.export_to_model_xml(f'./cases/{case_name}/model.xml')

    print(f'Running: {case_name}')
    openmc.run(
        threads=cores,
        cwd=f'./cases/{case_name}',
        path_input='./model.xml',
        geometry_debug=False,
        output=False
    )