# ******************************************************************************************
#  *** This function returns connection of PD elements in terms of the buses
# ******************************************************************************************
def PDElementsConnectionsFind(CktIncMatrix, AllPDElements, AllBuses):
    i = 0;
    PDElementsConnections = {}
    while i <= len(CktIncMatrix) - 6:
        if CktIncMatrix[i + 2] == 1:
            To = AllBuses[CktIncMatrix[i + 1]]
            In = AllBuses[CktIncMatrix[i + 4]]
        else:
            To = AllBuses[CktIncMatrix[i + 4]]
            In = AllBuses[CktIncMatrix[i + 1]]
        PDElementsConnections[AllPDElements[CktIncMatrix[i]]] = (To, In)
        i = i + 6
    return PDElementsConnections

# ******************************************************************************************
#  *** This function is used to find removed PD Elements because of same connection buses
# ******************************************************************************************
def FindRemovedPDElemnts(PDElementsConnections):

    Removed={}
    RemovedConnection = []
    PDElementsConnectionsReduced = PDElementsConnections.copy()

    for i, j in PDElementsConnections.items():
        for k, m in PDElementsConnections.items():
            if i != k:
                if j == m:
                    if m not in RemovedConnection:
                        RemovedConnection.append(m)
                        Removed[k] = i
                        del PDElementsConnectionsReduced[k]

    AllPDElementsReduced = list(PDElementsConnectionsReduced.keys())

    ReplacedRemoved={}
    for i, j in Removed.items():
        if j in ReplacedRemoved:
            ReplacedRemoved[j].append(i)
        else:
            ReplacedRemoved[j] = i

    return [AllPDElementsReduced, PDElementsConnectionsReduced, ReplacedRemoved, Removed]

# ******************************************************************************************
# *** This function is to find parent buses of each bus using PDElementsConnections
# ******************************************************************************************
def FindParentBus(PDElementsConnections):
    x={}
    for i in PDElementsConnections:
        x[PDElementsConnections[i][1]] = PDElementsConnections[i][0]
    return x


# ******************************************************************************************
# *** This function is to find children buses of each bus using Parent matrix
# ******************************************************************************************
def FindChildrenBuses(Parent):
    Children = {}
    for i, j in Parent.items():
        NumChild = 0
        TempParent = j
        TempChild = [i]
        for k, m in Parent.items():
            if i != k:
                if j == m:
                    NumChild += 1
                    TempChild.append(k)
        Children[TempParent] = TempChild

    return Children

# ******************************************************************************************
# *** This function is used to find Neighbor PD Elements of each bus
# ******************************************************************************************
def FindBusNeighborPDElements(AllBuses, PDElementsConnections):
    Neighbor={}
    for i in AllBuses:
        for j, k in PDElementsConnections.items():
            if (k[0] == i) or (k[1] == i):
                if i in Neighbor:
                    Neighbor[i].append(j)
                else:
                    Neighbor[i] = [j]

    return Neighbor

# ******************************************************************************************
# *** This function is used to find Neighbor Buses of each Bus
# ******************************************************************************************
def FindBusNeighborBuses(AllBuses, BusNeighborPDElements, PDElementsConnections):
    Neighbor={}
    for i in AllBuses:
        for j in BusNeighborPDElements[i]:
            if PDElementsConnections[j][0] == i:
                if i in Neighbor:
                    if PDElementsConnections[j][1] not in Neighbor[i]:
                        Neighbor[i].append(PDElementsConnections[j][1])
                else:
                    Neighbor[i] = [PDElementsConnections[j][1]]

            elif PDElementsConnections[j][1] == i:
                if i in Neighbor:
                    if PDElementsConnections[j][0] not in Neighbor[i]:
                        Neighbor[i].append(PDElementsConnections[j][0])
                else:
                    Neighbor[i] = [PDElementsConnections[j][0]]

    return Neighbor
# ******************************************************************************************
# *** This function is organized Neighbor PD Elemtns for considering a constraint
# ******************************************************************************************
def OrganizeNeighborPDElements(time, Bus, x_Line, x_MT, x_PV, BusNeighborPDElements, MTBus, PVBus):
    Neighbor = 0
    for i in BusNeighborPDElements[Bus]:
        Neighbor = Neighbor + x_Line[i, time]

    # If MT connects to this Bus
    if MTBus[Bus] != []:
        Neighbor = Neighbor + x_MT[MTBus[Bus][0], time]

    # If PV connects to this Bus
    if PVBus[Bus] != []:
        Neighbor = Neighbor + x_PV[PVBus[Bus][0], time]

    return Neighbor

# ******************************************************************************************
# *** This function is organized Neighbor PD Elemtns for considering a constraint
# ******************************************************************************************
def OrganizeNeighborPDElementsWithoutDERs(time, Bus, x_Line, BusNeighborPDElements):
    Neighbor = 0
    for i in BusNeighborPDElements[Bus]:
        Neighbor = Neighbor + x_Line[i, time]

    return Neighbor

# ***************************************************************************************************
# *** This function is to find children lines of each lines using PD Elements connection matrix
# ***************************************************************************************************
def FindChildrenLines(PDElementsConnections):
    Children={}
    for i, j in PDElementsConnections.items():
        TempChildren=[]
        for k, m in PDElementsConnections.items():
            if i is not k:
                if (j[1] is m[0]) or (j[1] is m[1]):
                    TempChildren.append(k)
        Children[i] = TempChildren

    return Children

# ***************************************************************************************************
# *** This function returns Phase Connection matrix of all PD Elements
# ***************************************************************************************************

def FindPDElementPhaseMatrix(Ckt,AllPDElements):
    PDElementPhaseConnection = {}
    for i in AllPDElements:
        Element = i.split('.')[0]
        Name = i.split('.')[1]
        PDElementPhaseConnection[i] = [0, 0, 0]
        Ckt.dssCircuit.SetActiveElement('{}.{}'.format(Element, Name))
        NumPhases = Ckt.dssCircuit.ActiveCktElement.NumPhases
        if NumPhases != 0:
            if Element == 'Line':
                for j in range(NumPhases):
                    PDElementPhaseConnection[i][Ckt.dssCircuit.ActiveCktElement.NodeOrder[j] - 1] = 1

            if Element == 'Transformer':
                for j in range(NumPhases):
                    PDElementPhaseConnection[i][Ckt.dssCircuit.ActiveCktElement.NodeOrder[j] - 1] = 1

            if Element == 'Reactor':
                for j in range(NumPhases):
                    PDElementPhaseConnection[i][Ckt.dssCircuit.ActiveCktElement.NodeOrder[j] - 1] = 1

    return PDElementPhaseConnection

