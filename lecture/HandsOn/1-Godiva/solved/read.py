import numpy as np
import matplotlib.pyplot as plt
import openmc

radii = np.linspace(1.0, 10.0, 31)

keffs = []
keff_stds = []

for r in radii:
    case_name = f'{r:.2F}'
    sp = openmc.StatePoint(f'./cases/{case_name}/statepoint.220.h5')
    keffs.append(sp.keff.n)
    keff_stds.append(sp.keff.s)

keffs = np.array(keffs)
keff_stds = np.array(keff_stds)

# Find the two bracketing points closest to keff = 1.0
diff = keffs - 1.0
idx = np.argmin(np.abs(diff))

# Choose the two points that straddle keff = 1.0
if diff[idx] > 0:
    i_lo, i_hi = idx - 1, idx
else:
    i_lo, i_hi = idx, idx + 1

r_lo, r_hi = radii[i_lo], radii[i_hi]
k_lo, k_hi = keffs[i_lo], keffs[i_hi]

r_critical = r_lo + (1.0 - k_lo) / (k_hi - k_lo) * (r_hi - r_lo)
print(f'Bracketing radii: {r_lo:.2f} cm (keff={k_lo:.5f}), {r_hi:.2f} cm (keff={k_hi:.5f})')
print(f'Critical radius: {r_critical:.4f} cm')
volume = 4/3 * np.pi * r_critical**3
print(f'Critical volume: {volume:.2f} cm^3')
mass = volume * 18.74 * 1e-3
print(f'Critical mass: {mass:.2f} kg')

# Plot
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(radii, keffs, yerr=keff_stds, fmt='o-', markersize=4, capsize=3, label='k-eff')
ax.axhline(1.0, color='red', linestyle='--', label='k-eff = 1.0')
ax.axvline(r_critical, color='green', linestyle='--',
           label=f'Critical radius = {r_critical:.4f} cm')
ax.set_xlabel('Radius (cm)')
ax.set_ylabel('k-eff')
ax.set_title('Godiva: k-eff vs. Sphere Radius')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('keff_vs_radius.png', dpi=150)
plt.show()
print('Plot saved to keff_vs_radius.png')
