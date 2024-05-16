MeshGenExample
###############

Description
============
This project is a meshing example based on gmsh and tetgen
which is targeted at a mesh suitable for devsim device simulation in 3D.

Recommended Usage
==================

Execute the scripts in order of the enumeration.

::

  01_generate_gmsh_stl.py

Generates a simple .stl geometry which resembles a cube of 1x1x1.

::

  02_mesh_tetgen_and_convert.py

Uses ``tetgen.exe`` to generate a tetrehedral mesh of the .stl cube
and converts the result back to the gmsh2.2 format.

::

  03_mesh_define_contacts.py

Reads the converted gmsh mesh and attaches the contacts to the top and buttom surface.
The mesh is scaled by a factor but the mesh in general should stay the same.

::

  04_check_tetrahedra.py

Checks the tetrahedra in the mesh and compares them to theoretical values.
Evaluates the total volume of the geometry for theoretical values and actual devsim values.

::

  04_devsim_eletrical_sim.py

Performs a constructed electrical simulation. The dimensions, doping and mobility are
chosen in a way that the volume has a resistance of 1 Ohm. Therefore the expected result
of the simulation is 1A for 1V.

Resources
=========
Tetgen
------
https://wias-berlin.de/software/tetgen/

Gmsh
----
https://gmsh.info/doc/texinfo/gmsh.html

Devsim
------
https://devsim.net/index.html

https://forum.devsim.org/

https://forum.devsim.org/t/drift-diffusion-simulation-for-3d-produces-higher-currents-than-expected