# ***************************************************************************************************
# *** This function returns Phase Connection matrix of all buses
# ***************************************************************************************************
def FindBusesPhaseMatrix(Ckt,AllBuses):
    BusesPhaseMatrix={}
    for i in AllBuses:
        BusesPhaseMatrix[i]=[0,0,0]
        Ckt.dssCircuit.SetActiveBus(i)
        NumNodes = Ckt.dssCircuit.ActiveBus.NumNodes
        if NumNodes > 3:
            NumNodes=3
        if NumNodes != 0:
            for j in range(NumNodes):
                BusesPhaseMatrix[i][Ckt.dssCircuit.ActiveBus.Nodes[j] - 1] = 1


    return BusesPhaseMatrix

# ***************************************************************************************************
# *** This function finds connection matrix of each load connection
# ***************************************************************************************************
def FindLoadsConnections(Ckt, S_Base):
    LoadToBus={}
    stop = Ckt.dssCircuit.Loads.First
    while stop:
        name = Ckt.dssCircuit.Loads.Name
        Ckt.dssCircuit.SetActiveElement('Load.{}'.format(name))
        P = (Ckt.dssCircuit.Loads.kW)/S_Base
        Q = (Ckt.dssCircuit.Loads.kvar)/S_Base
        if Ckt.dssCircuit.Loads.IsDelta:
            Phases = [0, 0, 0]
            NumPhases = Ckt.dssCircuit.ActiveCktElement.NumPhases
            BusConnection = Ckt.dssCircuit.ActiveCktElement.BusNames[0].split('.')
            BusName = BusConnection[0]

            if NumPhases == 3:
                Phases = [1, 1, 1]
            elif NumPhases == 2:
                Phases[int(BusConnection[1]) - 1] = 1
                Phases[int(BusConnection[2]) - 1] = 1
            elif NumPhases == 1:
                Phases[int(BusConnection[1]) - 1] = 1


            LoadToBus[name] = [BusName, NumPhases, Phases, P, Q]

        else:
            Phases = [0, 0, 0]
            NumPhases = Ckt.dssCircuit.ActiveCktElement.NumPhases
            BusConnection = Ckt.dssCircuit.ActiveCktElement.BusNames[0].split('.')
            BusName = BusConnection[0]
            if NumPhases == 3:
                Phases = [1, 1, 1]
            else:
                for i in range(NumPhases):
                    Phases[int(BusConnection[i+1])-1] = 1
            LoadToBus[name] = [BusName, NumPhases, Phases, P, Q]

        stop = Ckt.dssCircuit.Loads.Next

    return LoadToBus
# ***************************************************************************************************
# *** This function finds connection matrix of each load to the bus
# ***************************************************************************************************
def FindLoadToBus(AllBuses, LoadConnections):
    LoadToBus = {}
    for i in AllBuses:
        for k, m in LoadConnections.items():
            if i == m[0]:
                if i in LoadToBus.keys():
                    LoadToBus[i].append(k)
                else:
                    LoadToBus[i] = [k]

    return LoadToBus

# ***************************************************************************************************
# *** Find Capacitor banks connection
# ***************************************************************************************************
def FindLoadsWeight(AllLoads, **kwargs):
    LoadsWieght = {}
    for i in AllLoads:
        LoadsWieght[i] = 1

    if len(kwargs):
        for i, v in kwargs.items():
            Load = '{}'.format(i)
            if Load in LoadsWieght:
                LoadsWieght[Load] = v

    return LoadsWieght

# ***************************************************************************************************
# *** This function finds maximum capacity of the loads
# ***************************************************************************************************
def FindLoadsCapacity(Ckt,S_Base):
    LoadsCapacity={}
    Ckt.dssCircuit.Loads.First
    LoadName=Ckt.dssCircuit.Loads.Name
    Power = [(Ckt.dssCircuit.Loads.kW)/S_Base,(Ckt.dssCircuit.Loads.kvar)/S_Base]
    LoadsCapacity[LoadName] = Power
    while 1:
        stop = Ckt.dssCircuit.Loads.Next
        if stop == 0:
            break
        LoadName = Ckt.dssCircuit.Loads.Name
        Power = [(Ckt.dssCircuit.Loads.kW)/S_Base, (Ckt.dssCircuit.Loads.kvar)/S_Base]
        LoadsCapacity[LoadName] = Power
    return LoadsCapacity

# ***************************************************************************************************
# *** Define a matrix for power flow equations
# ***************************************************************************************************
def Define_aMatrix(sqrt,np):
    a1 = complex(-0.5 , -sqrt(3)/2)
    a2 = complex(-0.5 , sqrt(3)/2)
    a = np.array([[1, a1, a2],[a2, 1, a1], [a1, a2, 1]])
    return a

# ***************************************************************************************************
# *** Define load type matrix
# ***************************************************************************************************
def DefineLoadType(AllLoads, DispatchableLoads):
    LoadType = {}
    for i in AllLoads:
        LoadType[i] = 0

    if len(DispatchableLoads):
        for j in DispatchableLoads:
            LoadType[j] = 1

    return LoadType

# ***************************************************************************************************
# *** Define MT matrix (Not using now!!)
# ***************************************************************************************************
def DefineMTConnection(AllBuses, S_Base, **kwargs):
    MTBus = {}
    for i in AllBuses:
        MTBus[i] = [0, 0]

    if len(kwargs):
        for i, j in kwargs.items():
            i = i[3::]
            P = j[0]/S_Base
            Q = j[1]/S_Base
            BS = j[2]
            MTBus[i] = [P , Q, BS]

    return MTBus
# ***************************************************************************************************
# *** Define MT to Bus matrix
# ***************************************************************************************************
def FindMTconnection(S_Base, **kwargs):
    MTBus = {}

    if len(kwargs):
        for i, j in kwargs.items():
            i = i[3::]
            MTname = 'MTBus{}'.format(i)
            P = j[0] / S_Base
            Q = j[1] / S_Base
            Ramp = j[2] / S_Base
            BS = j[3] if j[3] in j else 1
            MTBus[MTname] = [i, [P, Q], Ramp, BS]

    return MTBus
# ***************************************************************************************************
# *** Find which Bus has MT connection
# ***************************************************************************************************
def FindMTtoBus(AllBuses, MTconnection):
    MTtoBus = {}
    for i in AllBuses:
        MTtoBus[i] = []
    for i, j in MTconnection.items():
        MTtoBus[j[0]].append(i)

    return MTtoBus

