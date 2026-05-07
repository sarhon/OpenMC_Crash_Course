import numpy as np
import openmc
import matplotlib.pyplot as plt
from scipy.stats import linregress

borons = np.linspace(500, 1300, 9)

keffs    = np.zeros(len(borons))
keff_unc = np.zeros(len(borons))
abs_rate = np.zeros(len(borons))
abs_unc  = np.zeros(len(borons))

for i, boron_ppm in enumerate(borons):
    sp = openmc.StatePoint(f'./case/{boron_ppm}/statepoint.220.h5')

    k = sp.keff
    keffs[i]    = k.n
    keff_unc[i] = k.s

    tally = sp.get_tally(name='moderator_absorption')
    abs_rate[i] = tally.mean.flat[0]
    abs_unc[i]  = tally.std_dev.flat[0]

# Reactivity: ρ = (k-1)/k * 1e5  [pcm]
rho     = (keffs - 1) / keffs * 1e5
rho_unc = keff_unc / keffs**2 * 1e5   # propagated uncertainty

# Linear fit — slope is the boron worth in pcm/ppm
fit = linregress(borons, rho)

print(f"Boron worth:  {fit.slope:.3f} pcm/ppm")
print(f"Fit R²:       {fit.rvalue**2:.5f}")

fig, ax1 = plt.subplots(figsize=(8, 5))

# Left axis — reactivity
ax1.errorbar(borons, rho, yerr=rho_unc, fmt='o', capsize=4,
             color='tab:blue', label='Reactivity')
ax1.plot(borons, fit.slope * borons + fit.intercept, '--',
         color='tab:blue', label=f'Linear fit: {fit.slope:.2f} pcm/ppm')
ax1.set_xlabel('Boron Concentration (ppm)')
ax1.set_ylabel('Reactivity ρ (pcm)', color='tab:blue')
ax1.tick_params(axis='y', labelcolor='tab:blue')

# Right axis — moderator absorption rate
ax2 = ax1.twinx()
ax2.errorbar(borons, abs_rate, yerr=abs_unc, fmt='s', capsize=4,
             color='tab:orange', label='Moderator absorption')
ax2.set_ylabel('Moderator Absorption Rate (neutrons / source neutron)', color='tab:orange')
ax2.tick_params(axis='y', labelcolor='tab:orange')

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

ax1.set_title('Boron Reactivity Worth and Moderator Absorption Rate')
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./boron_analysis.png', dpi=300)
plt.close()