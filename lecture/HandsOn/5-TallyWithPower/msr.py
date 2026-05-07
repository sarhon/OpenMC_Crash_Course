import os

import openmc
import psutil

EV_TO_J = 1.602176634e-19

# ── Power level ───────────────────────────────────────────────────────────────
power_W = 1.0e6  # 1 MW thermal

# UCl3-NaCl eutectic salt (33/67 mol%) with 20 w/o HALEU
# UCl3 → 0.33 U + 0.99 Cl   |   NaCl → 0.67 Na + 0.67 Cl
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
    particles=10_000,
    batches=120,
    inactive=20,
    temperature={'method': 'interpolation'},
    photon_transport=True,  # enables photon transport for full heating tally
)

# 1 cm × 1 cm × 1 cm homogeneous salt box with reflective boundaries.
# Reflective boundaries approximate an infinite homogeneous medium by removing
# net neutron leakage from the repeated unit cell.
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

# Scalar heating tally — total energy deposited [eV / source neutron]
# Used to convert any tally to physical units at a given power level.
total_heating_tally = openmc.Tally(name="total_heating")
total_heating_tally.scores = ["heating"]

# Scalar flux tally — no mesh needed; flux is uniform in an infinite homogeneous medium
flux_tally = openmc.Tally(name="flux")
flux_tally.scores = ["flux"]

tallies = openmc.Tallies([total_heating_tally, flux_tally])

model = openmc.Model(geometry=geometry, materials=materials, settings=settings, tallies=tallies)

case_name = "case"
os.makedirs(f'./{case_name}', exist_ok=True)
model.export_to_model_xml(f'./{case_name}/model.xml')

cores = psutil.cpu_count(logical=False)
openmc.run(threads=cores, cwd=f'./{case_name}/', path_input='./model.xml')

# ── Normalization to physical power ───────────────────────────────────────────
# heating score gives [eV / source neutron].
# Dividing the target power [W] by heating per source neutron [eV/src × J/eV]
# gives the source rate [src/s] needed to sustain that power.
# Multiplying any other tally by src_rate converts it to a physical rate.

sp = openmc.StatePoint(f'./{case_name}/statepoint.{settings.batches}.h5')

Q_per_src = sp.get_tally(name="total_heating").mean.flat[0]  # eV / src
if Q_per_src <= 0.0:
    raise RuntimeError(f"Total heating must be positive for power normalization; got {Q_per_src:.4e} eV/src")

src_rate = power_W / (Q_per_src * EV_TO_J)  # src / s

total_volume  = box_width**3                          # cm³
power_density = power_W / total_volume                # W/cm³, uniform by symmetry

# flux score gives track-length integrated flux [cm / src neutron]; divide by
# volume to get flux density [n/cm²/s]
flux_per_src  = sp.get_tally(name="flux").mean.flat[0]
flux_physical = flux_per_src * src_rate / total_volume  # n/cm²/s

print(f"Heating per source neutron : {Q_per_src:.4e} eV/src")
print(f"Source rate at {power_W/1e6:.0f} MW         : {src_rate:.4e} src/s")
print(f"Power density              : {power_density:.4e} W/cm³")
print(f"Mean physical flux         : {flux_physical:.4e} n/cm²/s")