# ***************************************************************************************************
# *** Define PV matrix (Not using now!!)
# ***************************************************************************************************
def DefinePVConnection(AllBuses, S_Base, **kwargs):
    PVBus = {}
    for i in AllBuses:
        PVBus[i] = [0, 0]

    if len(kwargs):
        for i, j in kwargs.items():
            i=i[3::]
            P = j[0]/S_Base
            BS = j[1]
            PVBus[i] = [P, BS]

    return PVBus

# ***************************************************************************************************
# *** Define PV to Bus matrix
# ***************************************************************************************************
def FindPVConnection(Ckt123, S_Base, **kwargs):
    PVBus = {}

    if len(kwargs):
        for i, j in kwargs.items():
            i = i[3::]
            PVname = 'PVBus{}'.format(i)
            P = j[0] / S_Base
            BS = j[1] if j[1] in j else 1
            PVBus[PVname] = [i, P, BS]

    # Find PV Systems in OpenDSS circuit
    stop = Ckt123.dssCircuit.PVSystems.First
    while stop:
        Name = Ckt123.dssCircuit.PVSystems.Name
        Ckt123.dssCircuit.SetActiveElement(Name)
        Bus = Ckt123.dssCircuit.ActiveCktElement.BusNames[0]
        S = Ckt123.dssCircuit.PVSystems.kVArated/S_Base
        PVBus[Name] = [Bus, S, 1]
        stop = Ckt123.dssCircuit.PVSystems.Next
    return PVBus


# ***************************************************************************************************
# *** Find which Bus has PV connection
# ***************************************************************************************************
def FindPVtoBus(AllBuses, PVconnection):
    PVtoBus = {}
    for i in AllBuses:
        PVtoBus[i] = []
    for i, j in PVconnection.items():
        PVtoBus[j[0]].append(i)

    return PVtoBus

# ***************************************************************************************************
# *** Define switchable PD Elements and lines
# ***************************************************************************************************
def FindSwitchableLines(AllPDElements, *args):
    SwitchableLines = {}
    for i in AllPDElements:
        Name = i.split('.')[1]
        Name = Name[0:2].lower()
        if Name == 'sw':
            SwitchableLines[i] = 1
        else:
            SwitchableLines[i] = 0
    if len(args):
        for i in args:
            SwitchableLines[i] = 1

    return SwitchableLines

# ***************************************************************************************************
# *** This function is used to list all switches
# ***************************************************************************************************
def FindSwitches(SwitchableLines):
    Switches = []
    for i, j in SwitchableLines.items():
        if j == 1:
            Switches.append(i)

    return Switches
# ***************************************************************************************************
# *** Find all lines length
# ***************************************************************************************************
def FindLinesLength(Ckt):
    LinesLength = {}
    stop = Ckt.dssCircuit.Lines.First
    while stop:
        Length = Ckt.dssCircuit.Lines.Length
        Name = Ckt.dssCircuit.Lines.Name
        LinesLength[Name] = Length
        stop = Ckt.dssCircuit.Lines.Next

    return LinesLength

# ***************************************************************************************************
# *** Integrate All PD Elements into lines length
# ***************************************************************************************************
def FindPDElementLength(AllPDElements, LinesLength):
    PDElementsLength = {}
    for i in AllPDElements:
        Name = i.split('.')[1]
        if Name in LinesLength:
            PDElementsLength[i] = LinesLength[Name]
        else:
            PDElementsLength[i] = 10 #ft

    return PDElementsLength

# ***************************************************************************************************
# *** Find all lines square capacity
# ***************************************************************************************************
def FindLinesSquareCapacity(Ckt, I_Base):
    LinesSquareCapacity = {}
    stop = Ckt.dssCircuit.Lines.First
    while stop:
        Name = Ckt.dssCircuit.Lines.Name
        Capacity = Ckt.dssCircuit.Lines.NormAmps
        Capacity_pu = Capacity/I_Base
        SquareCapacity = Capacity_pu * Capacity_pu
        LinesSquareCapacity[Name]= SquareCapacity
        stop = Ckt.dssCircuit.Lines.Next

    return LinesSquareCapacity

# ***************************************************************************************************
# *** Integrate all PD Elements into Lines square capacity
# ***************************************************************************************************
def FindPDElementsSquareCapacity(AllPDElements, LinesSquareCapacity):
    PDElementsSquareCapacity = {}
    for i in AllPDElements:
        Name = i.split('.')[1]
        if Name in LinesSquareCapacity:
            PDElementsSquareCapacity[i] = LinesSquareCapacity[Name]
        else:
            PDElementsSquareCapacity[i] = 1  # pu

    return PDElementsSquareCapacity

# ***************************************************************************************************
# *** Find Capacitor banks connection
# ***************************************************************************************************
def FindCapacitorConnection(Ckt):
    CapacitorConnection = {}

    Ckt.dssCircuit.Capacitors.First
    Name = Ckt.dssCircuit.Capacitors.Name
    NumPhases = Ckt.dssCircuit.ActiveElement.NumPhases
    TotalCapacity = Ckt.dssCircuit.Capacitors.kvar
    EachPhaseCapacity = TotalCapacity/NumPhases

    Ckt.dssCircuit.SetActiveElement(Name)
    BusOrder = Ckt.dssCircuit.ActiveElement.BusNames[0].split('.')
    BusName = BusOrder[0]
    CapacitorConnection[Name] = [BusName, [0, 0, 0]]
    if NumPhases == 3:
        CapacitorConnection[Name][1] = [EachPhaseCapacity, EachPhaseCapacity, EachPhaseCapacity]
    else:
        for j in range(NumPhases):
            Phase = int(BusOrder[j + 1]) - 1
            CapacitorConnection[Name][1][Phase] = EachPhaseCapacity

    NumCapacitors = Ckt.dssCircuit.Capacitors.Count
    for i in range(NumCapacitors-1):
        Ckt.dssCircuit.Capacitors.Next
        Name = Ckt.dssCircuit.Capacitors.Name
        NumPhases = Ckt.dssCircuit.ActiveElement.NumPhases
        TotalCapacity = Ckt.dssCircuit.Capacitors.kvar
        EachPhaseCapacity = TotalCapacity / NumPhases

        Ckt.dssCircuit.SetActiveElement(Name)
        BusOrder = Ckt.dssCircuit.ActiveElement.BusNames[0].split('.')
        BusName = BusOrder[0]
        CapacitorConnection[Name] = [BusName, [0, 0, 0]]
        if NumPhases == 3:
            CapacitorConnection[Name][1] = [EachPhaseCapacity, EachPhaseCapacity, EachPhaseCapacity]
        else:
            for j in range(NumPhases):
                Phase = int(BusOrder[j + 1])-1
                CapacitorConnection[Name][1][Phase] = EachPhaseCapacity

    return CapacitorConnection

