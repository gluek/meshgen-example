# Copyright 2013 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

from devsim import *
from devsim.python_packages.simple_physics import *
import diode_common

def print_currents(device, contact):
    """
    Print out contact currents
    """
    ece_name = "ElectronContinuityEquation"
    hce_name = "HoleContinuityEquation"
    contact_bias_name = GetContactBiasName(contact)
    electron_current= get_contact_current(device=device, contact=contact, equation=ece_name)
    hole_current    = get_contact_current(device=device, contact=contact, equation=hce_name)
    total_current   = electron_current + hole_current
    voltage = get_parameter(device=device, name=GetContactBiasName(contact))
    data = (voltage, electron_current, hole_current, total_current)
    print(f"{contact:10}{voltage:+.3e}\t{electron_current:+.3e}\t{hole_current:+.3e}\t{total_current:+.3e}")
    return data

def print_all_currents():
    """
    Prints all currents to console and returns outmap of values. !Currently only functional when all contacts are
    silicon contacts!
    :return:
    """
    print("\nSolution:")
    print("{0:10}{1:15}{2:12}{3:12}{4:10}".format("Contact", "Voltage", "Electron", "Hole", "Total"))
    print("                         Current     Current     Current")
    device_list = get_device_list()
    for device in device_list:
        contact_list = get_contact_list(device=device)
        outmap = {}
        for contact in contact_list:
                outmap[contact] = print_currents(device, contact)
    return outmap

device = "nVolume"
region = "Bulk"

diode_common.Create3DGmshMesh(device, region, "./Out/nVolume_contacts_scaling_1.msh.msh")

diode_common.SetParameters(device=device, region=region)
set_parameter(device=device, region=region, name="mu_n", value=1)
set_parameter(device=device, region=region, name="mu_p", value=1)

# this is the devsim format
write_devices (file="./Out/nVolume_devsim_out.msh")

set_parameter(name="extended_solver", value="True")
set_parameter(name="extended_model", value="True")
set_parameter(name="extended_equation", value="True")

####
#### NetDoping
####
node_model(device=device, region=region, name="Acceptors", equation="0.0")
node_model(device=device, region=region, name="Donors",    equation="1.0/1.6*1e19")
node_model(device=device, region=region, name="NetDoping", equation="Donors-Acceptors;")

diode_common.InitialSolution(device, region)

####
#### Initial DC solution
####
solve(type="dc", absolute_error=1.0, relative_error=1e-12, maximum_iterations=100)

###
### Drift diffusion simulation at equilibrium
###

diode_common.DriftDiffusionInitialSolution(device, region)

solve(type="dc", absolute_error=1e-10, relative_error=1e-12, maximum_iterations=50)

v = 0.1
while v < 1.01:
    set_parameter(device=device, name=GetContactBiasName("top"), value=v)
    solve(type="dc", absolute_error=1e-10, relative_error=1e-12, maximum_iterations=30)
    print_all_currents()
    v += 0.1

element_from_edge_model(edge_model="ElectricField",   device=device, region=region)
element_from_edge_model(edge_model="ElectronCurrent", device=device, region=region)
element_from_edge_model(edge_model="HoleCurrent",     device=device, region=region)

#write_devices(file="gmsh_nVolume_dd.dat", type="tecplot")
#write_devices(file="gmsh_nVolume_dd.msh", type="devsim")
#write_devices(file="gmsh_nVolume_dd.msh", type="vtk")

