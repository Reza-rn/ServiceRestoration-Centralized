from OpenDSSInit import *
import sys
from Functions import *
import math
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 400
import time
# ****************************************************
# * Start of time
# ****************************************************
StartTime = time.time ()

# ****************************************************
# * DSS Object
# ****************************************************
# create DSS object of the circuit
Ckt = DSS()

# Load 100k-Node
FolderName = sys.argv[0][:-7]
Ckt.dssText.Command = r"Compile '"+FolderName+ "/Test_Network/Master.dss"; CktNum = 4

# EnergyMeter
if CktNum == 4:
    Ckt.dssText.command = "New Energymeter.m1 Line.SwMainLine 1"


#==================================================================================
# Set Maximum iterations
Ckt.dssText.command = "Set Maxiterations=200"

# Solve the Circuit
Ckt.Solve()
if Ckt.dssSolution.Converged:
    #print("The Circuit Solved Successfully")
    print("The OpenDSS Connection Established Successfully")
else:
    print('Unsuccessful Connection')

# ****************************************************
# * End defining circuit
# ****************************************************
# ************************************************
# Get all the list of all buses, lines and loads
AllLines = Ckt.dssCircuit.Lines.AllNames
AllBuses = Ckt.dssCircuit.AllBusNames
AllLoads = Ckt.dssCircuit.Loads.AllNames
# print(AllBuses)
CktIncMatrix = Ckt.IncMatrix()
AllPDElements = Ckt.FindAllPDElements()


# ****************************************************
# * Find parent Buses of each Bus
# ****************************************************
# Calculate PD Elements connections
PDElementsConnections = PDElementsConnectionsFind(CktIncMatrix, AllPDElements,
                                                  Ckt.dssCircuit.Solution.IncMatrixcols)

# Find Parent set
ParentBus = FindParentBus(PDElementsConnections)

#Reduced PD Elements
RemovedPDElements = FindRemovedPDElemnts(PDElementsConnections)
AllPDElementsReduced = RemovedPDElements[0]
PDElementsConnectionsReduced = RemovedPDElements[1]
ReplacedRemovedPDElements = RemovedPDElements[2]
RemovedPDElements = RemovedPDElements[3]

# ****************************************************
# * Find children Buses of each Bus
# ****************************************************
ChildrenBuses = FindChildrenBuses(ParentBus)

# ****************************************************
# * Find neighbor PD Elements of each bus
# ****************************************************
BusNeighborPDElements = FindBusNeighborPDElements(AllBuses, PDElementsConnections)

# ****************************************************
# * Find neighbor Buses each Bus
# ****************************************************
BusNeighborBuses = FindBusNeighborBuses(AllBuses, BusNeighborPDElements, PDElementsConnections)

# ****************************************************
# * Find children lines of each line
# ****************************************************
ChildrenLines = FindChildrenLines(PDElementsConnections)

# ****************************************************
# * Find PD Element Phase Matrix
# ****************************************************
PDElementPhaseMatrix = FindPDElementPhaseMatrix(Ckt, AllPDElements)

# ****************************************************
# * Find Buses Phase Matrix
# ****************************************************
BusesPhaseMatrix = FindBusesPhaseMatrix(Ckt, AllBuses)
# print(BusesPhaseMatrix['300'])


# *************************************************************
# * Find S_Base and V_Base and Z_Base and circuit parameters
# *************************************************************
#SourceBus = Ckt.FindSourceBus()
SourceBus = ['sourcebus']
SubPDElement = FindFirstPDElement(PDElementsConnections, SourceBus)  # find connected PD element to the source bus
Source={}; Source[SourceBus[0]] = SubPDElement

# Add another source
#SourceBus.append('sourcebus2')
Source = FindSourcebusConnection(Source, SourceBus, PDElementsConnections, ParentBus)

S_Base = Ckt.FindS_Base()
V_Base = Ckt.FindV_Base()
Z_Base = (V_Base**2)*1000/S_Base  # Base Impedance-region 1
I_Base = S_Base/(math.sqrt(3)*V_Base)  # Base current
L_Base = I_Base**2        # square of current base;
PhasesNum = 3  # distribution networks phase numbers
PhaseSequence = ['a', 'b', 'c']

