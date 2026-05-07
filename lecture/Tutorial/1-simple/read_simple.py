import openmc

statepoint = openmc.StatePoint('./case/statepoint.120.h5')
print(type(statepoint.keff))
print('keff', statepoint.keff)
print(statepoint.keff.nominal_value, statepoint.keff.std_dev)
