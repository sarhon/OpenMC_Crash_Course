import numpy as np
import openmc
import matplotlib.pyplot as plt
import uncertainties.unumpy as unp

keffs = np.array([])

radii = np.linspace(0.1, 1.0, 10)
for radius in radii:
    case_name = f"case/{radius:.2F}"
    statepoint = openmc.StatePoint(f'./{case_name}/statepoint.120.h5')
    keff = statepoint.keff
    keffs = np.append(keffs, keff)

plt.errorbar(radii, unp.nominal_values(keffs),
             yerr=unp.std_devs(keffs),
             fmt='o', capsize=4)
plt.xlabel("Radius (cm)")
plt.ylabel("k-eff")
plt.title("k-eff vs. Fuel Radius")
plt.grid()
plt.tight_layout()
plt.savefig('./keff.png', dpi=300)
plt.close()

reactivity = (keffs - 1.0) / keffs * 1e5

plt.errorbar(radii[3:], unp.nominal_values(reactivity)[3:],
             yerr=unp.std_devs(reactivity)[3:],
             fmt='o', capsize=4)
plt.xlabel("Radius (cm)")
plt.ylabel("Reactivity (pcm)")
plt.title("Reactivity vs. Fuel Radius")
plt.grid()
plt.tight_layout()
plt.savefig('./react.png', dpi=300)
plt.close


parts = [f"{keffs[i]:.3u}" for i in [0, 1]] + ["..."] + [f"{keffs[i]:.3u}" for i in [-2, -1]]
print("[" + ",  ".join(parts) + "]")