# ***************************************************************************************************
# *** Find which Bus has capacitor bank
# ***************************************************************************************************
def FindCapacitorToBus(AllBuses, CapacitorConnection):
    CapacitortoBus = {}
    for i in AllBuses:
        CapacitortoBus[i] = []
    for i, j in CapacitorConnection.items():
        CapacitortoBus[j[0]].append(i)

    return CapacitortoBus

# ***************************************************************************************************
# *** Find the PD element which is connected to the source bus
# ***************************************************************************************************
def FindFirstPDElement(PDElementsConnections, SourceBus):
    PDElement = None
    for i, j in PDElementsConnections.items():
        if SourceBus[0].lower() == j[0].lower():
            PDElement = i

    return PDElement

# ***************************************************************************************************
# *** Set restoration times
# ***************************************************************************************************
def SetRestorationTimes(numbers):
    Time = []
    for i in range(numbers):
        Time.append('t{}'.format(i+1))
    return Time

# ***************************************************************************************************
# *** Find Source bus Connections
# ***************************************************************************************************
def FindSourceconnection(PDElementsConnection, SourceBus):
    Source = {}
    if SourceBus != []:
        for i in SourceBus:
            Source[i] = 0

    for k in SourceBus:
        for i, j in PDElementsConnection.items():
            if (j[0] == k) or (j[1] == k):
                Source[k] = i

    return Source

# ***************************************************************************************************
# *** Convert elements of a vector to base values
# ***************************************************************************************************
def Convert_pu(x, base):
    output = []
    for i in x:
        output.append(i/base)

    return output

# ***************************************************************************************************
# *** Convert elements of a vector to base values
# ***************************************************************************************************
def ArrangeSourceCapacity(SourceBus, S_Base, SourceCapacity):
    output = {}
    for i in SourceBus:
        output[i] = SourceCapacity[SourceBus.index(i)]/S_Base

    return output

# ***************************************************************************************************
# *** Find Resistance of distribution lines
# ***************************************************************************************************
def FindLinesResistance(Ckt, AllLines):
    LinesResistance={}
    for i in AllLines:
        Ckt.dssCircuit.SetActiveElement('Line.{}'.format(i))
        R = list(Ckt.dssCircuit.Lines.Rmatrix)
        LinesResistance[i] = R

    return LinesResistance

# ***************************************************************************************************
# *** Find Reactance of distribution lines
# ***************************************************************************************************
def FindLinesReactance(Ckt, AllLines):
    LinesReactance={}
    for i in AllLines:
        Ckt.dssCircuit.SetActiveElement('Line.{}'.format(i))
        X = list(Ckt.dssCircuit.Lines.Xmatrix)
        LinesReactance[i] = X

    return LinesReactance


# ***************************************************************************************************
# *** Find Resistance of All PD Elements
# ***************************************************************************************************
def FindPDElementsR(AllPDElements, PDElementPhaseMatrix, LinesResistance, PDElementLength, Z_Base):
    PDElementResistance={}
    for i in AllPDElements:
        Type = i.split('.')[0]
        Name = i.split('.')[1]
        if Type == 'Line':
            Rmatrix = LinesResistance[Name]
            # Multiply by length and Convert to p.u.------------
            if Name[0:1] == 'sw':
                for j in Rmatrix:
                  Rmatrix[Rmatrix.index(j)] = j / Z_Base
            else:
                for j in Rmatrix:
                  Rmatrix[Rmatrix.index(j)] = j * PDElementLength[i] / Z_Base
            # --------------------------------------------------
            FinalRmatrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            Connection = PDElementPhaseMatrix[i]

            if len(Rmatrix) == 9: # Three Phase-------------------------------------------
                FinalRmatrix[0][:] = Rmatrix[0:3]
                FinalRmatrix[1][:] = Rmatrix[3:6]
                FinalRmatrix[2][:] = Rmatrix[6:9]
                PDElementResistance[i] = FinalRmatrix

            elif len(Rmatrix) == 4: # Two Phase-------------------------------------------
                if (Connection[0] == 1) and (Connection[1] == 1):
                    FinalRmatrix[0][0] = Rmatrix[0]
                    FinalRmatrix[0][1] = Rmatrix[1]
                    FinalRmatrix[1][0] = Rmatrix[2]
                    FinalRmatrix[1][1] = Rmatrix[3]

                elif (Connection[0] == 1) and (Connection[2] == 1):
                    FinalRmatrix[0][0] = Rmatrix[0]
                    FinalRmatrix[0][2] = Rmatrix[1]
                    FinalRmatrix[2][0] = Rmatrix[2]
                    FinalRmatrix[2][2] = Rmatrix[3]

                elif (Connection[1] == 1) and (Connection[2] == 1):
                    FinalRmatrix[1][1] = Rmatrix[0]
                    FinalRmatrix[1][2] = Rmatrix[1]
                    FinalRmatrix[2][1] = Rmatrix[2]
                    FinalRmatrix[2][2] = Rmatrix[3]

                PDElementResistance[i] = FinalRmatrix

            elif len(Rmatrix) == 1: # One Phase-------------------------------------------
                if Connection[0] == 1:
                    FinalRmatrix[0][0] = Rmatrix[0]

                elif Connection[1] == 1:
                    FinalRmatrix[1][1] = Rmatrix[0]

                elif Connection[2] == 1:
                    FinalRmatrix[2][2] = Rmatrix[0]

                PDElementResistance[i] = FinalRmatrix

        elif Type == 'Transformer':
            FinalRmatrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            Connection = PDElementPhaseMatrix[i]

            if Connection[0] == 1: # phase a
                FinalRmatrix[0][0] = 0.01 / Z_Base

            if Connection[1] == 1:  # phase b
                FinalRmatrix[1][1] = 0.01 / Z_Base

            if Connection[2] == 1:  # phase c
                FinalRmatrix[2][2] = 0.01 / Z_Base

            PDElementResistance[i] = FinalRmatrix

        elif Type == 'Reactor':
            FinalRmatrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            Connection = PDElementPhaseMatrix[i]

            if Connection[0] == 1: # phase a
                FinalRmatrix[0][0] = 0.001 / Z_Base

            if Connection[1] == 1:  # phase b
                FinalRmatrix[1][1] = 0.001 / Z_Base

            if Connection[2] == 1:  # phase c
                FinalRmatrix[2][2] = 0.001 / Z_Base

            PDElementResistance[i] = FinalRmatrix

    return PDElementResistance

