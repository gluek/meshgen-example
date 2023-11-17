import gmsh
import sys

plot = False

gmsh.initialize()
gmsh.open("./Out/nVolume_meshed.msh")

gmsh.model.occ.synchronize()

gmsh.model.mesh.classifySurfaces(0)

id_surf_top = gmsh.model.getEntitiesInBoundingBox(-0.1, -0.1, 0.9, 1.1, 1.1, 1.1, 2)[0][1]
id_surf_bot = gmsh.model.getEntitiesInBoundingBox(-0.1, -0.1, -0.1, 1.1, 1.1, 0.1, 2)[0][1]

# Physical Groups
grp_epi = gmsh.model.addPhysicalGroup(3, [0], 1, "Bulk")

contact_diodeA = gmsh.model.addPhysicalGroup(2, [id_surf_top], 2, "top")
contact_diodeB = gmsh.model.addPhysicalGroup(2, [id_surf_bot], 3, "bot")

gmsh.model.occ.synchronize()

gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)

gmsh.option.setNumber("Mesh.ScalingFactor", 1.0)
gmsh.write("./Out/nVolume_contacts_scaling_1.msh")

gmsh.option.setNumber("Mesh.ScalingFactor", 1.0e-5)
gmsh.write("./Out/nVolume_contacts_scaling_1e-5.msh")

gmsh.option.setNumber("Mesh.ScalingFactor", 10.0)
gmsh.write("./Out/nVolume_contacts_scaling_10.msh")

if plot:
    # Launch the GUI to see the results:
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()

    gmsh.finalize()