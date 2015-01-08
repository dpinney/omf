''' Working towards a timeTravel chart. '''
import omf, json, os, math, networkx as nx
from matplotlib import pyplot as plt
from omf.solvers.gridlabd import runInFilesystem

def main():
	''' JSON manipulation, Gridlab running, etc. goes here. '''
	feedJson = json.load(open('./ABEC Frank Calibrated.json'))
	tree = feedJson['tree']
	# Add recorders here.
	stub = {'object':'group_recorder', 'group':'"class=node"', 'property':'voltage_A', 'interval':3600, 'file':'aVoltDump.csv'}
	for phase in ['A','B','C']:
		copyStub = dict(stub)
		copyStub['property'] = 'voltage_' + phase
		copyStub['file'] = phase.lower() + 'VoltDump.csv'
		tree[omf.feeder.getMaxKey(tree) + 1] = copyStub
	# Run gridlab.
	allOutputData = runInFilesystem(tree, attachments=feedJson['attachments'], keepFiles=True, workDir=".", glmName='ABEC Frank SolverGen.glm')
	try: os.remove('PID.txt')
	except: pass
	print 'Gridlab ran correctly', allOutputData.keys()
	'''-----------------------------
	--VOLTAGE PLOTTING STARTS HERE--
	-----------------------------'''
	# Calculate average node voltage deviation. First, helper functions.
	def pythag(x,y):
		''' For right triangle with sides x and y, return the hypotenuse. '''
		return math.sqrt(x**2+y**2)
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		return sum(l)/len(l)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Do all time steps.
	allNodeNames = [x for x in allOutputData['aVoltDump.csv'].keys() if x != '# timestamp']
	allTimeSteps = allOutputData['aVoltDump.csv']['# timestamp']
	# for step, stamp in enumerate(allTimeSteps):
	step, stamp = (0, '2011-01-01 00:00:00 PST')
	# TODO: REMOVE ME
	nodeVolts = {}
	for nodeName in allNodeNames:
		allVolts = []
		for phase in ['A','B','C']:
			v = complex(allOutputData[phase.lower() + 'VoltDump.csv'][nodeName][step])
			phaseVolt = pythag(v.real, v.imag)
			if phaseVolt != 0.0:
				if digits(phaseVolt)>3:
					# Normalize to 120 V standard
					phaseVolt = phaseVolt*(120/feedVoltage)
				allVolts.append(phaseVolt)
		# HACK: Take average of all phases to collapse dimensionality.
		nodeVolts[nodeName] = avg(allVolts)
	_plotOneTimeStep(nodeVolts, step, tree)

def _plotOneTimeStep(nodeVolts, stepName, tree, neatoLayout=True):
	''' It's like voltageDrop.py but parameterized on the nodeVolts.
		Watch out, it saves a png directly to the file system. '''
	# Color nodes by VOLTAGE.
	fGraph = omf.feeder.treeToNxGraph(tree)
	voltChart = plt.figure(figsize=(10,10))
	plt.axes(frameon = 0)
	plt.axis('off')
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = nx.graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
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
	voltChart.savefig("./pngs/volts" + str(stepName) + ".png")

if __name__ == '__main__':
	main()
	pass