# ***************************************************************************************************
# *** Find Reactance of All PD Elements
# ***************************************************************************************************
def FindPDElementsX(AllPDElements, PDElementPhaseMatrix, LinesReactance, PDElementsLength, Z_Base):
    PDElementReactance = {}
    for i in AllPDElements:
        Type = i.split('.')[0]
        Name = i.split('.')[1]
        if Type == 'Line':
            Xmatrix = LinesReactance[Name]
            # Multiply by length and Convert to p.u.------------
            for j in Xmatrix:
                Xmatrix[Xmatrix.index(j)] = j * PDElementsLength[i] / Z_Base
            # --------------------------------------------------
            FinalXmatrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            Connection = PDElementPhaseMatrix[i]

            if len(Xmatrix) == 9:  # Three Phase-------------------------------------------
                FinalXmatrix[0][:] = Xmatrix[0:3]
                FinalXmatrix[1][:] = Xmatrix[3:6]
                FinalXmatrix[2][:] = Xmatrix[6:9]
                PDElementReactance[i] = FinalXmatrix

            elif len(Xmatrix) == 4:  # Two Phase-------------------------------------------
                if (Connection[0] == 1) and (Connection[1] == 1):
                    FinalXmatrix[0][0] = Xmatrix[0]
                    FinalXmatrix[0][1] = Xmatrix[1]
                    FinalXmatrix[1][0] = Xmatrix[2]
                    FinalXmatrix[1][1] = Xmatrix[3]

                elif (Connection[0] == 1) and (Connection[2] == 1):
                    FinalXmatrix[0][0] = Xmatrix[0]
                    FinalXmatrix[0][2] = Xmatrix[1]
                    FinalXmatrix[2][0] = Xmatrix[2]
                    FinalXmatrix[2][2] = Xmatrix[3]

                elif (Connection[1] == 1) and (Connection[2] == 1):
                    FinalXmatrix[1][1] = Xmatrix[0]
                    FinalXmatrix[1][2] = Xmatrix[1]
                    FinalXmatrix[2][1] = Xmatrix[2]
                    FinalXmatrix[2][2] = Xmatrix[3]

                PDElementReactance[i] = FinalXmatrix

            elif len(Xmatrix) == 1:  # One Phase-------------------------------------------
                if Connection[0] == 1:
                    FinalXmatrix[0][0] = Xmatrix[0]

                elif Connection[1] == 1:
                    FinalXmatrix[1][1] = Xmatrix[0]

                elif Connection[2] == 1:
                    FinalXmatrix[2][2] = Xmatrix[0]

                PDElementReactance[i] = FinalXmatrix

        elif Type == 'Transformer':
            FinalXmatrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            Connection = PDElementPhaseMatrix[i]

            if Connection[0] == 1:  # phase a
                FinalXmatrix[0][0] = 0.01 / Z_Base

            if Connection[1] == 1:  # phase b
                FinalXmatrix[1][1] = 0.01 / Z_Base

            if Connection[2] == 1:  # phase c
                FinalXmatrix[2][2] = 0.01 / Z_Base

            PDElementReactance[i] = FinalXmatrix

        elif Type == 'Reactor':
            FinalXmatrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            Connection = PDElementPhaseMatrix[i]

            if Connection[0] == 1:  # phase a
                FinalXmatrix[0][0] = 0.01 / Z_Base

            if Connection[1] == 1:  # phase b
                FinalXmatrix[1][1] = 0.01 / Z_Base

            if Connection[2] == 1:  # phase c
                FinalXmatrix[2][2] = 0.01 / Z_Base

            PDElementReactance[i] = FinalXmatrix

    return PDElementReactance

# ***************************************************************************************************
# *** Calculate R_hat PD Elements
# ***************************************************************************************************
def CalculatePDElements_R_hat(PDElementsR, PDElementsX, sqrt, np):
    PDElementsR_hat = {}
    # alpah matrix------------------------------------------------
    a1 = complex(-0.5, -sqrt(3)/2)
    a2 = complex(-0.5, sqrt(3)/2)
    a = np.array([[1, a1, a2], [a2, 1, a1], [a1, a2, 1]])
    # ------------------------------------------------------------
    for i, j in PDElementsR.items():
        Matrix1 = a * np.array(j)
        Matrix2 = a * np.array(PDElementsX[i])
        R_hat = Matrix1.real - Matrix2.imag
        PDElementsR_hat[i] = R_hat.tolist()

    return PDElementsR_hat

# ***************************************************************************************************
# *** Calculate X_hat PD Elements
# ***************************************************************************************************
def CalculatePDElements_X_hat(PDElementsX, PDElementsR, sqrt, np):
    PDElementsX_hat = {}
    # alpah matrix------------------------------------------------
    a1 = complex(-0.5, -sqrt(3)/2)
    a2 = complex(-0.5, sqrt(3)/2)
    a = np.array([[1, a1, a2], [a2, 1, a1], [a1, a2, 1]])
    # ------------------------------------------------------------
    for i, j in PDElementsX.items():
        Matrix1 = a * np.array(j)
        Matrix2 = a * np.array(PDElementsR[i])
        X_hat = Matrix1.real + Matrix2.imag
        PDElementsX_hat[i] = X_hat.tolist()

    return PDElementsX_hat

# ***************************************************************************************************
# *** This function is used to calculate Z_hat
# ***************************************************************************************************
def CalculatePDElements_Z_hat(PDElementsR, PDElementsX, sqrt):
    PDElementsZ_hat = {}
    for i in PDElementsR:
        PDElementsZ_hat[i] = [[0, 0, 0],[0, 0, 0],[0, 0, 0]]

    for i, j in PDElementsR.items():
        for k in range(3):
            for m in range(3):
                PDElementsZ_hat[i][k][m] = sqrt(j[k][m]*j[k][m] + (PDElementsX[i][k][m])*(PDElementsX[i][k][m]))

    return PDElementsZ_hat

