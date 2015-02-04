''' Working towards a timeTravel chart. '''
import omf, json, os, math, networkx as nx, gc
from matplotlib import pyplot as plt
from omf.solvers.gridlabd import runInFilesystem
from omf import feeder

def main():
	''' JSON manipulation, Gridlab running, etc. goes here. '''
	# Import data.
	feedJson = json.load(open('./ABEC Frank Calibrated.json'))
	tree = feedJson['tree']
	# Input data, model-style.
	inputDict = {'simLength':24,'simStartDate':'2011-01-01', 'simLengthUnits':'hours'}
	# Add recorders.
	stub = {'object':'group_recorder', 'group':'"class=node"', 'property':'voltage_A', 'interval':3600, 'file':'aVoltDump.csv'}
	for phase in ['A','B','C']:
		copyStub = dict(stub)
		copyStub['property'] = 'voltage_' + phase
		copyStub['file'] = phase.lower() + 'VoltDump.csv'
		tree[omf.feeder.getMaxKey(tree) + 1] = copyStub
	feeder.adjustTime(tree, inputDict['simLength'], inputDict['simLengthUnits'], inputDict['simStartDate'])
	# Run gridlab.
	allOutputData = runInFilesystem(tree, attachments=feedJson['attachments'], keepFiles=True, workDir='.', glmName='ABEC Frank SolverGen.glm')
	try: os.remove('PID.txt')
	except: pass
	print 'Gridlab ran correctly', allOutputData.keys()
	# Make plots.
	#TODO: figure out what to do about neato taking like 2 minutes to run.
	neatoLayout = True
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Make a graph object.
	fGraph = omf.feeder.treeToNxGraph(tree)
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = nx.graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	# Plot all time steps.
	for step, stamp in enumerate(allOutputData['aVoltDump.csv']['# timestamp']):
		# Build voltage map.
		nodeVolts = {}
		for nodeName in [x for x in allOutputData['aVoltDump.csv'].keys() if x != '# timestamp']:
			allVolts = []
			for phase in ['A','B','C']:
				v = complex(allOutputData[phase.lower() + 'VoltDump.csv'][nodeName][step])
				phaseVolt = _pythag(v.real, v.imag)
				if phaseVolt != 0.0:
					if _digits(phaseVolt)>3:
						# Normalize to 120 V standard
						phaseVolt = phaseVolt*(120/feedVoltage)
					allVolts.append(phaseVolt)
			# HACK: Take average of all phases to collapse dimensionality.
			nodeVolts[nodeName] = _avg(allVolts)
		# Apply voltage map and chart it.
		voltChart = plt.figure(figsize=(10,10))
		plt.axes(frameon = 0)
		plt.axis('off')
		edgeIm = nx.draw_networkx_edges(fGraph, positions)
		nodeIm = nx.draw_networkx_nodes(fGraph,
			pos = positions,
			node_color = [nodeVolts.get(n,0) for n in fGraph.nodes()],
			linewidths = 0,
			node_size = 30,
			cmap = plt.cm.jet)
		plt.sci(nodeIm)
		plt.clim(110,130)
		plt.colorbar()
		plt.title(stamp)
		voltChart.savefig('./pngs/volts' + str(step).zfill(3) + '.png')
		# Reclaim memory by closing, deleting and garbage collecting the last chart.
		voltChart.clf()
		plt.close()
		del voltChart
		gc.collect()

def _pythag(x,y):
	''' For right triangle with sides x and y, return the length of the hypotenuse. '''
	return math.sqrt(x**2+y**2)

def _digits(x):
	''' Returns number of digits before the decimal in the float x. '''
	return math.ceil(math.log10(x+1))

def _avg(l):
	''' Average of a list of ints or floats. '''
	return sum(l)/len(l)

if __name__ == '__main__':
	main()