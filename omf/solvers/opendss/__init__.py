''' Run OpenDSS and plot the results for arbitrary circuits. '''

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import math
import os
import warnings
try:
	import opendssdirect as dss
except:
	warnings.warn('opendssdirect not installed; opendss functionality disabled.')

def runDSS(dssFilePath):
	''' Run DSS file and set export path. '''
	# Get paths because openDss doesn't like relative paths.
	fullPath = os.path.abspath(dssFilePath)
	dssFileLoc = os.path.dirname(fullPath)
	dss.run_command('Clear')
	dss.run_command('Redirect ' + fullPath)
	dss.run_command('Solve')
	# also generate coordinates.
	x = dss.run_command('Export BusCoords ' + dssFileLoc + '/coords.csv')
	coords = pd.read_csv(dssFileLoc + '/coords.csv', header=None)
	coords.columns = ['Element', 'X', 'Y']
	hyp = []
	for index, row in coords.iterrows():
		hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
	coords['radius'] = hyp
	return coords

def voltagePlot(filePath, PU=True):
	''' Voltage plotting routine.'''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	volt_coord = runDSS(filePath)
	dss.run_command('Export voltages ' + dssFileLoc + '/volts.csv')
	# Generate voltage plots.
	voltage = pd.read_csv(dssFileLoc + '/volts.csv')
	volt_coord.columns = ['Bus', 'X', 'Y', 'radius']
	voltageDF = pd.merge(volt_coord, voltage, on='Bus') # Merge on the bus axis so that all data is in one frame.
	plt.title('Voltage Profile')
	plt.xlabel('Distance from source[miles]')
	if PU:
		for i in range(1, 4): 
			volt_ind = ' pu' + str(i)
			plt.scatter(voltageDF['radius'], voltageDF[volt_ind], label='Phase ' + str(i))
		plt.ylabel('Voltage [PU]')
		plt.legend()
		plt.savefig(dssFileLoc + '/Voltage Profile [PU].png')
	else:
		# plt.axis([1, 7, 2000, 3000]) # Ignore sourcebus-much greater-for overall magnitude.
		for i in range(1, 4): 
			mag_ind = ' Magnitude' + str(i)
			plt.scatter(voltageDF['radius'], voltageDF[mag_ind], label='Phase ' + str(i))
		plt.ylabel('Voltage [V]')
		plt.legend()
		plt.savefig(dssFileLoc + '/Voltage Profile [V].png')
	plt.clf()

def currentPlot(filePath):
	''' Current plotting function.'''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	curr_coord = runDSS(filePath)
	dss.run_command('Export currents ' + dssFileLoc + '/currents.csv')
	current = pd.read_csv(dssFileLoc + '/currents.csv')
	curr_coord.columns = ['Index', 'X', 'Y', 'radius'] # DSS buses don't have current, but are connected to it. 
	curr_hyp = []
	currentDF = pd.concat([curr_coord, current], axis=1)
	plt.xlabel('Distance from source [km]')
	plt.ylabel('Current [Amps]')
	plt.title('Current Profile')
	for i in range(1, 3):
		for j in range(1, 4):
			cur_ind = ' I' + str(i) + '_' + str(j)
			plt.scatter(currentDF['radius'], currentDF[cur_ind], label=cur_ind)
	plt.legend()
	plt.savefig(dssFileLoc + '/Current Profile.png')
	plt.clf()