# ***************************************************************************************************
# *** This function is used in Active power balance euqation
# ***************************************************************************************************
def ActivePowerBalance(PDElement, Phase, P_Load, P_Line, P_PV, P_sub, PDElementsConnections,
                       PDElementPhaseMatrix, LoadToBus, LoadsConnection, ChildrenLines, PVBus, SourceBus, Source):
    PowerBalance = 0
    BusName = PDElementsConnections[PDElement][1]
    #Phase index
    if Phase == 'a':
        PhaseIndex = 0
    elif Phase == 'b':
        PhaseIndex = 1
    elif Phase == 'c':
        PhaseIndex = 2
    # Loads-----------------------------------------------------------------
    if BusName in LoadToBus:
        for i in LoadToBus[BusName]:
            if LoadsConnection[i][2][PhaseIndex] == 1:
                PowerBalance = PowerBalance + (P_Load[i])/LoadsConnection[i][1]
    # Lines-----------------------------------------------------------------
    if ChildrenLines[PDElement] is not []:
        for i in ChildrenLines[PDElement]:
            if PDElementPhaseMatrix[i][PhaseIndex] == 1:
                if PDElementsConnections[i][0] == BusName:
                    PowerBalance = PowerBalance + P_Line[Phase, i]

                else:
                    PowerBalance = PowerBalance - P_Line[Phase, i]

    # Substations--------------------------------------------------------------
    if BusName in SourceBus:
        PowerBalance = PowerBalance - P_sub[Phase, BusName]

    if PDElement == Source[SourceBus[0]]:
        PowerBalance = PowerBalance - P_sub[Phase, SourceBus[0]]

    # Loss-----------------------------------------------------------------
    # Loss is ignored for simplification of problem formulation
    # Generation-----------------------------------------------------------
    # PV---------
    if PVBus[BusName] is not []:
        for i in PVBus[BusName]:
            PowerBalance = PowerBalance - P_PV[Phase, i]

    return PowerBalance

# ***************************************************************************************************
# *** This function is used in Reactive power balance euqation
# ***************************************************************************************************
def ReactivePowerBalance(PDElement, Phase, Q_Load, Q_Line, Q_PV,  Q_sub, PDElementsConnections,
                         PDElementPhaseMatrix, LoadToBus, LoadsConnection, ChildrenLines, PVBus, SourceBus, Source ):
    PowerBalance = 0
    BusName = PDElementsConnections[PDElement][1]
    # Phase index
    if Phase == 'a':
        PhaseIndex = 0
    elif Phase == 'b':
        PhaseIndex = 1
    elif Phase == 'c':
        PhaseIndex = 2
    # Loads-----------------------------------------------------------------
    if BusName in LoadToBus:
        for i in LoadToBus[BusName]:
            if LoadsConnection[i][2][PhaseIndex] == 1:
                PowerBalance = PowerBalance + Q_Load[i]

    # Lines-----------------------------------------------------------------
    if ChildrenLines[PDElement] is not []:
        for i in ChildrenLines[PDElement]:
            if PDElementPhaseMatrix[i][PhaseIndex] == 1:
                if PDElementsConnections[i][0] == BusName:
                    PowerBalance = PowerBalance + Q_Line[Phase, i]

                else:
                    PowerBalance = PowerBalance - Q_Line[Phase, i]

    # Substations--------------------------------------------------------------
    if BusName in SourceBus:
        PowerBalance = PowerBalance - Q_sub[Phase, BusName]

    if PDElement == Source[SourceBus[0]]:
        PowerBalance = PowerBalance - Q_sub[Phase, SourceBus[0]]

    # Loss-----------------------------------------------------------------
    # Loss is ignored for simplification of problem formulation
    # Generation-----------------------------------------------------------
    # PV---------
    if PVBus[BusName] is not []:
        for i in PVBus[BusName]:
            PowerBalance = PowerBalance - Q_PV[Phase, i]

    # Capacitor Bank-----------------------------------------------------------
    # Capacitor bank is ignored for simplification of problem formulation

    return PowerBalance

# *****************************************************************************************
# * This function is used to find the right hand side of the voltage drop equation
# *****************************************************************************************
def VoltageRHS(Phase, PDElement, ParentBus, U_Bus, P_Line, Q_Line, PDElementsR_hat, PDElementsX_hat):
    # Phase index
    if Phase == 'a':
        PhaseIndex = 0
    elif Phase == 'b':
        PhaseIndex = 1
    elif Phase == 'c':
        PhaseIndex = 2

    VoltageDrop = 0

    # Parent Bus Voltage
    VoltageDrop = VoltageDrop + U_Bus[Phase, ParentBus]

    # r_hat*P_line section
    Temp1 = 0
    for i in range(3):
        Temp1 = Temp1 + PDElementsR_hat[PDElement][PhaseIndex][i]*P_Line[Phase, PDElement]

    # x_hat*Q_line section
    Temp2 = 0
    for i in range(3):
        Temp2 = Temp2 + PDElementsX_hat[PDElement][PhaseIndex][i] * Q_Line[Phase, PDElement]

    # Integrate both r_hat*P_line and x_hat*Q_line in original equation
    VoltageDrop = VoltageDrop - 2*(Temp1 + Temp2)

    # z_hat*l_Line section
    # remove this term because do not have access to line current for simplification

    return VoltageDrop

# *********************************************************************************
# * Calculate total loss of the distribution network
# *********************************************************************************
def CalculateTotalLoss(RestorationTime, AllPDElements, PhaseSequence, l_Line, PDElementsR):
    Loss = 0
    for t in RestorationTime:
        for j in AllPDElements:
            for i in PhaseSequence:
                # Phase index
                if i == 'a':
                    PhaseIndex = 0
                elif i == 'b':
                    PhaseIndex = 1
                elif i == 'c':
                    PhaseIndex = 2

                for k in range(3):
                    Loss = Loss + PDElementsR[j][PhaseIndex][k] * l_Line[PhaseSequence[k], j, t]

    return Loss

# *******************************************************************************************************
# * This function adjusts source capacity based on provided power by the source
# *******************************************************************************************************
def CalculateUsource(Sourcebus, SourceCapacity, RestorationTime, voltage):
    Usource = {}
    for i in Sourcebus:
        Usource[i]={}
        for t in RestorationTime:
            if SourceCapacity[i] == 0:
                Usource[i][t] = 0

            else:
                Usource[i][t] = voltage

    return Usource

# *******************************************************************************************************
# * This function finds PD Element connected to each sourcebus
# *******************************************************************************************************
def FindSourcebusConnection(Source, SourceBus, PDElementsConnections, ParentBus):

    # A function to find key from value in dictionary
    key_list = list(PDElementsConnections.keys())
    val_list = list(PDElementsConnections.values())

    for i in SourceBus:
        if SourceBus.index(i) != 0:
            Parent = ParentBus[i]
            if (Parent, i) in val_list:
                PDElement = key_list[val_list.index((Parent, i))]
                Source[i] = PDElement

    return Source

