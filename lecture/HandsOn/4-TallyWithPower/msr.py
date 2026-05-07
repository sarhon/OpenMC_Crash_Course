import os

import numpy as np
import openmc
import psutil

# UCl3-NaCl eutectic salt (33/67 mol%) with 20 w/o HALEU
# UCl3 → 0.33 U + 0.99 Cl - NaCl → 0.67 Na + 0.67 Cl
enrich_wo = 0.20
u235_ao = (enrich_wo / 235) / (enrich_wo / 235 + (1 - enrich_wo) / 238)

salt = openmc.Material(name="ucl3_nacl_eutectic")
salt.add_nuclide("U235", 0.33 * u235_ao)
salt.add_nuclide("U238", 0.33 * (1.0 - u235_ao))
salt.add_element("Cl",   1.66)  # 0.99 from UCl3 + 0.67 from NaCl
salt.add_element("Na",   0.67)
salt.set_density("g/cm3", 3.2)  # liquid salt at operating temperature
salt.temperature = 900.0        # K

materials = openmc.Materials([salt])
materials.cross_sections = "/home/harrison/data/openmc-xs/endfb-vii.1-hdf5/cross_sections.xml"

settings = openmc.Settings(
    particles=100_000,
    batches=250,
    inactive=50,
    temperature={'method': 'interpolation'},
    photon_transport=True,  # enables photon transport for full heating tally
)

# Infinity Homogenous
box_width = 1.0  # cm
half_width = box_width / 2.0
xmin = openmc.XPlane(x0=-half_width, boundary_type="reflective")
xmax = openmc.XPlane(x0= half_width, boundary_type="reflective")
ymin = openmc.YPlane(y0=-half_width, boundary_type="reflective")
ymax = openmc.YPlane(y0= half_width, boundary_type="reflective")
zmin = openmc.ZPlane(z0=-half_width, boundary_type="reflective")
zmax = openmc.ZPlane(z0= half_width, boundary_type="reflective")
box_region = +xmin & -xmax & +ymin & -ymax & +zmin & -zmax
cell = openmc.Cell(name="salt", fill=salt, region=box_region)
geometry = openmc.Geometry(openmc.Universe(cells=[cell]))

settings.source = [openmc.IndependentSource(
    space=openmc.stats.Box(
        lower_left =(-half_width, -half_width, -half_width),
        upper_right=( half_width,  half_width,  half_width),
    ),
    constraints={'fissionable': True},
    energy=openmc.stats.Watt(),
    particle='neutron'
)]

# Scalar heating tally total energy deposited [eV / source neutron]
total_heating_tally = openmc.Tally(name="total_heating")
total_heating_tally.scores = ["heating"]

# Scalar flux tally
flux_tally = openmc.Tally(name="flux")
flux_tally.scores = ["flux"]

# Neutron flux spectrum: 500 equal-lethargy bins from 1e-5 eV → 20 MeV
neutron_energies = np.logspace(np.log10(1e-5), np.log10(20e6), 501)
neutron_spectrum_tally = openmc.Tally(name="neutron_spectrum")
neutron_spectrum_tally.filters = [openmc.EnergyFilter(neutron_energies)]
neutron_spectrum_tally.scores = ["flux"]

# Photon flux spectrum: 200 equal-lethargy bins from 1 keV → 20 MeV
photon_energies = np.logspace(np.log10(1e3), np.log10(20e6), 201)
photon_spectrum_tally = openmc.Tally(name="photon_spectrum")
photon_spectrum_tally.filters = [
    openmc.EnergyFilter(photon_energies),
    openmc.ParticleFilter(["photon"]),
]
photon_spectrum_tally.scores = ["flux"]

tallies = openmc.Tallies([
    total_heating_tally,
    flux_tally,
    neutron_spectrum_tally,
    photon_spectrum_tally,
])

model = openmc.Model(geometry=geometry, materials=materials, settings=settings, tallies=tallies)

case_name = "case"
os.makedirs(f'./{case_name}', exist_ok=True)
model.export_to_model_xml(f'./{case_name}/model.xml')

cores = psutil.cpu_count(logical=False)
openmc.run(threads=cores, cwd=f'./{case_name}/', path_input='./model.xml')