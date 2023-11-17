#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Gerrit Lükens
# Created Date: 15.11.2023
# Python Version: 3.10
# version ='1.0'
# ----------------------------------------------------------------------------
import copy
import subprocess
import os
from pathlib import Path


# Factory Functions ----------------------------------------------------------
def create_element(mesh_type: str, line: str, config: dict = None) -> dict:
    """
    Creates an element dictionary object with all the information. Type ID follows gmsh convention:
        2 : 3-node triangle, 4 : 4-node tetrahedron
    :param mesh_type: "gmsh" or "tetgen"
    :param line: line of element section in mesh file
    :param config: Additional information for some mesh formats
    :returns: {
                "mesh_type": mesh_type,
                "id": id,
                "type": type,
                "tag_count": tag_count,
                "tags": tags,
                "node_count": len(nodes),
                "nodes": nodes
              }
    """
    match mesh_type:
        case "gmsh":
            line_split = line.strip().split()
            id, type, tag_count = (int(s) for s in line_split[:3])
            tags = [int(tag) for tag in line_split[3:3+tag_count]]
            nodes = [int(node) for node in line_split[3+tag_count:]]

            return {
                "mesh_type": mesh_type,
                "id": id,
                "type": type,
                "tag_count": tag_count,
                "tags": tags,
                "node_count": len(nodes),
                "nodes": nodes,
            }

        case "tetgen":
            if "nodes_per_element" not in config.keys():
                raise ValueError("tetgen needs additional information: "
                                 "nodes_per_element: (3 for faces, 4/10 for tetrahedra)")
            line_split = line.strip().split()
            id = int(line_split[0])
            if config["nodes_per_element"] == 3:
                type = 2
            elif config["nodes_per_element"] == 4:
                type = 4
            nodes = [int(node) for node in line_split[1:1+config["nodes_per_element"]]]
            tags = line_split[1+config["nodes_per_element"]:]

            return {
                "mesh_type": mesh_type,
                "id": id,
                "type": type,
                "tag_count": len(tags),
                "tags": tags,
                "node_count": len(nodes),
                "nodes": nodes,
            }

        case _:
            raise KeyError(f"Mesh Type {mesh_type} not supported")


def create_node(mesh_type: str, line: str) -> dict:
    """
    :param mesh_type:
    :param line:
    :return: gmsh: {"id": id, "coords": coords}
    tetgen: {"id": id, "coords": coords, "tags": tags}
    """
    match mesh_type:
        case "gmsh":
            line_split = line.strip().split()
            id = int(line_split[0])
            coords = [float(i) for i in line_split[1:]]
            return {"id": id, "coords": coords}
        case tetgen:
            line_split = line.strip().split()
            id = int(line_split[0])
            coords = [float(i) for i in line_split[1:4]]
            tags = [float(i) for i in line_split[4:]]
            return {"id": id, "coords": coords, "tags": tags}


def create_physical_name(line: str) -> dict:
    line_split = line.strip().split()
    dim = int(line_split[0])
    id = int(line_split[1])
    name = line_split[2]
    return {"dim": dim, "id": id, "name": name}


class MeshType:
    def __init__(self, mesh=None):
        if mesh is None:
            self.nodes = []
            self.node_count = 0
            self.physical_names = []
            self.elements = []
            self.element_count = 0
            self.triangles = []
            self.tetrahedra = []
        else:
            self.nodes = mesh.nodes
            self.node_count = mesh.node_count
            self.physical_names = mesh.physical_names
            self.elements = mesh.elements
            self.element_count = mesh.element_count
            self.triangles = mesh.triangles
            self.tetrahedra = mesh.tetrahedra

    def read_files(self, file_name):
        pass

    def write_files(self, file_name):
        pass

    def read_mesh(self, mesh):
        pass


