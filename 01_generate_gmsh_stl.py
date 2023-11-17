import gmsh
import math
import os.path
import sys

gmsh.initialize()
gmsh.model.add("nVolume")
gmsh.option.setNumber("Mesh.MeshSizeFactor", 50.0)

# build bulk
id_bulk1 = gmsh.model.occ.addBox(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1)

gmsh.model.occ.synchronize()

id_surf_top = gmsh.model.getEntitiesInBoundingBox(-0.1, -0.1, 0.9, 1.1, 1.1, 1.1, 2)[0][1]
id_surf_bot = gmsh.model.getEntitiesInBoundingBox(-0.1, -0.1, -0.1, 1.1, 1.1, 0.1, 2)[0][1]
id_surfaces = gmsh.model.getEntitiesInBoundingBox(-0.1, -0.1, -0.1, 1.1, 1.1, 1.1, 2)


# Physical Groups
grp_epi = gmsh.model.addPhysicalGroup(2, [i[1] for i in id_surfaces], 1, "Bulk")


gmsh.model.occ.synchronize()


gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
#gmsh.option.setNumber("Mesh.ScalingFactor", 1.0e-5)
gmsh.option.setNumber("Mesh.Algorithm", 5)
gmsh.option.setNumber("Mesh.Algorithm3D", 10)
gmsh.option.setNumber("Mesh.CharacteristicLengthExtendFromBoundary", 1)
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.option.setNumber("Mesh.Recombine3DConformity", 1.0)
gmsh.option.setNumber("Mesh.Recombine3DAll", 1.0)

gmsh.option.setNumber("Mesh.Format", 27) #STL
#gmsh.option.setNumber("Mesh.Format", 30) #Medit

gmsh.model.mesh.generate(3)

gmsh.write("./Out/nVolume.stl")

if 0:
    # Launch the GUI to see the results:
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()

gmsh.finalize()