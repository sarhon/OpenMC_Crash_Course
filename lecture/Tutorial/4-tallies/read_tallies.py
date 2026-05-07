import openmc
import matplotlib.pyplot as plt


statepoint = openmc.StatePoint('./tallies_case/statepoint.120.h5')
tally = statepoint.get_tally(name='flux_map')
mesh = tally.filters[0].mesh

nx, ny, nz = mesh.dimension
flux = tally.mean.reshape((nx, ny, nz)).sum(axis=2).T
x_min, y_min, z_min = mesh.lower_left
x_max, y_max, z_max = mesh.upper_right

plt.imshow(flux, extent=(x_min, x_max, y_min, y_max), origin='lower')
plt.xlabel('x (cm)')
plt.ylabel('y (cm)')
plt.title('Flux Map')
plt.colorbar(label='Flux')
plt.tight_layout()
plt.savefig('./flux_map.png', dpi=300)
plt.close()

group_tally = statepoint.get_tally(name='three_group_flux_map')
group_fluxes = group_tally.mean.reshape((nx, ny, nz, 3)).sum(axis=2)

for group_number, group_name in [(0, 'Thermal'), (2, 'Fast')]:
    flux = group_fluxes[:, :, group_number].T

    plt.imshow(flux, extent=(x_min, x_max, y_min, y_max), origin='lower')
    plt.xlabel('x (cm)')
    plt.ylabel('y (cm)')
    plt.title(f'{group_name} Flux Map')
    plt.colorbar(label='Flux')
    plt.tight_layout()
    plt.savefig(f'./{group_name.lower()}_flux_map.png', dpi=300)
    plt.close()