# *************************************************************
# * Loads Data
# *************************************************************
# Load connections
LoadsConnection = FindLoadsConnections(Ckt, S_Base)

# Load to Bus Connection matrix
LoadToBus = FindLoadToBus(AllBuses, LoadsConnection)

# Loads Maximum capacity
Loads_max = FindLoadsCapacity(Ckt, S_Base)

# Modify secondary loads
[AllLoadsModi, LoadToBusModi, LoadsConnectionModi, Loads_maxModi] = ModifySecondaryLoad(CktNum, Ckt, AllLoads,
                                            ParentBus,PDElementsConnections, LoadsConnection, Loads_max, LoadToBus)

# Loads priority or weight
LoadsWeight = FindLoadsWeight(AllLoadsModi)#, t5293655aload=5, t5293655bload=5, t5293655cload=5)


# ************************************************************************
# Load Type matrix
# ***********************************************************************
# 1 mean non-dispatchable
# pass load name to function if you want to change it into non-dispatchable
DispatchableLoads = []#'675c']
LoadType = DefineLoadType(AllLoadsModi, DispatchableLoads)

# ************************************************************************
# Lines
# ***********************************************************************
# Lines Length (The unit length of ckt 123-nodes is kft)
LinesLength = FindLinesLength(Ckt)

# Lines Capacity
LinesSquareCapacity = FindLinesSquareCapacity(Ckt, I_Base)

# Line Resistance (Ohm/units)
LinesResistance = FindLinesResistance(Ckt, AllLines)

# Line Reactance (Ohm/units)
LinesReactance = FindLinesReactance(Ckt, AllLines)

# ************************************************************************
# PD Elements = Lines + Transformers
# ***********************************************************************
# All PD Elements Length
PDElementsLength = FindPDElementLength(AllPDElements, LinesLength)

# All PD Elements Capacity
PDElementsSquareCapacity = FindPDElementsSquareCapacity(AllPDElements, LinesSquareCapacity)

# Integrate all PD Elements Resistance
PDElementsR = FindPDElementsR(AllPDElements, PDElementPhaseMatrix, LinesResistance, PDElementsLength, Z_Base)

# Integrate all PD Elements Reactance
PDElementsX = FindPDElementsX(AllPDElements, PDElementPhaseMatrix, LinesReactance, PDElementsLength, Z_Base)

# PD Elements R_hat resistance:
PDElementsR_hat = CalculatePDElements_R_hat(PDElementsR, PDElementsX, math.sqrt, np)

# PD Elements X_hat resistance:
PDElementsX_hat = CalculatePDElements_X_hat(PDElementsX, PDElementsR, math.sqrt, np)

# PD Elements X_hat resistance:
PDElementsZ_hat = CalculatePDElements_Z_hat(PDElementsR, PDElementsX, math.sqrt)


# *****************************************************************************
# PV
# *****************************************************************************
# define PV matrix Bus connection which first is PV capacity
PVconnection = FindPVConnection(Ckt, S_Base, Busm1026706=[1000, 1], Busm1047592=[1000, 1], Busc3_m1026706=[2000, 1],
                                Busc3_m1047592=[1000, 1])
PVBus = FindPVtoBus(AllBuses, PVconnection)

# *****************************************************************************
# Distribution Lines' capacity
# *****************************************************************************
# Switchable lines, all lines name like Line.sw... considers as switchable, also other lines can be added to end of
# this function to be considered as switchable
SwitchableLines = FindSwitchableLines(AllPDElements) #, 'Line.110')