# *********************************************************************************
# * Find X-Y coordinates of buses
# *********************************************************************************
def FindXY_Coordinates(ckt):
    Coordinates = {}
    Temp_buses = ckt.AllBuses()

    for i in Temp_buses:
        x = ckt.dssCircuit.Buses(i).x
        y = ckt.dssCircuit.Buses(i).y
        Coordinates[i]=[x, y]

    return Coordinates

# *******************************************************************************************************
# * This function finds neighbor lines for spanning tree constraint of restricting to have one parent
# *******************************************************************************************************
def FindParentFlow(Bus, Beta, PDElementsConnections, BusNeighborBuses):

    FlowDirection = 0

    # A function to find key from value in dictionary
    key_list = list(PDElementsConnections.keys())
    val_list = list(PDElementsConnections.values())

    for i in BusNeighborBuses[Bus]:
        if (Bus, i) in val_list:
            Line = key_list[val_list.index((Bus, i))]
            FlowDirection = FlowDirection + Beta[Line, 'd2']

        elif (i, Bus) in val_list:
            Line = key_list[val_list.index((i, Bus))]
            FlowDirection = FlowDirection + Beta[Line, 'd1']

    return FlowDirection

# *******************************************************************************************************
# * This function defines higher weight for normally close switches to have them close if possible
# *******************************************************************************************************
def DefineSwitchWeight(SwitchableLines, NormallyCloseSwitches, W):
    Weight = {}
    for i in SwitchableLines:
        if SwitchableLines[i] == 1:
            if i in NormallyCloseSwitches:
                Weight[i] = W

            else:
                Weight[i] = 1

    return Weight

# *******************************************************************************************************
# * This function defines higher weight for normally close switches to have them close if possible
# *******************************************************************************************************
def ModifySwitchesCoordinates(XY_Coordinates, SwitchableLines, PDElementsConnections, ParentBus, ChildrenBuses):

    for i, j in SwitchableLines.items():
        if j == 1:
            bus1 = PDElementsConnections[i][0]
            bus2 = PDElementsConnections[i][1]
            if (XY_Coordinates[bus1][0] == 0) or (XY_Coordinates[bus1][1] == 0):
                stop = 1
                Parent = (ParentBus[bus1]+'.')[:-1]
                while stop:
                    if (XY_Coordinates[Parent][0] != 0) and (XY_Coordinates[Parent][1] != 0):
                        XY_Coordinates[bus1][0] = XY_Coordinates[Parent][0]
                        XY_Coordinates[bus1][1] = XY_Coordinates[Parent][1]
                        stop = 0
                    Parent = (ParentBus[Parent]+'.')[:-1]

            if (XY_Coordinates[bus2][0] == 0) or (XY_Coordinates[bus2][1] == 0):
                stop = 1
                Child = (ChildrenBuses[bus2][0]+'.')[:-1]
                while stop:
                    if (XY_Coordinates[Child][0] != 0) and (XY_Coordinates[Child][1] != 0):
                        XY_Coordinates[bus2][0] = XY_Coordinates[Child][0]
                        XY_Coordinates[bus2][1] = XY_Coordinates[Child][1]
                        stop = 0
                    Child = (ChildrenBuses[Child][0]+'.')[:-1]

    return XY_Coordinates

# *******************************************************************************************************
# * This function is used to find the service transfomer which the load in secondary is connected
# *******************************************************************************************************
def FindLoad2Secondarytransformer(loadname, ckt, ParentBus, PDElementsConnections):
    # Find bus name and its parent for load
    ckt.dssCircuit.SetActiveElement('Load.{}'.format(loadname))
    bus = ckt.dssCircuit.ActiveCktElement.BusNames[0].split('.')
    BusName = bus[0]
    ParentName = ParentBus[BusName]

    # Find PD Element connected to the bus
    key_list = list(PDElementsConnections.keys())
    val_list = list(PDElementsConnections.values())
    val_index = val_list.index((ParentName, BusName))
    PDElement = key_list[val_index]

    # Find parent PD Elements until reaching service transfomer
    stop = 1
    Type = PDElement.split('.')[0]
    if Type.lower() == 'Transformer'.lower():
        stop = 0

    while stop:
        BusName = (ParentName + '.')[:-1]
        ParentName = (ParentBus[BusName] +'.')[:-1]
        val_index = val_list.index((ParentName, BusName))
        PDElement = key_list[val_index]

        Type = PDElement.split('.')[0]
        if Type.lower() == 'Transformer'.lower():
            stop = 0

    return PDElement
# *******************************************************************************************************
# * This function is used modify vectors for secondary loads
# *******************************************************************************************************
def ModifySecondaryLoad(CktNum, ckt, AllLoads, ParentBus, PDElementsConnections, LoadsConnection, Loads_max, LoadToBus):

    AllLoadsModi = list(AllLoads).copy()
    LoadsConnectionModi = LoadsConnection.copy()
    Loads_maxModi = Loads_max.copy()
    LoadToBusModi = LoadToBus.copy()

    if (CktNum == 2)|(CktNum == 3):
        for i in AllLoads:
            ckt.dssCircuit.SetActiveElement('Load.{}'.format(i))
            voltage = ckt.dssCircuit.ActiveCktElement.VoltagesMagAng[0]
            if voltage <= 600:
                Transfomer = FindLoad2Secondarytransformer(i, ckt, ParentBus, PDElementsConnections)
                Bus = PDElementsConnections[Transfomer][0]
                NewLoad = Transfomer.split('.')[1] + 'load'

                ckt.dssCircuit.SetActiveElement(Transfomer) # Set Transformer as active element
                Phases = [0, 0, 0]
                NumPhases = ckt.dssCircuit.ActiveCktElement.NumPhases
                BusConnection = ckt.dssCircuit.ActiveCktElement.BusNames[0].split('.')
                Phase = BusConnection[1]

                if NumPhases==1:
                    # Remove load from AllLoadsModi
                    AllLoadsModi.remove(i)
                    # Add new load to AllLoadsModi
                    if NewLoad not in AllLoadsModi:
                        AllLoadsModi.append(NewLoad)

                    # Remove load from LoadTobus
                    LoadToBusModi.pop(LoadsConnection[i][0], None)
                    # Add new load to LoadToBusModi
                    if Bus not in LoadToBusModi:
                        LoadToBusModi[Bus] = [NewLoad]
                    else:
                        LoadToBusModi[Bus].append(NewLoad)

                    # Remove load from LoadConnectionsModi
                    LoadsConnectionModi.pop(i, None)
                    # Add or update new load to LoadsConnectionModi
                    Phases[int(Phase)-1] = 1
                    P_Load = LoadsConnection[i][3]
                    Q_Load = LoadsConnection[i][4]
                    if NewLoad not in LoadsConnectionModi:
                        LoadsConnectionModi[NewLoad] = [Bus,NumPhases, Phases, P_Load, Q_Load]
                    else:
                        LoadsConnectionModi[NewLoad][3] = LoadsConnectionModi[NewLoad][3] + P_Load
                        LoadsConnectionModi[NewLoad][4] = LoadsConnectionModi[NewLoad][4] + Q_Load

                    # Remove load from Loads_maxModi
                    Loads_maxModi.pop(i, None)
                    # Add or update new load to Loads_maxModi
                    if NewLoad not in Loads_maxModi:
                        Loads_maxModi[NewLoad] = [P_Load, Q_Load]
                    else:
                        Loads_maxModi[NewLoad][0] = Loads_maxModi[NewLoad][0] + P_Load
                        Loads_maxModi[NewLoad][1] = Loads_maxModi[NewLoad][1] + Q_Load

    return [AllLoadsModi, LoadToBusModi, LoadsConnectionModi, Loads_maxModi]