class Gmsh(MeshType):
    def __init__(self, mesh=None):
        super().__init__(mesh)

    def reset_data(self):
        self.nodes = []
        self.node_count = 0
        self.physical_names = []
        self.elements = []
        self.element_count = 0
        self.triangles = []
        self.tetrahedra = []

    def read_files(self, file_name):
        if not file_name[-4:] == ".msh":
            file_name += ".msh"
        with open(file_name) as fh:
            current_mode = None
            self.reset_data()
            for line in fh:
                if current_mode != self.mode_selector(line, current_mode):  # mode has changed
                    current_mode = self.mode_selector(line, current_mode)
                else:
                    self.line_handler(line, current_mode)
        self.check_data_and_convert()

    def line_handler(self, line: str, current_mode: str):
        match current_mode:
            case "header":
                if line.strip().split()[0] != "2.2":
                    raise ValueError(f"Unsupported Gmsh Version: {line.strip().split()[0]}, only Version 2.2")
            case "names":
                if len(line.split()) == 1:
                    return
                self.physical_names.append(create_physical_name(line))
            case "nodes":
                if len(line.split()) == 1:
                    self.node_count = int(line.strip())
                    return
                self.nodes.append(create_node("gmsh", line))
            case "elements":
                if len(line.split()) == 1:
                    self.element_count = int(line.strip())
                    return
                self.elements.append(create_element("gmsh", line))
            case "":
                return

    def mode_selector(self, line: str, current_mode) -> str:
        match line:
            case str(x) if "$MeshFormat" in x:
                return "header"
            case str(x) if "$PhysicalNames" in x:
                return "names"
            case str(x) if "$Nodes" in x:
                return "nodes"
            case str(x) if "$Elements" in x:
                return "elements"
            case str(x) if "$End" in x:
                return ""
            case _:
                return current_mode

    def check_data_and_convert(self):
        if not self.node_count == len(self.nodes):
            raise ValueError(f"Node counts do not match! Expected:{self.node_count}, Value:{len(self.nodes)}")
        if not self.element_count == len(self.elements):
            raise ValueError(f"Element counts do not match! Expected:{self.element_count}, Value:{len(self.elements)}")

        for element in self.elements:
            if element["type"] == 2:
                self.triangles.append(element)
            elif element["type"] == 4:
                self.tetrahedra.append(element)

        self.triangles = copy.deepcopy(self.triangles)
        for tri in self.triangles:
            tri["id"] = tri["id"] % len(self.triangles) + 1

        self.tetrahedra = copy.deepcopy(self.tetrahedra)
        for tetra in self.tetrahedra:
            tetra["id"] = tetra["id"] % len(self.tetrahedra) + 1
        self.triangles.sort(key=lambda x: x["id"])
        self.tetrahedra.sort(key=lambda x: x["id"])

    def write_files(self, file_name):
        if not file_name[-4:] == ".msh":
            file_name += ".msh"
        with open(file_name, 'w') as fh:
            fh.write("$MeshFormat\n2.2 0 8\n$EndMeshFormat\n")  #Header

            fh.write("$PhysicalNames\n")
            fh.write(f"{len(self.physical_names)}\n")
            for name in self.physical_names:
                fh.write("{} {} {}\n".format(name["dim"], name["id"], name["name"]))
            fh.write("$EndPhysicalNames\n")

            fh.write("$Nodes\n")
            fh.write(f"{self.node_count}\n")
            for node in self.nodes:
                fh.write("{} {:.16e} {:.16e} {:.16e}\n".format(
                    node["id"], node["coords"][0], node["coords"][1], node["coords"][2]))
            fh.write("$EndNodes\n")

            fh.write("$Elements\n")
            fh.write(f"{self.element_count}\n")
            for element in self.elements:
                fh.write("{} {} {} {} {}\n".format(
                    element["id"], element["type"], element["tag_count"],
                    "".join(map(lambda x: str(x)+" ", element["tags"])).strip(),
                    "".join(map(lambda x: str(x)+" ",element["nodes"])).strip()))
            fh.write("$EndElements\n")

    def read_mesh(self, mesh: MeshType):
        self.nodes = mesh.nodes
        self.node_count = mesh.node_count
        self.physical_names = mesh.physical_names
        self.elements = mesh.elements
        self.element_count = mesh.element_count
        self.triangles = mesh.triangles
        self.tetrahedra = mesh.tetrahedra

    def __str__(self):
        return (f"Gmsh 2.2, Nodes:{self.node_count}, Elements: {self.element_count}, "
                f"Faces:{len(self.triangles)}, Tetrahedra:{len(self.tetrahedra)}")


