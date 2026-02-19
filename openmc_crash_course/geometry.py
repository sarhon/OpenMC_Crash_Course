import openmc
import numpy as np
import math

def create_pin_cell_universe(
        uo2, zirc, water,
        fuel_radius=0.39, cladding_radius=0.45
):
    """Creates a fuel pin cell universe.

    A pin cell consists of three concentric cylindrical regions:
    - Fuel pellet (UO2) in the center
    - Cladding (Zircaloy) surrounding the fuel
    - Moderator (water) outside the cladding
    """
    fuel_cylinder = openmc.ZCylinder(r=fuel_radius)
    cladding_cylinder = openmc.ZCylinder(r=cladding_radius)

    fuel_pin_univ = openmc.Universe(name='Fuel Pin')
    fuel_cell = openmc.Cell(name='fuel', fill=uo2, region=-fuel_cylinder)
    clad_cell = openmc.Cell(name='cladding', fill=zirc, region=+fuel_cylinder & -cladding_cylinder)
    mod_cell = openmc.Cell(name='moderator', fill=water, region=+cladding_cylinder)
    fuel_pin_univ.add_cells([fuel_cell, clad_cell, mod_cell])

    return fuel_pin_univ

def create_infinite_pincell_geometry(
        uo2, zirc, water,
        fuel_radius=0.39, cladding_radius=0.45,
        pitch=1.26
):
    """Creates an infinite pin cell geometry with periodic boundaries.

    Used to study spatial self-shielding without leakage effects.
    """
    pin_univ = create_pin_cell_universe(uo2, zirc, water, fuel_radius, cladding_radius)
    prism = openmc.model.RectangularPrism(width=pitch, height=pitch, boundary_type='periodic')
    
    root_cell = openmc.Cell(fill=pin_univ, region=-prism)
    root_universe = openmc.Universe(cells=[root_cell])
    return openmc.Geometry(root_universe)

def create_finite_pincell_geometry(
        uo2, zirc, water,
        fuel_radius=0.39, cladding_radius=0.45,
        pitch=1.26, height=100.0
):
    """Creates a finite pin cell geometry with vacuum boundaries.

    Used to study leakage effects and the difference between k-inf and k-eff.
    """
    pin_univ = create_pin_cell_universe(uo2, zirc, water, fuel_radius, cladding_radius)
    
    z_min = openmc.ZPlane(name='z_min', z0=-height/2, boundary_type='vacuum')
    z_max = openmc.ZPlane(name='z_max', z0=height/2, boundary_type='vacuum')
    
    prism = openmc.model.RectangularPrism(width=pitch, height=pitch, boundary_type='vacuum')
    prism.min_x1.name = 'min_x'
    prism.max_x1.name = 'max_x'
    prism.min_x2.name = 'min_y'
    prism.max_x2.name = 'max_y'
    
    root_cell = openmc.Cell(fill=pin_univ, region=-prism & +z_min & -z_max)
    
    root_universe = openmc.Universe(cells=[root_cell])
    return openmc.Geometry(root_universe)

def create_water_universe(water):
    """Creates a water-only universe for guide tubes and reflector regions."""
    water_univ = openmc.Universe(name='Water Guide Tube')
    water_gt_cell = openmc.Cell(fill=water)
    water_univ.add_cells([water_gt_cell])
    return water_univ

def create_assembly_lattice(
        fuel_pin_univ, water_univ,
        pitch=1.26, size=17
):
    """Creates a fuel assembly lattice with guide tubes.

    Creates a size x size lattice of fuel pins with water guide tubes
    at the center and four corners.
    """
    lattice = openmc.RectLattice()
    lattice.lower_left = (-pitch * size / 2, -pitch * size / 2)
    lattice.pitch = (pitch, pitch)
    
    universes = np.full((size, size), fuel_pin_univ)
    # Simple water tubes in the middle and corners
    center = size // 2
    universes[center, center] = water_univ
    universes[3, 3] = water_univ
    universes[3, size-4] = water_univ
    universes[size-4, 3] = water_univ
    universes[size-4, size-4] = water_univ
    
    lattice.universes = universes
    return lattice

def create_core_lattice(fuel_univ, reflector_univ, core_map, assy_pitch):
    """Creates a core lattice from a map of assemblies.

    The core_map is a 2D list where 1 = fuel assembly, 0 = reflector.
    """
    size = len(core_map)
    lattice = openmc.RectLattice()
    lattice.lower_left = (-assy_pitch * size / 2, -assy_pitch * size / 2)
    lattice.pitch = (assy_pitch, assy_pitch)
    
    universes = np.empty((size, size), dtype=openmc.Universe)
    for i in range(size):
        for j in range(size):
            universes[i, j] = fuel_univ if core_map[i][j] == 1 else reflector_univ
    
    lattice.universes = universes
    lattice.outer = reflector_univ
    return lattice

