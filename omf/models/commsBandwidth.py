''' Comms Bandwidth Model '''

import json, os, sys, tempfile, datetime, shutil, tempfile, networkx as nx
from os.path import join as pJoin
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf import comms

# Model metadata:
tooltip = "Calculate the bandwidth requirements for a communications system on a feeder"
modelName, template = metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	outData = {}
	#feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	#inputDict['feederName1'] = feederName
	feederName = inputDict['feederName1']
	shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'static', 'publicFeeders', feederName+'.omd'), pJoin(modelDir, feederName+'.omd'))
	feederPath = pJoin(modelDir,feederName+'.omd')
	feeder = comms.createGraph(feederPath)
	comms.setFiber(feeder, edgeType='switch', rfBandwidthCap=int(inputDict['rfCapacity']), fiberBandwidthCap=int(inputDict['fiberCapacity']))
	comms.setRf(feeder, packetSize=int(inputDict['meterPacket']))
	comms.calcBandwidth(feeder)
	comms.saveOmc(comms.graphGeoJson(feeder), modelDir, feederName)

	#bandwidth capacity
	overloadedFiber = []
	for edge in nx.get_edge_attributes(feeder, 'fiber'):
		if feeder[edge[0]][edge[1]]['bandwidthUse'] > feeder[edge[0]][edge[1]]['bandwidthCapacity']:
			overloadedFiber.append(edge)

	overloadedCollectors = []
	for rfCollector in nx.get_node_attributes(feeder, 'rfCollector'):
		if feeder.node[rfCollector]['bandwidthUse'] > feeder.node[rfCollector]['bandwidthCapacity']:
			overloadedCollectors.append(rfCollector)

	outData['overloadedFiber'] = overloadedFiber
	outData['overloadedCollectors'] = overloadedCollectors
	if len(overloadedFiber) == 0:
		outData['fiberStatus'] = 'passed'
	else:
		outData['fiberStatus'] = 'insufficient'
	if len(overloadedCollectors) == 0:
		outData['collectorStatus'] = 'passed'
	else:
		outData['collectorStatus'] = 'insufficient'

	#cost calculations

	outData['fiber_cost'] = comms.getFiberCost(feeder, float(inputDict.get('fiber_cost', 0)))
	outData['rf_collector_cost'] = comms.getrfCollectorsCost(feeder, float(inputDict.get('rf_collector_cost', 0)))
	outData['smart_meter_cost'] = comms.getsmartMetersCost(feeder, float(inputDict.get('smart_meter_cost', 0)))

	outData['total_cost'] = outData['fiber_cost'] + outData['rf_collector_cost'] + outData['smart_meter_cost']

	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"fiberCapacity": 10**6,
		"rfCapacity": 10**3*5,
		"meterPacket": 10,
		"feederName1":"Olin Barre LatLon",
		"fiber_cost": 3,
		"rf_collector_cost": 30000,
		"smart_meter_cost": 1000,
		"created":str(datetime.datetime.now())
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'static', 'publicFeeders', defaultInputs['feederName1']+'.omd'), pJoin(modelDir, defaultInputs['feederName1']+'.omd'))
	except:
		return False
	return creationCode

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()