class Tetgen(MeshType):
    def __init__(self, mesh=None):
        super().__init__(mesh)

    def reset_data(self):
        self.nodes = []
        self.node_count = 0
        self.physical_names = []
        self.elements = []
        self.element_count = 0
        self.triangles = []
        self.tetrahedra = []

    def read_files(self, file_name):
        if ".ele" in file_name or ".face" in file_name or ".node" in file_name:
            file_name = file_name.rsplit(".", 1)[0]
        self.reset_data()
        self.read_nodes(file_name)
        self.read_faces(file_name)
        self.read_tetrahedra(file_name)

        self.check_data_and_convert()

    def read_nodes(self, file_name):
        with open(file_name + ".node") as fh:
            first_line = []
            for line in fh:
                if line[0] == "#": continue  # skip comments
                if not any(first_line):  # read header line
                    first_line = line
                    self.node_count = int(first_line.split()[0])
                    continue
                self.nodes.append(create_node("tetgen", line))

    def read_faces(self, file_name):
        with open(file_name+".face") as fh:
            first_line = []
            for line in fh:
                if line[0] == "#": continue  # skip comments
                if not any(first_line):  # read header line
                    first_line = line
                    self.element_count += int(first_line.split()[0])
                    continue
                self.triangles.append(create_element("tetgen", line, config={"nodes_per_element": 3}))

    def read_tetrahedra(self, file_name):
        with open(file_name + ".ele") as fh:
            first_line = []
            for line in fh:
                if line[0] == "#": continue  # skip comments
                if not any(first_line):  # read header line
                    first_line = line
                    self.element_count += int(first_line.split()[0])
                    continue
                self.tetrahedra.append(create_element("tetgen", line, config={"nodes_per_element": 4}))

    def check_data_and_convert(self):
        if not self.node_count == len(self.nodes):
            raise ValueError(f"Node counts do not match! Expected:{self.node_count}, Value:{len(self.nodes)}")
        if not self.element_count == len(self.triangles) + len(self.tetrahedra):
            raise ValueError(f"Element counts do not match! Expected:{self.element_count}, Value:{len(self.elements)}")
        self.elements = copy.deepcopy(self.triangles)
        tetra_local = copy.deepcopy(self.tetrahedra)
        for tetra in tetra_local:
            tetra["id"] += len(self.triangles)
            self.elements.append(tetra)

    def write_files(self, file_name):
        if ".ele" in file_name or ".face" in file_name or ".node" in file_name:
            file_name = file_name.rsplit(".", 1)[0]

        with open(file_name + ".node", 'w') as fnode:
            fnode.write(f"# Generated by Python Convert Script\n")
            fnode.write(f"{self.node_count} 3 0 0\n")
            for node in self.nodes:
                fnode.write("{:>5} {:.16e} {:.16e} {:.16e}\n".format(
                    node["id"], node["coords"][0], node["coords"][1], node["coords"][2]))

        with open(file_name + ".face", 'w') as fface:
            fface.write(f"# Generated by Python Convert Script\n")
            fface.write(f"{len(self.triangles)}  0\n")
            for triangle in self.triangles:
                fface.write("{:>5} {} {}\n".format(triangle["id"],
                                                "".join(map(lambda x: "{:>6}".format(str(x)), triangle["nodes"])),
                                                "".join(map(lambda x: str(x)+" ", triangle["tags"])).strip()))

        with open(file_name + ".ele", 'w') as fele:
            fele.write(f"# Generated by Python Convert Script\n")
            fele.write(f"{len(self.tetrahedra)}  4  0\n")
            for tetra in self.tetrahedra:
                fele.write("{:>5}  {} {}\n".format(tetra["id"],
                                               "".join(map(lambda x: "{:>6}".format(str(x)), tetra["nodes"])),
                                               "".join(map(lambda x: str(x) + " ", tetra["tags"])).strip()))

    def read_mesh(self, mesh: MeshType):
        self.nodes = mesh.nodes
        self.node_count = mesh.node_count
        self.physical_names = mesh.physical_names
        self.elements = mesh.elements
        self.element_count = mesh.element_count
        self.triangles = mesh.triangles
        self.tetrahedra = mesh.tetrahedra

    def __str__(self):
        return (f"Tetgen, Nodes:{self.node_count}, Elements: {self.element_count}, "
                f"Faces:{len(self.triangles)}, Tetrahedra:{len(self.tetrahedra)}")


if __name__ == "__main__":

    subprocess.run(["tetgen.exe", "-pq", Path("./Out/nVolume.stl")])

    mesh_tetgen = Tetgen()
    mesh_tetgen.read_files("./Out/nVolume.1.node")
    mesh_gmsh = Gmsh(mesh_tetgen)
    mesh_gmsh.write_files("./Out/nVolume_meshed.msh")
