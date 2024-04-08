import os, json
from dss import DSS as dssObj

try:
    import RSO_pack
except ImportError:
    from . import RSO_pack 

thisDir = os.path.abspath(os.path.dirname(__file__))

# helper functions: modified from ProtectionSettingsOptimizer OpenDSS example 

def runDSS( file ):
    ''' compiles and solves the given opendss file '''
    dssText = dssObj.Text
    dssCircuit = dssObj.ActiveCircuit
    dssText.Command = 'clear'
    dssText.Command = 'compile '+ file
    dssText.Command = 'set maxcontroliter = 500'
    dssText.Command = 'solve'
    return dssText, dssCircuit

def parseSysInfo(SysInfo):
    ''' returns the Lines, Names, and Buses of the Relays and Reclosers in the circuit '''
    Buses = SysInfo['Buses']
    devLines = [x['MonitoredObj'].split('Line.')[1] for x in SysInfo['Relays']]
    devLines += [x['MonitoredObj'].split('Line.')[1] for x in SysInfo['Recs']]
    devNames = [x['Name'] for x in SysInfo['Relays']]
    devNames += [x['Name'] for x in SysInfo['Recs']]
    dev_BusV = [Buses[RSO_pack.index_dict(Buses,'Name',x['Bus1'])]['kV']*1e3 for x in SysInfo['Relays'] ]
    dev_BusV += [Buses[RSO_pack.index_dict(Buses,'Name',x['Bus1'])]['kV']*1e3 for x in SysInfo['Recs'] ]
    return Buses, devLines, devNames, dev_BusV

def parseFaultInfo(Buses):
    ''' returns the Names and Nodes of the Buses in the circuit '''
    faultBuses = [x['Name'] for x in Buses]
    faultBusPhases = [None]*len(faultBuses)
    for ii in range(len(faultBuses)):
        faultBusPhases[ii] = Buses[RSO_pack.index_dict(Buses,'Name',faultBuses[ii])]['nodes']
    return faultBuses, faultBusPhases

def loadFaultCSV(FData, testPath):
    ''' copies the Fault data in FData to <testPath>/FData.csv'''
    Fault_File_loc = os.path.normpath(os.path.join(testPath,'FData.csv'))
    FData.to_csv(Fault_File_loc,index=False,header=False)
    Fault_Data_CSV = RSO_pack.read_Fault_CSV_Data(Fault_File_loc)
    return Fault_Data_CSV

def parseSwitchInfo(SysInfo):
    ''' returns the Lines and States of the switches in the circuit '''
    #lines where switch = True 
    switchLines = [x['Name'] for x in SysInfo['Lines'] if x['isSwitch']]
    #lines that are enabled
    switchStates = [1 if x['Enabled'] else 0 for x in SysInfo['Lines'] if x['isSwitch']]
    return switchLines, switchStates

def writeSettingsAndInfo(testPath, settings, old_info):
    ''' copies the settings and previous info to <testPath>/settings_rso_out.json and <testPath>old_info_rso_out.json '''
    settingsFile = os.path.normpath(os.path.join(testPath, 'settings_rso_out.json'))
    with open(settingsFile, "w") as f:
        j = json.dumps(settings, default=str)
        f.write(j)
    infoFile = os.path.normpath(os.path.join(testPath, 'old_info_rso_out.json'))
    with open(infoFile, "w") as f:
        j = json.dumps(old_info, default=str)
        f.write(j)

def run(testPath, testFile):
    ''' runs setting optimization on the given opendss file, given constant program setting inputs '''
    #fault resistances to test
    Fres = ['0.001','1']
    #supported fault types
    Fts = ['3ph','SLG','LL']

    # program settings
    Force_NOIBR = 1
    #DOC = 0
    enableIT = 0
    CTI = 0.25
    OTmax = 10
    Sho_Plots=1
    type_select = False
    Fault_Res = ['R0_001','R1']
    Min_Ip = [0.1,0.1]
    Substation_bus = 'sourcebus'
    initpop = None
    SetDir=False

    dssText, dssCircuit = runDSS(os.path.normpath(os.path.join(testPath, testFile)))
    # collect system info from OpenDSS
    SysInfo = RSO_pack.getSysInfo(dssCircuit)

    Buses, devLines, devNames, dev_BusV = parseSysInfo(SysInfo)
    Device_Data_CSV = RSO_pack.getDeviceData(dssCircuit,devNames,devLines,dev_BusV)

    # collect fault data 
    faultBuses, faultBusPhases = parseFaultInfo(Buses)

    FData = RSO_pack.getFaultInfo(dssCircuit,dssText,faultBuses,faultBusPhases,Fres,Fts,devLines,devNames,dev_BusV)
    Fault_Data_CSV = loadFaultCSV(FData, testPath)

    switchLines, switchStates = parseSwitchInfo(SysInfo)
    settings,old_info = RSO_pack.runSettingsOptimizer(testPath,
                                                 switchStates,
                                                 switchLines,
                                                 Device_Data_CSV,
                                                 Fault_Data_CSV,
                                                 Fault_Res,
                                                 SysInfo,
                                                 Substation_bus,
                                                 Min_Ip,
                                                 enableIT,
                                                 Force_NOIBR,
                                                 CTI,
                                                 OTmax,
                                                 type_select,
                                                 SetDir,
                                                 Sho_Plots,
                                                 GA_initial_seed=initpop)
    
    writeSettingsAndInfo(testPath, settings, old_info)

def _test():
    testPath = os.path.normpath(os.path.join(thisDir, 'testFiles'))
    testFile = 'IEEE34Test.dss'
    run(testPath, testFile)

if __name__ == "__main__":
    _test()