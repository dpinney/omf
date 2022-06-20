import json

def buildCustomerInfo(inFile = '/Users/george/omf/omf/Cobb.clean.dss.omd', modelOut = '/Users/george/Downloads/output.Master3.no-networking2.json', outFile = '/Users/george/Desktop/no-netcustomerInfo2.csv', season = 'summer', timestep = .25, maxDuration = 8):
    with open(inFile) as inF:
        tree = json.load(inF)['tree']
    with open(modelOut) as mo:
        deviceTimeline = json.load(mo)["Device action timeline"]
    loadsShed = []
    for line in deviceTimeline:
        loadsShed.append(line["Shedded loads"])
    custInfo = ['Customer Name,Duration,Season,Average kW/hr,Business Type,Load Name']
    for elementDict in tree.values():
        if elementDict['object'] == 'load' and float(elementDict['kw'])>.1 and elementDict['name'] in loadsShed[0]:
            loadName = elementDict['name']
            avgLoad = float(elementDict['kw'])/2.5
            busType = 'residential'*(avgLoad<=10) + 'retail'*(avgLoad>10)*(avgLoad<=20) + 'agriculture'*(avgLoad>20)*(avgLoad<=39) + 'public'*(avgLoad>39)*(avgLoad<=50) + 'services'*(avgLoad>50)*(avgLoad<=100) + 'manufacturing'*(avgLoad>100)
            outDuration = 0
            for line in loadsShed:
                if loadName in line and outDuration <= maxDuration:
                    outDuration += timestep
            outDuration = int(outDuration)
            custInfo.append(f"{loadName},{outDuration},{season},{avgLoad},{busType},{loadName}")
    with open(outFile, 'w') as customerInfoFile:
        for line in custInfo:
            customerInfoFile.write(line)
            customerInfoFile.write('\n')

# buildCustomerInfo()