def create_assembly_universe(
        uo2, zirc, water,
        pitch=1.26, size=17,
        wall_thickness=0.2, gap_thickness=0.1
):
    """Creates a fuel assembly universe.

    Structure (from inside to outside):
    1. Lattice of fuel pins with guide tubes (size x size)
    2. Zircaloy assembly wall
    3. Water gap between assemblies
    """
    fuel_pin_univ = create_pin_cell_universe(uo2, zirc, water)
    water_univ = create_water_universe(water)
    lattice = create_assembly_lattice(fuel_pin_univ, water_univ, pitch, size)
    
    # Define assembly regions
    lattice_width = pitch * size
    inner_prism = openmc.model.RectangularPrism(width=lattice_width, height=lattice_width)

    wall_width = lattice_width + 2 * wall_thickness
    wall_prism = openmc.model.RectangularPrism(width=wall_width, height=wall_width)

    # Create cells
    lattice_cell = openmc.Cell(name='lattice_cell', fill=lattice, region=-inner_prism)
    wall_cell = openmc.Cell(name='wall_cell', fill=zirc, region=+inner_prism & -wall_prism)
    gap_cell = openmc.Cell(name='gap_cell', fill=water, region=+wall_prism)

    assy_univ = openmc.Universe(name='Fuel Assembly')
    assy_univ.add_cells([lattice_cell, wall_cell, gap_cell])
    return assy_univ

def generate_circular_core_map(
        grid_size, assy_pitch, target_assemblies=None
):
    """Generates a circular core map on a square grid.

    Selects the closest assemblies to the center to create a roughly
    circular core layout. Returns (core_map, barrel_radius) where:
    - core_map: 2D list where 1 = fuel assembly, 0 = reflector
    - barrel_radius: minimum radius to enclose all fuel assemblies
    """
    half = (grid_size - 1) / 2.0
    max_corner_dist = 0.0

    # Calculate distance for each grid position
    positions = []
    for i in range(grid_size):
        for j in range(grid_size):
            cx = (j - half) * assy_pitch
            cy = (half - i) * assy_pitch
            corner_dist = math.sqrt(
                (abs(cx) + assy_pitch / 2.0) ** 2 +
                (abs(cy) + assy_pitch / 2.0) ** 2
            )
            positions.append((corner_dist, i, j))

    # Select closest N assemblies
    positions.sort()
    target_assemblies = min(target_assemblies or len(positions), len(positions))

    selected = set()
    for k in range(target_assemblies):
        corner_dist, i, j = positions[k]
        selected.add((i, j))
        max_corner_dist = max(max_corner_dist, corner_dist)

    # Build core map
    core_map = []
    for i in range(grid_size):
        row = [1 if (i, j) in selected else 0 for j in range(grid_size)]
        core_map.append(row)

    barrel_inner_radius = max_corner_dist + 1.0
    return core_map, barrel_inner_radius


def create_core_geometry(
        uo2, zirc, water, steel, air,
        core_map,
        pitch=1.26, assy_size=17,
        wall_thickness=0.2, gap_thickness=0.1,
        barrel_ir=None, barrel_thickness=5.0,
        height=400.0
):
    """Creates a full core geometry with a cylindrical steel barrel and air.

    Parameters
    ----------
    steel : openmc.Material
        Reactor vessel / barrel material.
    air : openmc.Material
        Material outside the barrel.
    barrel_ir : float or None
        Inner radius of the steel barrel.  When *None* it is computed
        automatically so that no assembly is clipped.
    barrel_thickness : float
        Thickness of the steel barrel (cm).
    height : float
        Axial height of the core geometry (cm).
    """
    assy_inner_pitch = pitch * assy_size
    assy_pitch = assy_inner_pitch + 2 * (wall_thickness + gap_thickness)

    assy_univ = create_assembly_universe(
        uo2, zirc, water, pitch, assy_size, wall_thickness, gap_thickness
    )
    reflector_univ = create_water_universe(water)

    lattice = create_core_lattice(assy_univ, reflector_univ, core_map, assy_pitch)

    grid_size = len(core_map)

    # Auto-compute barrel inner radius if not provided
    if barrel_ir is None:
        half = (grid_size - 1) / 2.0
        max_corner = 0.0
        for i in range(grid_size):
            for j in range(grid_size):
                if core_map[i][j] == 1:
                    cx = (j - half) * assy_pitch
                    cy = (half - i) * assy_pitch
                    corner_dist = math.sqrt(
                        (abs(cx) + assy_pitch / 2.0) ** 2 +
                        (abs(cy) + assy_pitch / 2.0) ** 2
                    )
                    max_corner = max(max_corner, corner_dist)
        barrel_ir = max_corner + 1.0

    barrel_or = barrel_ir + barrel_thickness

    # Surfaces
    barrel_inner_cyl = openmc.ZCylinder(r=barrel_ir, name='barrel_inner')
    barrel_outer_cyl = openmc.ZCylinder(r=barrel_or, name='barrel_outer')

    # Z-planes for axial boundaries
    z_min = openmc.ZPlane(z0=-height/2, boundary_type='vacuum', name='z_min')
    z_max = openmc.ZPlane(z0=height/2, boundary_type='vacuum', name='z_max')

    # Square world boundary (just outside barrel)
    world_half = barrel_or + 10.0  # 10 cm margin
    world_prism = openmc.model.RectangularPrism(
        width=2 * world_half, height=2 * world_half,
        boundary_type='vacuum'
    )

    # Cells
    core_cell = openmc.Cell(name='core', fill=lattice,
                            region=-barrel_inner_cyl & +z_min & -z_max)
    barrel_cell = openmc.Cell(name='barrel', fill=steel,
                              region=+barrel_inner_cyl & -barrel_outer_cyl & +z_min & -z_max)
    air_cell = openmc.Cell(name='air', fill=air,
                           region=+barrel_outer_cyl & -world_prism & +z_min & -z_max)

    root_universe = openmc.Universe(cells=[core_cell, barrel_cell, air_cell])
    return openmc.Geometry(root_universe)
