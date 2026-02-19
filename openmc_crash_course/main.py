"""Command-line interface for OpenMC Crash Course."""


def main():
    """Display information about the OpenMC Crash Course."""
    print("""
OpenMC Crash Course
==================

A progressive tutorial series for learning OpenMC and nuclear reactor theory.

Examples:
  1. Infinite Medium     - Materials and k-infinity
  2. Infinite Pin Cell   - Geometry and spatial effects
  3. Finite Pin Cell     - Leakage and k-eff
  4. Fuel Assembly       - Lattices and universes
  5. Reactor Core        - Full system simulation

To run an example:
  cd examples/01_infinite_medium
  python main.py

For more information, see the README.md file.
""")


if __name__ == '__main__':
    main()