def networkPlot(filePath):
	''' Plot the physical topology of the circuit. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	coords = runDSS(filePath)
	dss.run_command('Export voltages ' + dssFileLoc + '/volts.csv')
	volts = pd.read_csv(dssFileLoc + '/volts.csv')
	coords.columns = ['Bus', 'X', 'Y', 'radius']
	G = nx.Graph()
	# Get the coordinates.
	pos = {}
	for index, row in coords.iterrows():
		try:
			bus_name = str(int(row['Bus']))
		except:
			bus_name = row['Bus']
		G.add_node(bus_name)
		pos[bus_name] = (row['X'], row['Y'])
 	# Get the connecting edges using Pandas.
	lines = dss.utils.lines_to_dataframe()
	edges = []
	for index, row in lines.iterrows():
		#HACK: dss upercases everything in the outputs.
		bus1 = row['Bus1'][:4].upper().replace('.', '')
		bus2 = row['Bus2'][:4].upper().replace('.', '')
		edges.append((bus1, bus2))
	G.add_edges_from(edges)
	# We'll color the nodes according to voltage.
	volt_values = {}
	labels = {}
	for index, row in volts.iterrows():
		volt_values[row['Bus']] = row[' pu1']
		labels[row['Bus']] = row['Bus']
	colorCode = [volt_values.get(node, 0.0) for node in G.nodes()]
	# Start drawing.
	nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode)
	edges = nx.draw_networkx_edges(G, pos)
	nx.draw_networkx_labels(G, pos, labels, font_size=8)
	plt.colorbar(nodes)
	plt.xlabel('Distance [m]')
	plt.title('Network Voltage Layout')
	plt.savefig(dssFileLoc + '/networkPlot.png')
	plt.clf()

def THD(filePath):
	''' Calculate and plot total harmonic distortion. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	bus_coords = runDSS(filePath)
	dss.run_command('Solve mode=harmonics')
	dss.run_command('Export voltages ' + dssFileLoc + '/voltharmonics.csv')
	# Clean up temp file.
	try:
		base = os.path.basename(filePath)
		fnameMinusExt = os.path.splitext(base)[0]
		os.remove('{}_SavedVoltages.dbl'.format(fnameMinusExt))
	except:
		pass
	voltHarmonics = pd.read_csv(dssFileLoc + '/voltharmonics.csv')
	bus_coords.columns = ['Bus', 'X', 'Y', 'radius']
	voltHarmonics.columns.str.strip()
	for index, row in voltHarmonics.iterrows():
		voltHarmonics['THD'] = row[' Magnitude1']/(math.sqrt(row[' Magnitude2']**2 + row[' Magnitude3']**2))
	distortionDF = pd.merge(bus_coords, voltHarmonics, on='Bus') # Merge on the bus axis so that all data is in one frame.
	plt.scatter(distortionDF['radius'], distortionDF['THD'])
	plt.xlabel('Distance from Source [miles]')
	plt.ylabel('THD [Percentage]')
	plt.title('Total Harmonic Distortion')
	plt.savefig(dssFileLoc + '/THD.png')
	plt.clf()


