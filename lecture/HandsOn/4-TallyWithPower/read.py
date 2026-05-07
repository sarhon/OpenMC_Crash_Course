import matplotlib.pyplot as plt
import numpy as np
import openmc
from uncertainties import ufloat

case_name = "case"

EV_TO_J = 1.602176634e-19
power_W = 1.0e6  # 1 MW thermal

# Normalization to physical power
# heating score gives [eV / source neutron].
# Dividing the target power [W] by heating per source neutron [eV/src × J/eV]
# gives the source rate [src/s] needed to sustain that power.
# Multiplying any other tally by src_rate converts it to a physical rate.

sp = openmc.StatePoint(f'./{case_name}/statepoint.250.h5')

_ht = sp.get_tally(name="total_heating")
Q_per_src = ufloat(_ht.mean.flat[0], _ht.std_dev.flat[0])  # eV / src

if Q_per_src.n <= 0.0:
    raise RuntimeError(f"Total heating must be positive for power normalization; got {Q_per_src}")

src_rate = power_W / (Q_per_src * EV_TO_J)  # src / s  (uncertainty propagated)

total_volume  = 1.0                                   # cm³
power_density = power_W / total_volume                # W/cm³, uniform by symmetry (exact)

# flux score gives track-length integrated flux [cm / src neutron]; divide by
# volume to get flux density [n/cm²/s]
_ft = sp.get_tally(name="flux")
flux_per_src  = ufloat(_ft.mean.flat[0], _ft.std_dev.flat[0])
flux_physical = flux_per_src * src_rate / total_volume  # n/cm²/s  (uncertainty propagated)

print(
    f"Heating per source neutron : {Q_per_src:.3e} eV/src\n"
    f"Source rate at {power_W/1e6:.0f} MW        : {src_rate:.3e} src/s\n"
    f"Power density              : {power_density:.4e} W/cm³\n"
    f"Mean physical flux         : {flux_physical:.3e} n/cm²/s"
)

# ---------------------------------------------------------------------------
# Flux spectrum (lethargy-weighted, physical units)
# ---------------------------------------------------------------------------
# Spectrum tally gives [cm / src neutron] per energy bin. After dividing by
# volume and multiplying by src_rate we get [n/cm²/s] per bin. Dividing by
# Δu = ln(E_hi/E_lo) converts to per unit lethargy so the spectrum is flat
# in a 1/E region and area under the curve is the total flux.

neutron_energies = np.logspace(np.log10(1e-5), np.log10(20e6), 501)
photon_energies  = np.logspace(np.log10(1e3),  np.log10(20e6), 201)

n_tally = sp.get_tally(name="neutron_spectrum")
p_tally = sp.get_tally(name="photon_spectrum")

n_flux_per_src = n_tally.mean.ravel()   # cm/src per bin
p_flux_per_src = p_tally.mean.ravel()

# Convert to physical flux density per unit lethargy [n/cm²/s/lethargy]
n_lethargy_widths = np.diff(np.log(neutron_energies))
p_lethargy_widths = np.diff(np.log(photon_energies))

n_spectrum = n_flux_per_src * src_rate.n / total_volume / n_lethargy_widths
p_spectrum = p_flux_per_src * src_rate.n / total_volume / p_lethargy_widths

fig, ax = plt.subplots(figsize=(8, 5))
ax.step(neutron_energies[:-1], n_spectrum, where="post",
        label="Neutron flux", color="steelblue")
ax.step(photon_energies[:-1], p_spectrum, where="post",
        label="Photon flux",  color="tomato")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(1e-5*1e6, 30*1e6)   # MeV: covers full neutron range through 20 MeV
ax.set_xlabel("Energy [eV]")
ax.set_ylabel(r"$\phi(u)$ [n/cm²/s/lethargy]")
ax.set_title(f"UCl₃-NaCl MSR flux spectrum at {power_W/1e6:.0f} MW")
ax.legend()
ax.grid(which="both", ls="--", alpha=0.4)
fig.tight_layout()
fig.savefig("spectrum.png", dpi=150)
print("Spectrum saved to spectrum.png")