#Normlly open switches can have higher wieght
if CktNum == 3:
    NormallyCloseSwitches = ['Line.swx8223_48332_sw', 'Line.swv7173_48332_sw', 'Line.swv9287_48332_sw',
                         'Line.swa8735_48332_sw', 'Line.swl5437_48332_sw', 'Line.swln4625713_sw', 'Line.swln4641075_sw',
                         'Line.swl5491_48332_sw', 'Line.swln4625696_sw', 'Line.swln4586093_sw', 'Line.swl5659_48332_sw',
                         'Line.swln3693186_sw', 'Line.swv7313_48332_sw', 'Line.swa8611_48332_sw', 'Line.swln4625876_sw',
                         'Line.swv9111_48332_sw', 'Line.swx8271_48332_sw', 'Line.swv7041_48332_sw',
                         'Line.swl5397_48332_sw', 'Line.swln247171_sw', 'Line.swl5523_48332_sw',
                         'Line.sw2002200004641085_sw', 'Line.swxj171_48332_sw', 'Line.swa8869_48332_sw',
                         'Line.sw2002200004991174_sw', 'Line.swl9191_48332_sw', 'Line.swln0247162_sw',
                         'Line.swln247160_sw', 'Line.swln293471_sw', 'Line.swa8645_48332_sw', 'Line.swv9109_48332_sw',
                         'Line.swg9343_48332_sw', 'Line.swl5565_48332_sw', 'Line.swa333_48332_sw', 'Line.swln4625680_sw',
                         'Line.sw175078', 'Line.sw183046', 'Line.sw246178', 'Line.sw249319', 'Line.sw254077',
                         'Line.sw255376', 'Line.sw261249', 'Line.sw298361', 'Line.sw298362']
elif CktNum == 2:
    NormallyCloseSwitches = ['Line.swx8223_48332_sw', 'Line.swv7173_48332_sw', 'Line.swv9287_48332_sw',
                             'Line.swa8735_48332_sw', 'Line.swl5437_48332_sw', 'Line.swln4625713_sw',
                             'Line.swln4641075_sw',
                             'Line.swl5491_48332_sw', 'Line.swln4625696_sw', 'Line.swln4586093_sw',
                             'Line.swl5659_48332_sw',
                             'Line.swln3693186_sw', 'Line.swv7313_48332_sw', 'Line.swa8611_48332_sw',
                             'Line.swln4625876_sw',
                             'Line.swv9111_48332_sw', 'Line.swx8271_48332_sw', 'Line.swv7041_48332_sw',
                             'Line.swl5397_48332_sw', 'Line.swln247171_sw', 'Line.swl5523_48332_sw',
                             'Line.sw2002200004641085_sw', 'Line.swxj171_48332_sw', 'Line.swa8869_48332_sw',
                             'Line.sw2002200004991174_sw', 'Line.swl9191_48332_sw', 'Line.swln0247162_sw',
                             'Line.swln247160_sw', 'Line.swln293471_sw', 'Line.swa8645_48332_sw',
                             'Line.swv9109_48332_sw',
                             'Line.swg9343_48332_sw', 'Line.swl5565_48332_sw', 'Line.swa333_48332_sw',
                             'Line.swln4625680_sw']
