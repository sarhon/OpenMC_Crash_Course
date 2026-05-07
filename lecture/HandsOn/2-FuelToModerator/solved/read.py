import numpy as np
import matplotlib.pyplot as plt
import openmc

fuel_to_moderators = np.linspace(0.05, 0.5, 10)

keffs = []
keff_stds = []

for f2m in fuel_to_moderators:
    case_name = f'{f2m:.2F}'
    sp = openmc.StatePoint(f'./cases/{case_name}/statepoint.220.h5')
    keffs.append(sp.keff.n)
    keff_stds.append(sp.keff.s)

keffs = np.array(keffs)
keff_stds = np.array(keff_stds)

peak_idx = np.argmax(keffs)
print(f'Peak k-inf: {keffs[peak_idx]:.5f} +/- {keff_stds[peak_idx]:.5f} at F/M = {fuel_to_moderators[peak_idx]:.2f}')

for f2m, k, s in zip(fuel_to_moderators, keffs, keff_stds):
    print(f'  F/M = {f2m:.2f}  keff = {k:.5f} +/- {s:.5f}')

# Plot
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(fuel_to_moderators, keffs, yerr=keff_stds, fmt='o-', markersize=5,
            capsize=3, label='k-inf')
ax.axvline(fuel_to_moderators[peak_idx], color='green', linestyle='--',
           label=f'Peak F/M = {fuel_to_moderators[peak_idx]:.2f}')
ax.set_xlabel('Fuel-to-Moderator Ratio')
ax.set_ylabel('k-inf')
ax.set_title('k-inf vs. Fuel-to-Moderator Ratio')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('kinf_vs_f2m.png', dpi=150)
plt.show()
print('Plot saved to kinf_vs_f2m.png')
