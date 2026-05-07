import os

import numpy as np
import openmc
import psutil

cores = psutil.cpu_count(logical=False)

heu = openmc.Material(name='heu')
enrichment = 0.9371
heu.add_nuclide('U235', enrichment, percent_type='wo')
heu.add_nuclide('U238', 1.0-enrichment, percent_type='wo')
heu.set_density('g/cm3', 18.74)
heu.temperature = 294 # K

materials = openmc.Materials([heu])
materials.cross_sections = "/home/harrison/data/openmc-xs/endfb-vii.1-hdf5/cross_sections.xml"

settings = openmc.Settings()
settings.batches = 220
settings.inactive = 20
settings.particles = 10_000
settings.run_mode = 'eigenvalue'
settings.temperature = {'method': 'interpolation'}

radii = np.linspace(1.0, 10.0, 31)

for r in radii:
    case_name = f'{r:.2F}'
    sphere = openmc.Sphere(r=r)
    sphere.boundary_type = 'vacuum'

    cell = openmc.Cell(
        region=-sphere,
        fill=heu
    )

    universe = openmc.Universe(cells=[cell])
    geometry = openmc.Geometry(universe)

    model = openmc.Model(
        materials=materials,
        geometry=geometry,
        settings=settings,
    )


    # Make a directory for the XML
    os.makedirs(f'./cases/{case_name}', exist_ok=True)

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