elif CktNum == 4:
    NormallyCloseSwitches = ['Line.swmainline', 'Line.swx8223_48332_sw', 'Line.swv7173_48332_sw', 'Line.swv9287_48332_sw', 'Line.swa8735_48332_sw',
    'Line.swl5437_48332_sw', 'Line.swln4625713_sw', 'Line.swln4641075_sw', 'Line.swl5491_48332_sw', 'Line.swln4625696_sw',
    'Line.swln4586093_sw', 'Line.swl5659_48332_sw', 'Line.swln3693186_sw', 'Line.swv7313_48332_sw', 'Line.swa8611_48332_sw',
    'Line.swln4625876_sw', 'Line.swv9111_48332_sw', 'Line.swx8271_48332_sw', 'Line.swv7041_48332_sw', 'Line.swl5397_48332_sw',
    'Line.swln247171_sw', 'Line.swl5523_48332_sw', 'Line.sw2002200004641085_sw', 'Line.swxj171_48332_sw', 'Line.swa8869_48332_sw',
    'Line.swl9407_48332_sw', 'Line.swx8225_48332_sw', 'Line.sw2002200004868472_sw', 'Line.sw2002200004991174_sw',
    'Line.swl9191_48332_sw', 'Line.swln0247162_sw', 'Line.swln247160_sw', 'Line.swln5686080-1', 'Line.swa8645_48332_sw',
    'Line.swv9109_48332_sw', 'Line.swg9343_48332_sw', 'Line.swl5565_48332_sw', 'Line.swa333_48332_sw', 'Line.swln4625680_sw',
    'Line.swc1_x8223_48332_sw', 'Line.swc1_v7173_48332_sw', 'Line.swc1_v9287_48332_sw', 'Line.swc1_a8735_48332_sw',
    'Line.swc1_l5437_48332_sw', 'Line.swc1_ln4625713_sw', 'Line.swc1_ln4641075_sw', 'Line.swc1_l5491_48332_sw',
    'Line.swc1_ln4625696_sw', 'Line.swc1_ln4586093_sw', 'Line.swc1_l5659_48332_sw', 'Line.swc1_ln3693186_sw',
    'Line.swc1_v7313_48332_sw', 'Line.swc1_a8611_48332_sw', 'Line.swc1_ln4625876_sw', 'Line.swc1_v9111_48332_sw',
    'Line.swc1_x8271_48332_sw', 'Line.swc1_v7041_48332_sw', 'Line.swc1_l5397_48332_sw', 'Line.swc1_ln247171_sw',
    'Line.swc1_l5523_48332_sw', 'Line.swc1_2002200004641085_sw', 'Line.swc1_xj171_48332_sw', 'Line.swc1_a8869_48332_sw',
    'Line.swc1_l9407_48332_sw', 'Line.swc1_x8225_48332_sw', 'Line.swc1_2002200004868472_sw', 'Line.swc1_2002200004991174_sw',
    'Line.swc1_l9191_48332_sw', 'Line.swc1_ln0247162_sw', 'Line.swc1_ln247160_sw', 'Line.swc1_ln293471_sw',
    'Line.swc1_a8645_48332_sw', 'Line.swc1_v9109_48332_sw', 'Line.swc1_g9343_48332_sw', 'Line.swc1_l5565_48332_sw',
    'Line.swc1_a333_48332_sw', 'Line.swc1_ln4625680_sw', 'Line.swc2_x8223_48332_sw', 'Line.swc2_v7173_48332_sw',
    'Line.swc2_v9287_48332_sw', 'Line.swc2_a8735_48332_sw', 'Line.swc2_l5437_48332_sw', 'Line.swc2_ln4625713_sw',
    'Line.swc2_ln4641075_sw', 'Line.swc2_l5491_48332_sw', 'Line.swc2_ln4625696_sw', 'Line.swc2_ln4586093_sw',
    'Line.swc2_l5659_48332_sw', 'Line.swc2_ln3693186_sw', 'Line.swc2_v7313_48332_sw', 'Line.swc2_a8611_48332_sw',
    'Line.swc2_ln4625876_sw', 'Line.swc2_v9111_48332_sw', 'Line.swc2_x8271_48332_sw', 'Line.swc2_v7041_48332_sw',
    'Line.swc2_l5397_48332_sw', 'Line.swc2_ln247171_sw', 'Line.swc2_l5523_48332_sw', 'Line.swc2_2002200004641085_sw',
    'Line.swc2_xj171_48332_sw', 'Line.swc2_a8869_48332_sw', 'Line.swc2_l9407_48332_sw', 'Line.swc2_x8225_48332_sw',
    'Line.swc2_2002200004868472_sw', 'Line.swc2_2002200004991174_sw', 'Line.swc2_l9191_48332_sw', 'Line.swc2_ln0247162_sw',
    'Line.swc2_ln247160_sw', 'Line.swc2_ln293471_sw', 'Line.swc2_a8645_48332_sw', 'Line.swc2_v9109_48332_sw',
    'Line.swc2_g9343_48332_sw', 'Line.swc2_l5565_48332_sw', 'Line.swc2_a333_48332_sw', 'Line.swc2_ln4625680_sw',
    'Line.swc3_x8223_48332_sw', 'Line.swc3_v7173_48332_sw', 'Line.swc3_v9287_48332_sw', 'Line.swc3_a8735_48332_sw',
    'Line.swc3_l5437_48332_sw', 'Line.swc3_ln4625713_sw', 'Line.swc3_ln4641075_sw', 'Line.swc3_l5491_48332_sw',
    'Line.swc3_ln4625696_sw', 'Line.swc3_ln4586093_sw', 'Line.swc3_l5659_48332_sw', 'Line.swc3_ln3693186_sw',
    'Line.swc3_v7313_48332_sw', 'Line.swc3_a8611_48332_sw', 'Line.swc3_ln4625876_sw', 'Line.swc3_v9111_48332_sw',
    'Line.swc3_x8271_48332_sw', 'Line.swc3_v7041_48332_sw', 'Line.swc3_l5397_48332_sw', 'Line.swc3_ln247171_sw',
    'Line.swc3_l5523_48332_sw', 'Line.swc3_2002200004641085_sw', 'Line.swc3_xj171_48332_sw', 'Line.swc3_a8869_48332_sw',
    'Line.swc3_l9407_48332_sw', 'Line.swc3_x8225_48332_sw', 'Line.swc3_2002200004868472_sw', 'Line.swc3_2002200004991174_sw',
    'Line.swc3_l9191_48332_sw', 'Line.swc3_ln0247162_sw', 'Line.swc3_ln247160_sw', 'Line.swc3_ln293471_sw',
    'Line.swc3_a8645_48332_sw', 'Line.swc3_v9109_48332_sw', 'Line.swc3_g9343_48332_sw', 'Line.swc3_l5565_48332_sw',
    'Line.swc3_a333_48332_sw', 'Line.swc3_ln4625680_sw', 'Line.swc4_x8223_48332_sw', 'Line.swc4_v7173_48332_sw',
    'Line.swc4_v9287_48332_sw', 'Line.swc4_a8735_48332_sw', 'Line.swc4_l5437_48332_sw', 'Line.swc4_ln4625713_sw',
    'Line.swc4_ln4641075_sw', 'Line.swc4_l5491_48332_sw', 'Line.swc4_ln4625696_sw', 'Line.swc4_ln4586093_sw',
    'Line.swc4_l5659_48332_sw', 'Line.swc4_ln3693186_sw', 'Line.swc4_v7313_48332_sw', 'Line.swc4_a8611_48332_sw',
    'Line.swc4_ln4625876_sw', 'Line.swc4_v9111_48332_sw', 'Line.swc4_x8271_48332_sw', 'Line.swc4_v7041_48332_sw',
    'Line.swc4_l5397_48332_sw', 'Line.swc4_ln247171_sw', 'Line.swc4_l5523_48332_sw', 'Line.swc4_2002200004641085_sw',
    'Line.swc4_xj171_48332_sw', 'Line.swc4_a8869_48332_sw', 'Line.swc4_l9407_48332_sw', 'Line.swc4_x8225_48332_sw',
    'Line.swc4_2002200004868472_sw', 'Line.swc4_2002200004991174_sw', 'Line.swc4_l9191_48332_sw', 'Line.swc4_ln0247162_sw',
    'Line.swc4_ln247160_sw', 'Line.swc4_ln293471_sw', 'Line.swc4_a8645_48332_sw', 'Line.swc4_v9109_48332_sw',
    'Line.swc4_g9343_48332_sw', 'Line.swc4_l5565_48332_sw', 'Line.swc4_a333_48332_sw', 'Line.swc4_ln4625680_sw',
    'Line.swc5_x8223_48332_sw', 'Line.swc5_v7173_48332_sw', 'Line.swc5_v9287_48332_sw', 'Line.swc5_a8735_48332_sw',
    'Line.swc5_l5437_48332_sw', 'Line.swc5_ln4625713_sw', 'Line.swc5_ln4641075_sw', 'Line.swc5_l5491_48332_sw',
    'Line.swc5_ln4625696_sw', 'Line.swc5_ln4586093_sw', 'Line.swc5_l5659_48332_sw', 'Line.swc5_ln3693186_sw',
    'Line.swc5_v7313_48332_sw', 'Line.swc5_a8611_48332_sw', 'Line.swc5_ln4625876_sw', 'Line.swc5_v9111_48332_sw',
    'Line.swc5_x8271_48332_sw', 'Line.swc5_v7041_48332_sw', 'Line.swc5_l5397_48332_sw', 'Line.swc5_ln247171_sw',
    'Line.swc5_l5523_48332_sw', 'Line.swc5_2002200004641085_sw', 'Line.swc5_xj171_48332_sw', 'Line.swc5_a8869_48332_sw',
    'Line.swc5_l9407_48332_sw', 'Line.swc5_x8225_48332_sw', 'Line.swc5_2002200004868472_sw', 'Line.swc5_2002200004991174_sw',
    'Line.swc5_l9191_48332_sw', 'Line.swc5_ln0247162_sw', 'Line.swc5_ln247160_sw', 'Line.swc5_ln293471_sw',
    'Line.swc5_a8645_48332_sw', 'Line.swc5_v9109_48332_sw', 'Line.swc5_g9343_48332_sw', 'Line.swc5_l5565_48332_sw',
    'Line.swc5_a333_48332_sw', 'Line.swc5_ln4625680_sw', 'Line.swc6_x8223_48332_sw', 'Line.swc6_v7173_48332_sw',
    'Line.swc6_v9287_48332_sw', 'Line.swc6_a8735_48332_sw', 'Line.swc6_l5437_48332_sw', 'Line.swc6_ln4625713_sw',
    'Line.swc6_ln4641075_sw', 'Line.swc6_l5491_48332_sw', 'Line.swc6_ln4625696_sw', 'Line.swc6_ln4586093_sw',
    'Line.swc6_l5659_48332_sw', 'Line.swc6_ln3693186_sw', 'Line.swc6_v7313_48332_sw', 'Line.swc6_a8611_48332_sw',
    'Line.swc6_ln4625876_sw', 'Line.swc6_v9111_48332_sw', 'Line.swc6_x8271_48332_sw', 'Line.swc6_v7041_48332_sw',
    'Line.swc6_l5397_48332_sw', 'Line.swc6_ln247171_sw', 'Line.swc6_l5523_48332_sw', 'Line.swc6_2002200004641085_sw',
    'Line.swc6_xj171_48332_sw', 'Line.swc6_a8869_48332_sw', 'Line.swc6_l9407_48332_sw', 'Line.swc6_x8225_48332_sw',
    'Line.swc6_2002200004868472_sw', 'Line.swc6_2002200004991174_sw', 'Line.swc6_l9191_48332_sw', 'Line.swc6_ln0247162_sw',
    'Line.swc6_ln247160_sw', 'Line.swc6_ln293471_sw', 'Line.swc6_a8645_48332_sw', 'Line.swc6_v9109_48332_sw',
    'Line.swc6_g9343_48332_sw', 'Line.swc6_l5565_48332_sw', 'Line.swc6_a333_48332_sw', 'Line.swc6_ln4625680_sw',
    'Line.swc7_x8223_48332_sw', 'Line.swc7_v7173_48332_sw', 'Line.swc7_v9287_48332_sw', 'Line.swc7_a8735_48332_sw',
    'Line.swc7_l5437_48332_sw', 'Line.swc7_ln4625713_sw', 'Line.swc7_ln4641075_sw', 'Line.swc7_l5491_48332_sw',
    'Line.swc7_ln4625696_sw', 'Line.swc7_ln4586093_sw', 'Line.swc7_l5659_48332_sw', 'Line.swc7_ln3693186_sw',
    'Line.swc7_v7313_48332_sw', 'Line.swc7_a8611_48332_sw', 'Line.swc7_ln4625876_sw', 'Line.swc7_v9111_48332_sw',
    'Line.swc7_x8271_48332_sw', 'Line.swc7_v7041_48332_sw', 'Line.swc7_l5397_48332_sw', 'Line.swc7_ln247171_sw',
    'Line.swc7_l5523_48332_sw', 'Line.swc7_2002200004641085_sw', 'Line.swc7_xj171_48332_sw', 'Line.swc7_a8869_48332_sw',
    'Line.swc7_l9407_48332_sw', 'Line.swc7_x8225_48332_sw', 'Line.swc7_2002200004868472_sw', 'Line.swc7_2002200004991174_sw',
    'Line.swc7_l9191_48332_sw', 'Line.swc7_ln0247162_sw', 'Line.swc7_ln247160_sw', 'Line.swc7_ln293471_sw',
    'Line.swc7_a8645_48332_sw', 'Line.swc7_v9109_48332_sw', 'Line.swc7_g9343_48332_sw', 'Line.swc7_l5565_48332_sw',
    'Line.swc7_a333_48332_sw', 'Line.swc7_ln4625680_sw', 'Line.swc8_x8223_48332_sw', 'Line.swc8_v7173_48332_sw',
    'Line.swc8_v9287_48332_sw', 'Line.swc8_a8735_48332_sw', 'Line.swc8_l5437_48332_sw', 'Line.swc8_ln4625713_sw',
    'Line.swc8_ln4641075_sw', 'Line.swc8_l5491_48332_sw', 'Line.swc8_ln4625696_sw', 'Line.swc8_ln4586093_sw',
    'Line.swc8_l5659_48332_sw', 'Line.swc8_ln3693186_sw', 'Line.swc8_v7313_48332_sw', 'Line.swc8_a8611_48332_sw',
    'Line.swc8_ln4625876_sw', 'Line.swc8_v9111_48332_sw', 'Line.swc8_x8271_48332_sw', 'Line.swc8_v7041_48332_sw',
    'Line.swc8_ln5867591-1', 'Line.swc8_l5397_48332_sw', 'Line.swc8_ln247171_sw', 'Line.swc8_l5523_48332_sw',
    'Line.swc8_2002200004641085_sw', 'Line.swc8_xj171_48332_sw', 'Line.swc8_a8869_48332_sw', 'Line.swc8_l9407_48332_sw',
    'Line.swc8_x8225_48332_sw', 'Line.swc8_2002200004868472_sw', 'Line.swc8_2002200004991174_sw', 'Line.swc8_l9191_48332_sw',
    'Line.swc8_ln0247162_sw', 'Line.swc8_ln247160_sw', 'Line.swc8_ln293471_sw', 'Line.swc8_a8645_48332_sw',
    'Line.swc8_v9109_48332_sw', 'Line.swc8_g9343_48332_sw', 'Line.swc8_l5565_48332_sw', 'Line.swc8_a333_48332_sw',
    'Line.swc8_ln4625680_sw', 'Line.swc9_x8223_48332_sw', 'Line.swc9_v7173_48332_sw', 'Line.swc9_v9287_48332_sw',
    'Line.swc9_a8735_48332_sw', 'Line.swc9_l5437_48332_sw', 'Line.swc9_ln4625713_sw', 'Line.swc9_ln4641075_sw',
    'Line.swc9_l5491_48332_sw', 'Line.swc9_ln4625696_sw', 'Line.swc9_ln4586093_sw', 'Line.swc9_l5659_48332_sw',
    'Line.swc9_ln3693186_sw', 'Line.swc9_v7313_48332_sw', 'Line.swc9_a8611_48332_sw', 'Line.swc9_ln4625876_sw',
    'Line.swc9_v9111_48332_sw', 'Line.swc9_x8271_48332_sw', 'Line.swc9_v7041_48332_sw', 'Line.swc9_l5397_48332_sw',
    'Line.swc9_ln247171_sw', 'Line.swc9_l5523_48332_sw', 'Line.swc9_2002200004641085_sw', 'Line.swc9_xj171_48332_sw',
    'Line.swc9_a8869_48332_sw', 'Line.swc9_l9407_48332_sw', 'Line.swc9_x8225_48332_sw', 'Line.swc9_2002200004868472_sw',
    'Line.swc9_2002200004991174_sw', 'Line.swc9_l9191_48332_sw', 'Line.swc9_ln0247162_sw', 'Line.swc9_ln247160_sw',
    'Line.swc9_ln293471_sw', 'Line.swc9_a8645_48332_sw', 'Line.swc9_v9109_48332_sw', 'Line.swc9_g9343_48332_sw',
    'Line.swc9_l5565_48332_sw', 'Line.swc9_a333_48332_sw', 'Line.swc9_ln4625680_sw', 'Line.swc10_x8223_48332_sw',
    'Line.swc10_v7173_48332_sw', 'Line.swc10_v9287_48332_sw', 'Line.swc10_a8735_48332_sw', 'Line.swc10_l5437_48332_sw',
    'Line.swc10_ln4625713_sw', 'Line.swc10_ln4641075_sw', 'Line.swc10_l5491_48332_sw', 'Line.swc10_ln4625696_sw',
    'Line.swc10_ln4586093_sw', 'Line.swc10_l5659_48332_sw', 'Line.swc10_ln3693186_sw', 'Line.swc10_v7313_48332_sw',
    'Line.swc10_a8611_48332_sw', 'Line.swc10_ln4625876_sw', 'Line.swc10_v9111_48332_sw', 'Line.swc10_x8271_48332_sw',
    'Line.swc10_v7041_48332_sw', 'Line.swc10_l5397_48332_sw', 'Line.swc10_ln247171_sw', 'Line.swc10_l5523_48332_sw',
    'Line.swc10_2002200004641085_sw', 'Line.swc10_xj171_48332_sw', 'Line.swc10_a8869_48332_sw', 'Line.swc10_l9407_48332_sw',
    'Line.swc10_x8225_48332_sw', 'Line.swc10_2002200004868472_sw', 'Line.swc10_2002200004991174_sw',
    'Line.swc10_l9191_48332_sw', 'Line.swc10_ln0247162_sw', 'Line.swc10_ln247160_sw', 'Line.swc10_ln293471_sw',
    'Line.swc10_a8645_48332_sw', 'Line.swc10_v9109_48332_sw', 'Line.swc10_g9343_48332_sw', 'Line.swc10_l5565_48332_sw',
    'Line.swc10_a333_48332_sw', 'Line.swc10_ln4625680_sw', 'Line.swc11_x8223_48332_sw', 'Line.swc11_v7173_48332_sw',
    'Line.swc11_v9287_48332_sw', 'Line.swc11_a8735_48332_sw', 'Line.swc11_l5437_48332_sw', 'Line.swc11_ln4625713_sw',
    'Line.swc11_ln4641075_sw', 'Line.swc11_l5491_48332_sw', 'Line.swc11_ln4625696_sw', 'Line.swc11_ln4586093_sw',
    'Line.swc11_l5659_48332_sw', 'Line.swc11_ln3693186_sw', 'Line.swc11_v7313_48332_sw', 'Line.swc11_a8611_48332_sw',
    'Line.swc11_ln4625876_sw', 'Line.swc11_v9111_48332_sw', 'Line.swc11_x8271_48332_sw', 'Line.swc11_v7041_48332_sw',
    'Line.swc11_l5397_48332_sw', 'Line.swc11_ln247171_sw', 'Line.swc11_l5523_48332_sw', 'Line.swc11_2002200004641085_sw',
    'Line.swc11_xj171_48332_sw', 'Line.swc11_a8869_48332_sw', 'Line.swc11_l9407_48332_sw', 'Line.swc11_x8225_48332_sw',
    'Line.swc11_2002200004868472_sw', 'Line.swc11_2002200004991174_sw', 'Line.swc11_l9191_48332_sw', 'Line.swc11_ln0247162_sw',
    'Line.swc11_ln247160_sw', 'Line.swc11_ln293471_sw', 'Line.swc11_a8645_48332_sw', 'Line.swc11_v9109_48332_sw',
    'Line.swc11_g9343_48332_sw', 'Line.swc11_l5565_48332_sw', 'Line.swc11_a333_48332_sw', 'Line.swc11_ln4625680_sw']
else:
    NormallyCloseSwitches = ['Line.sw1', 'Line.sw2', 'Line.sw3', 'Line.sw4', 'Line.sw5']

SwitchableLineWeight = DefineSwitchWeight(SwitchableLines, NormallyCloseSwitches, 5) #third entry is weight of NC Sw.

# Switches for Lines
Switches_Lines = FindSwitches(SwitchableLines)

# *****************************************************************************
# CapacitorBanks
# *****************************************************************************
CapacitorConnection = FindCapacitorConnection(Ckt)
CapacitorBus = FindCapacitorToBus(AllBuses, CapacitorConnection)

# *****************************************************************************
# X_Y coordinates
# *****************************************************************************
XY_Coordinates = FindXY_Coordinates(Ckt)
#print(XY_Coordinates)

# Modify coordinates for switches in IEEE 8500 node system
if CktNum != 1:
    XY_Coordinates = ModifySwitchesCoordinates(XY_Coordinates, SwitchableLines, PDElementsConnections, ParentBus,
                                               ChildrenBuses)

# *****************************************************************************
print(AllBuses)

EndNetworkLoadingTime = time.time()



