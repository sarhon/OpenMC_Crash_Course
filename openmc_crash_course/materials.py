import openmc

def get_materials():
    """Returns a collection of materials used in the crash course."""
    uo2 = openmc.Material(name='fuel')
    uo2.add_nuclide('U235', 0.05)
    uo2.add_nuclide('U238', 0.95)
    uo2.add_nuclide('O16', 2.0)
    uo2.set_density('g/cm3', 10.0)

    zirc = openmc.Material(name='zirc')
    zirc.add_element('Zr', 1.0)
    zirc.set_density('g/cm3', 6.5)

    water = openmc.Material(name='water')
    water.add_nuclide('H1', 2.0)
    water.add_nuclide('O16', 1.0)
    water.set_density('g/cm3', 1.0)
    water.add_s_alpha_beta('c_H_in_H2O')

    steel = openmc.Material(name='steel')
    steel.add_element('Fe', 0.68)
    steel.add_element('Cr', 0.18)
    steel.add_element('Ni', 0.10)
    steel.add_element('Mn', 0.02)
    steel.add_element('Si', 0.01)
    steel.add_element('C', 0.01)
    steel.set_density('g/cm3', 7.9)

    air = openmc.Material(name='air')
    air.add_element('N', 0.784431)
    air.add_element('O', 0.210748)
    air.add_element('Ar', 0.004671)
    air.add_element('C', 0.000150)
    air.set_density('g/cm3', 0.001225)

    all_materials = {
        'uo2': uo2,
        'zirc': zirc,
        'water': water,
        'steel': steel,
        'air': air
    }

    return all_materials
