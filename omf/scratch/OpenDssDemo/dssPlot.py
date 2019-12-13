''' Run OpenDSS and plot the results for arbitrary circuits. '''

from argparse import ArgumentParser
import time
import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import math
import os, shutil

def runDSS(filename):
	''' Run DSS file and set export path.'''
	dss.run_command('set datapath=' + os.getcwd())
	dss.run_command('Redirect ' + filename)
	dss.run_command('Solve') # Ensure there is no seg fault for specialized plots.

def createRadii(coords):
	coords.columns = ['Element', 'X', 'Y']
	hyp = []
	for index, row in coords.iterrows():
		hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
	coords['radius'] = hyp
	return coords

def voltagePlots():
	''' Voltage plotting routine.'''
	base_coords = pd.read_csv('coords.csv', header=None)
	volt_coord = createRadii(base_coords)
	dss.run_command('Export voltages volts.csv') # Generate voltage plots.
	voltage = pd.read_csv('volts.csv') 
	volt_coord.columns = ['Bus', 'X', 'Y', 'radius']
	voltageDF = pd.merge(volt_coord, voltage, on='Bus') # Merge on the bus axis so that all data is in one frame.
	for i in range(1, 4): 
		volt_ind = ' pu' + str(i)
		mag_ind = ' Magnitude' + str(i)
		plt.scatter(voltageDF['radius'], voltageDF[volt_ind])
		plt.xlabel('Distance from source[miles]')
		plt.ylabel('Voltage [PU]')
		plt.title('Voltage profile for phase ' + str(i))
		plt.savefig('Pu Profile ' + str(i) + '.png') # A per unit plot.
		plt.clf()
		plt.scatter(voltageDF['radius'], voltageDF[mag_ind])
		plt.xlabel('Distance from source[miles]')
		plt.ylabel('Volt [V]')
		plt.axis([1, 7, 2000, 3000]) # Ignore sourcebus-much greater-for overall magnitude.
		plt.title('Voltage profile for phase ' + str(i))
		plt.savefig('Magnitude Profile ' + str(i) + '.png') # Actual voltages.
		plt.clf()
	plt.clf()

def currentPlots():
	''' Current plotting function.'''
	base_coords = pd.read_csv('coords.csv', header=None)
	curr_coord = createRadii(base_coords)
	dss.run_command('Export current currents.csv')
	current = pd.read_csv('currents.csv')
	curr_coord.columns = ['Index', 'X', 'Y', 'radius'] # DSS buses don't have current, but are connected to it. 
	curr_hyp = []
	currentDF = pd.concat([curr_coord, current], axis=1)
	for i in range(1, 3):
		for j in range(1, 4):
			cur_ind = ' I' + str(i) + '_' + str(j)
			plt.scatter(currentDF['radius'], currentDF[cur_ind])
			plt.xlabel('Distance from source [km]')
			plt.ylabel('Current [Amps]')
			plt.title('Current profile for ' + cur_ind)
			plt.savefig('Profile ' + str(i) +'.png')
			plt.clf()
	plt.clf()

def networkPlot():
	''' Plot the physical topology of the circuit. '''
	dss.run_command('Export voltages volts.csv')
	coords = pd.read_csv('coords.csv', header=None)
	volts = pd.read_csv('volts.csv')
	coords.columns = ['Bus', 'X', 'Y']
	print coords
	G = nx.Graph() # Declare networkx object.
	pos = {}
	# Get the coordinates.
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
	nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode) # We must seperate this to create a mappable object for colorbar.
	edges = nx.draw_networkx_edges(G, pos)
	nx.draw_networkx_labels(G, pos, labels) # We'll draw the labels seperately.
	plt.colorbar(nodes)
	plt.xlabel('Distance [m]')
	plt.title('Network Voltage Layout')
	plt.savefig('networkPlot.png')
	plt.clf()

def THD():
	''' Calculate and plot harmonics. '''
	base_coords = pd.read_csv('coords.csv', header=None)
	bus_coords = createRadii(base_coords)
	dss.run_command('Solve mode=harmonics')
	dss.run_command('Export voltages voltharmonics.csv')
	voltHarmonics = pd.read_csv('voltharmonics.csv')
	bus_coords.columns = ['Bus', 'X', 'Y', 'radius']
	voltHarmonics.columns.str.strip()
	for index, row in voltHarmonics.iterrows():
		voltHarmonics['THD'] = row[' Magnitude1']/(math.sqrt(row[' Magnitude2']**2 + row[' Magnitude3']**2))
	distortionDF = pd.merge(bus_coords, voltHarmonics, on='Bus') # Merge on the bus axis so that all data is in one frame.
	plt.scatter(distortionDF['radius'], distortionDF['THD'])
	plt.xlabel('Radius [m]')
	plt.ylabel('THD [Percentage]')
	plt.title('Total Harmonic Distortion')
	plt.savefig('THD.png')
	plt.clf()