# *********************************************************************************
# * Plot circuit connections based on the energization
# *********************************************************************************
def PlotCircuit(XY_Coordinates, AllBuses, AllPDElements, PDElementsConnections, DSR, plt, PVBus, SwitchableLines,
                AllLoads, LoadsConnection, PDElementPhaseMatrix, FaultedLines, SourceBus):

    # Draw Load pickup
    ResultLoads = {}
    for i in AllLoads:
        ResultLoads[i] = 0
    for v in DSR.getVars():
        if v.varName.split('[')[0] == 'x_Load':
            ResultLoads[v.varName.split('[')[1][:-1]] = v.x

    for j, k in ResultLoads.items():
        TempBus = LoadsConnection[j][0]
        if (XY_Coordinates[TempBus][0] != 0) and (XY_Coordinates[TempBus][1] != 0):
            if k == 0:
                #plt.scatter(XY_Coordinates[TempBus][0], XY_Coordinates[TempBus][1], c='r', marker='.', linewidths=0.0005)
                plt.scatter(XY_Coordinates[TempBus][0], XY_Coordinates[TempBus][1], c='r', s=0.05)#was 0.5
            elif k == 1:
                #plt.scatter(XY_Coordinates[TempBus][0], XY_Coordinates[TempBus][1], c='g', marker='.', linewidths=0.0005)
                plt.scatter(XY_Coordinates[TempBus][0], XY_Coordinates[TempBus][1], c='g', s=0.05)#was 0.5

    # Draw Buses
    for i in AllBuses:
        if (XY_Coordinates[i][0] != 0) and (XY_Coordinates[i][1] != 0):
            if PVBus[i] != []:
                plt.scatter(XY_Coordinates[i][0], XY_Coordinates[i][1], c='k', marker='D', linewidths=1)
                plt.text(XY_Coordinates[i][0] - 1000, XY_Coordinates[i][1] - 1300, 'PV', fontsize=5)
            if i in SourceBus:
                plt.scatter(XY_Coordinates[i][0], XY_Coordinates[i][1], c='k', marker='*', linewidths=2)
                plt.text(XY_Coordinates[i][0] - 1000, XY_Coordinates[i][1] - 1300, 'Sub.', fontsize=6)


    # Draw energized Lines----------------------------------------------------------
    ResultLines = {}
    for i in AllPDElements:
        ResultLines[i] = 1
    for v in DSR.getVars():
        if v.varName.split('[')[0] == 'x_Line':
            ResultLines[v.varName.split('[')[1][:-1]] = v.x

    # Faulted Lines
    for i in FaultedLines:
        ResultLines[i] = 0

    for j, k in ResultLines.items():
        Temp_Bus1 = PDElementsConnections[j][0]
        Temp_Bus2 = PDElementsConnections[j][1]
        if (XY_Coordinates[Temp_Bus1][0] != 0) and (XY_Coordinates[Temp_Bus1][1] != 0):
            if (XY_Coordinates[Temp_Bus2][0] != 0) and (XY_Coordinates[Temp_Bus2][1] != 0):
                TempX = [XY_Coordinates[Temp_Bus1][0], XY_Coordinates[Temp_Bus2][0]]
                TempY = [XY_Coordinates[Temp_Bus1][1], XY_Coordinates[Temp_Bus2][1]]
                NumPhases = sum(PDElementPhaseMatrix[j])
                if k == 0:
                    if SwitchableLines[j] == 1:
                        plt.plot(TempX, TempY, 'y-', marker=6, linewidth=1, markersize=1.5, markevery=100) # marker size was 2
                    else:
                        if NumPhases == 3:
                            plt.plot(TempX, TempY, 'r-', linewidth=0.8)
                        elif NumPhases == 2:
                            #plt.plot(TempX, TempY, 'r--', linewidth=0.8)
                            plt.plot(TempX, TempY, 'r', linewidth=0.8)
                        else:
                            #plt.plot(TempX, TempY, 'r:', linewidth=0.8)
                            plt.plot(TempX, TempY, 'r-', linewidth=0.8)
                        plt.scatter(XY_Coordinates[Temp_Bus1][0], XY_Coordinates[Temp_Bus1][1], c='k', marker='x', linewidths=2)
                        plt.text(XY_Coordinates[Temp_Bus1][0]-500, XY_Coordinates[Temp_Bus1][1] - 1100, 'Fault', fontsize=5)

                else:
                    if SwitchableLines[j] == 1:
                        plt.plot(TempX, TempY, 'b-', marker=7, linewidth=1, markersize=2, markevery=100)#marker size was 3


                    else:
                        if NumPhases == 3:
                            plt.plot(TempX, TempY, 'k-', linewidth=0.7)
                        elif NumPhases == 2:
                            plt.plot(TempX, TempY, 'k--', linewidth=0.4)
                        else:
                            plt.plot(TempX, TempY, 'k--', linewidth=0.4)

    plt.xlabel('X')
    plt.ylabel('Y')

    plt.savefig('IEEE_Network.pdf')
    plt.savefig('IEEE_Network.png')
    plt.show()