def dynamicPlot(filePath, time_step, iterations):
	''' Do a dynamic, long-term study of the powerflow. time_step is in seconds. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))	
	runDSS(filePath)
	dss.run_command('Solve')
	dynamicCommand = 'Solve mode=dynamics stepsize=%d number=%d' % (time_step, iterations)
	dss.run_command(dynamicCommand)
	for i in range(iterations):
		voltString = 'Export voltages ' + dssFileLoc + '/dynamicVolt%d.csv' % i
		currentString = 'Export currents ' + dssFileLoc + '/dynamicCurrent%d.csv' % i
		dss.run_command(voltString)
		dss.run_command(currentString)
	powerData = []
	for j in range(iterations):
		curVolt = 'dynamicvolt%d.csv' % j
		curCurrent = 'dynamiccurrent%d.csv' % j
		voltProfile = pd.read_csv(dssFileLoc + '/' + curVolt)
		voltProfile.columns = voltProfile.columns.str.replace(' ', '')
		curProfile = pd.read_csv(dssFileLoc + '/' + curCurrent)
		curProfile.columns = curProfile.columns.str.replace(' ', '')
		sourceVoltage = voltProfile.loc[voltProfile['Bus'] == 'SOURCEBUS']
		sourceCurrent = curProfile.loc[curProfile['Element'] == 'Vsource.SOURCE']
		data_summary = {'Volts': (sourceVoltage['Magnitude1'], sourceVoltage['Magnitude2'], sourceVoltage['Magnitude3']), 
		'Currents': (sourceCurrent['I1_1'], sourceCurrent['I1_2'], sourceCurrent['I1_3'])}
		power_triplet = (data_summary['Volts'][0]*data_summary['Currents'][0], data_summary['Volts'][1]*data_summary['Currents'][1], data_summary['Volts'][2]*data_summary['Currents'][2])
		powerData.append(power_triplet)
	first_phase = [item[0] for item in powerData]
	second_phase = [item[1] for item in powerData]
	third_phase = [item[2] for item in powerData]
	plt.plot(first_phase, label='Phase one')
	plt.plot(second_phase, label='Phase two')
	plt.plot(third_phase, label='Phase three')
	plt.legend()
	plt.xlim(0, iterations-1)
	plt.xlabel('Time [s]')
	plt.ylabel('Power [kW]')
	plt.title('Dynamic Simulation Power Plot')
	plt.savefig(dssFileLoc + '/DynamicPowerPlot.png')
	os.system('rm ' + dssFileLoc + '/dynamicvolt* ' + dssFileLoc + '/dynamiccurrent*')


def faultPlot(filePath):
	''' Plot fault study. ''' 
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	bus_coord = runDSS(filePath)
	dss.run_command('Solve Mode=FaultStudy')
	dss.run_command('Export fault ' + dssFileLoc + '/faults.csv')
	faultData = pd.read_csv(dssFileLoc + '/faults.csv')
	bus_coord.columns = ['Bus', 'X', 'Y', 'radius']
	faultDF = pd.concat([bus_coord, faultData], axis=1)
	faultDF.columns = faultDF.columns.str.strip()
	plt.axis([-1, 6, 0, 8000])
	plt.xlabel('Distance From Source [Miles]')
	plt.ylabel('Current [Amps]')
	plt.title('Fault Study')
	plt.scatter(faultDF['radius'], faultDF['3-Phase'], label='3-Phase to Ground')
	plt.scatter(faultDF['radius'], faultDF['1-Phase'], label='1-Phase to Ground')
	plt.scatter(faultDF['radius'], faultDF['L-L'], label='Line-to-Line')
	plt.legend()
	plt.savefig(dssFileLoc + '/Fault Currents.png')
	plt.clf()

def capacityPlot(filePath):
	''' Plot power vs. distance '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	coords = runDSS(filePath)
	dss.run_command('Export Capacity ' + dssFileLoc + '/capacity.csv')
	capacityData = pd.read_csv(dssFileLoc + '/capacity.csv')
	coords.columns = ['Index', 'X', 'Y', 'radius']
	capacityDF = pd.concat([coords, capacityData], axis=1)
	fig, ax1 = plt.subplots()
	ax1.set_xlabel('Distance From Source [Miles]')
	ax1.set_ylabel('Power [kW]')
	ax1.scatter(capacityDF['radius'], capacityData[' kW'], label='Power')
	ax2 = ax1.twinx()
	ax2.set_ylabel('Maximum transformer percentage (One-side)')
	ax2.scatter(capacityDF['radius'], capacityDF.iloc[:, 2]+capacityDF.iloc[:, 3], label='Transformer Loading', color='red')
	fig.tight_layout() # otherwise the right y-label is slightly clipped
	fig.legend()
	plt.savefig(dssFileLoc + '/Capacity Profile.png')
	plt.clf()

if __name__ == "__main__":
	# Make core output
	FPATH = 'ieee37_ours.dss'
	# Just run DSS
	# runDSS(FPATH)
	# Generate plots, note output is in FPATH dir.
	# voltagePlot(FPATH)
	# currentPlot(FPATH)
	networkPlot(FPATH)
	# THD(FPATH)
	# dynamicPlot(FPATH, 1, 10)
	# faultPlot(FPATH)
	# capacityPlot(FPATH)