def dynamicPlot(time_step, iterations):
	''' Do a dynamic, long-term study of the powerflow. time_step is in seconds. '''
	dss.run_command('Solve')
	dynamicCommand = 'Solve mode=dynamics stepsize=%d number=%d' % (time_step, iterations)
	dss.run_command(dynamicCommand)
	for i in range(iterations):
		voltString = 'Export voltages dynamicVolt%d.csv' % i
		currentString = 'Export currents dynamicCurrent%d.csv' % i
		dss.run_command(voltString)
		dss.run_command(currentString)
	powerData = []
	for j in range(iterations):
		curVolt = 'dynamicvolt%d.csv' % j
		curCurrent = 'dynamiccurrent%d.csv' % j
		voltProfile = pd.read_csv(curVolt)
		voltProfile.columns = voltProfile.columns.str.replace(' ', '')
		curProfile = pd.read_csv(curCurrent)
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
	plt.savefig('DynamicPowerPlot.png')
	os.system('rm dynamicvolt* dynamiccurrent*')


def faultPlot():
	''' Plot fault study. ''' 
	base_coords = pd.read_csv('coords.csv', header=None)
	bus_coord = createRadii(base_coords)
	dss.run_command('Solve Mode=FaultStudy')
	dss.run_command('Export fault faults.csv')
	faultData = pd.read_csv('faults.csv')
	bus_coord.columns = ['Bus', 'X', 'Y', 'radius'] # Add defined column names.
	faultDF = pd.concat([bus_coord, faultData], axis=1)
	faultDF.columns = faultDF.columns.str.strip()
	plt.scatter(faultDF['radius'], faultDF['3-Phase'])
	plt.xlabel('Distance [m]')
	plt.ylabel('Current [Amps]')
	plt.axis([-1, 6, 0, 8000])
	plt.savefig('3-Phase.png')
	plt.clf()
	plt.scatter(faultDF['radius'], faultDF['1-Phase'])
	plt.xlabel('Distance [m]')
	plt.ylabel('Current [Amps]')
	plt.savefig('1-phase.png')
	plt.axis([-1, 6, 0, 8000])
	plt.clf()
	plt.scatter(faultDF['radius'], faultDF['L-L'])
	plt.xlabel('Distance [m]')
	plt.ylabel('Current [Amps]')
	plt.axis([-1, 6, 0, 8000])
	plt.title('Fault Study')
	plt.savefig('L-L.png')
	plt.clf()

def capacityPlot():
	''' Plot power vs. distance '''
	# Generate radii(?)
	base_coords = pd.read_csv('coords.csv', header=None)
	coords = createRadii(base_coords)
	dss.run_command('Export Capacity capacity.csv')
	capacityData = pd.read_csv('capacity.csv')
	coords.columns = ['Index', 'X', 'Y', 'radius']
	capacityDF = pd.concat([coords, capacityData], axis=1)
	plt.scatter(capacityDF['radius'], capacityData[' kW'])
	plt.xlabel('Distance [m]')
	plt.ylabel('Power [kW]')
	plt.savefig('PowerLoad.png')
	plt.clf()
	plt.scatter(capacityDF['radius'], capacityData[' Imax'])
	plt.xlabel('Distance [m]')
	plt.ylabel('Current [Amps]')
	plt.savefig('CurrentLoad.png')
	plt.clf()
	plt.scatter(capacityDF['radius'], capacityDF.iloc[:, 2]+capacityDF.iloc[:, 3])
	plt.xlabel('Distance [m]')
	plt.ylabel('Maximum transformer percentage (One-side)')
	plt.title('Capacity Simulation')
	plt.savefig('CurrentLoad.png')
	plt.clf()

if __name__ == "__main__":
	# Files
	FNAME = 'ieee37.dss'
	# Make some output
	runDSS(FNAME)
	# Generate plots
	# voltagePlots()
	# currentPlots()
	networkPlot()
	# THD()
	# dynamicPlot(1, 10)
	# faultPlot()
	# capacityPlot()