# Copyright 2013 Devsim LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from devsim import *
import numpy
import matplotlib.pyplot as plt


def calculations_for_tet(index):
    xs = []
    ys = []
    zs = []
    radius = 0
    for i in range(4):
        ni = elements[index][i]
        xs.append(x[ni])
        ys.append(y[ni])
        zs.append(z[ni])

    mymat = numpy.zeros((3, 3))
    myrhs = numpy.zeros((3,1))
    n0 = elements[index][0]
    for i in range(3):
        ni = elements[index][i+1]
        v = coordinate[ni] - coordinate[n0]
        myrhs[i] = 0.5*numpy.dot(v, v.T)
        mymat[i, :] = coordinate[ni] - coordinate[n0]

    # print(mymat)
    # print(myrhs)
    foo = numpy.linalg.solve(mymat, myrhs) + coordinate[n0].T
    radius = 0.0

    for i in range(4):
        ni = elements[mytet][i]
        v = coordinate[ni] - foo.T
        radius = numpy.linalg.norm(v)
    return xs, ys, zs, radius, foo

mesh="./Out/nVolume_contacts_scaling_1.msh"
#mesh="./Out/nVolume_contacts_scaling_1e-5.msh"
#mesh="./Out/nVolume_contacts_scaling_10.msh"

create_gmsh_mesh(file=mesh, mesh="volume3d")
add_gmsh_region( mesh="volume3d" , gmsh_name="Bulk" , region="Bulk" , material="Silicon")
finalize_mesh( mesh="volume3d")
create_device( mesh="volume3d" , device="resistor3d")
#write_devices( file="gmsh_resistor3d_out.msh")

device="resistor3d"
region="Bulk"

elements = get_element_node_list(device=device, region=region)

x = get_node_model_values(device=device, region=region, name="x")
y = get_node_model_values(device=device, region=region, name="y")
z = get_node_model_values(device=device, region=region, name="z")

coordinate = numpy.matrix([list(a) for a in zip(x, y, z)])

#print coordinate[1]
vol = 0.0
tetras = []
tetrahedron_volumes = [None]*len(elements)
actual_volumes = [None]*len(elements)
element_node_volumes = get_element_model_values(device=device, region=region, name="ElementNodeVolume")

for tet_index, e in enumerate(elements):
    v = [None]*3
    for i in range(3):
        v[i] = coordinate[e[i+1]] - coordinate[e[0]]

    tet_vol = float(numpy.abs(numpy.dot(numpy.cross(v[0], v[1]), v[2].T)) / 6.0)
    vol += tet_vol
    actual_vol = sum([abs(q) for q in element_node_volumes[6*tet_index:6*(tet_index+1)]])
    actual_volumes[tet_index] = 2 * actual_vol
    tetrahedron_volumes[tet_index] = tet_vol
    tetras.append({
        "id": tet_index,
        "tetra_volume": tet_vol,
        "actual_volume": 2 * actual_vol,
        "ratio": 2 * actual_vol / tet_vol
    })

ratios = numpy.array([actual_volumes[i] / tetrahedron_volumes[i] for i in range(len(actual_volumes))])
max_ratio = numpy.max(ratios)
maxtet = numpy.where(ratios == max_ratio)[0][0]

print("")
print("Tetrahedron Stats: -----------------------------------------------------------------")
for tetra in tetras:
    print("id: {:>3}, ratio: {:.2f}, tetra volume: {:.4e}, actual volume: {:.4e}".format(
        tetra["id"], tetra["ratio"], tetra["tetra_volume"], tetra["actual_volume"]))
print("------------------------------------------------------------------------------------")
print(f"{sum(actual_volumes)}\tVolume calculated from tetrahedra edge volumes")
print(f"{sum(tetrahedron_volumes)}\tVolume from tetrahedra")



mytet = 3
xs, ys, zs, radius, foo = calculations_for_tet(mytet)
ax = plt.axes(projection='3d')
ax.set_aspect('equal')
ax.set_title("tetrahedron index: {}, ratio: {:.2f}".format(tetras[mytet]["id"], tetras[mytet]["ratio"]))

for i in range(4):
    for j in range(i+1, 4):
        ax.plot(
            (xs[i], xs[j]),
            (ys[i], ys[j]),
            (zs[i], zs[j]), 'b')

for i in range(4):
    ax.plot(
        (xs[i], foo[0].item()),
        (ys[i], foo[1].item()),
        (zs[i], foo[2].item()), 'k'
    )

mid_x = foo[0]
mid_y = foo[1]
mid_z = foo[2]
max_range = radius * 1.0
ax.set_xlim(mid_x - max_range, mid_x + max_range)
ax.set_ylim(mid_y - max_range, mid_y + max_range)
ax.set_zlim(mid_z - max_range, mid_z + max_range)

plt.show()
