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

def packagePlots(dirname):
	''' Move all png files to individual folder. Ensure that the working folder is free of png files beforehand.'''
	# Stream all plots to their own folders to avoid cluttering the workspace. 
	os.chdir(os.getcwd())
	if not os.path.isdir(dirname):
		os.mkdir(dirname)
	files = os.listdir(os.getcwd())
	sourcePath = os.getcwd()
	destPath = os.getcwd() + '/' + str(dirname)
	for file in files: # Each plotting function calls this function individually, so it is relatively safe to move all png files. 
		if file.endswith('.png'):
			shutil.move(os.path.join(sourcePath,file), os.path.join(destPath, file))

def createRadii(coords):
	coords.columns = ['Element', 'X', 'Y']
	hyp = []
	for index, row in coords.iterrows():
		hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
	coords['radius'] = hyp
	return coords


def voltagePlots(volt_coord):
	''' Voltage plotting routine.'''
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
	packagePlots('voltagePlots')
	#volt_coord.drop('radius', 1)

def currentPlots(curr_coord):
	''' Current plotting function.'''
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
	packagePlots('currentPlots')

def networkPlot(coords):
	''' Plot the physical topology of the circuit. '''
	dss.run_command('Export voltages volts.csv')
	volts = pd.read_csv('volts.csv')
	coords.columns = ['Bus', 'X', 'Y', 'radius']
	G = nx.Graph() # Declare networkx object.
	pos = {}
	for index, row in coords.iterrows(): # Get the coordinates.
 		if row['Bus'] == '799R':
			row['Bus'] = '799r'
		if row['Bus'] == 'SOURCEBUS':
			row['Bus'] = 'SourceBus'
		G.add_node(row['Bus'])
		pos[row['Bus']] = (row['X'], row['Y'])

	volt_values = {}
	labels = {}
	for index, row in volts.iterrows(): # We'll color the nodes according to voltage. FIX: pu1?
		if row['Bus'] == '799R':
			row['Bus'] = '799r'
		if row['Bus'] == 'SOURCEBUS':
			row['Bus'] = 'SourceBus'
		volt_values[row['Bus']] = row[' pu1']
		labels[row['Bus']] = row['Bus']


	colorCode = [volt_values[node] for node in G.nodes()]

	lines = dss.utils.lines_to_dataframe() # Get the connecting edges using Pandas.
	edges = []
	for index, row in lines.iterrows(): # For 799R, you need four charactesr. The others all have a period at the end, so splice that.
		bus1 = row['Bus1'][:4].replace('.', '')
		bus2 = row['Bus2'][:4].replace('.', '')
		edges.append((bus1, bus2))
	G.add_edges_from(edges)

	nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode) # We must seperate this to create a mappable object for colorbar.
	edges = nx.draw_networkx_edges(G, pos)
	nx.draw_networkx_labels(G, pos, labels) # We'll draw the labels seperately.
	plt.colorbar(nodes)
	plt.xlabel('Distance [m]')
	plt.title('Network Voltage Layout')
	plt.savefig('networkPlot.png')
	plt.clf()
	packagePlots('networkPlots')


def THD(bus_coords):
	''' Calculate and plot harmonics. '''
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
	plt.savefig('THD.png')
	plt.clf()
	packagePlots('THD')


def dynamicPlot():
	''' Do a dynamic, long-term study of the powerflow. '''
	dss.run_command('Solve')
	dss.run_command('New monitor ')
	dss.run_command('Solve mode=dynamics number=1 stepsize=.2')
	dss.run_command('Export Summary sum.csv')
	dss.run_command('Solve number=200')
	dss.run_command('Export Powers new_powers.csv')
	powers = pd.read_csv('powers.csv')
	powers.columns = powers.columns.str.strip()
	loads = powers.loc[powers['Element'].str.contains('Load')]
	individual_loads = loads['Element']
	individual_watts = loads['P(kW)']
	plt.figure(figsize=(10, 8))
	plt.xticks(rotation='vertical')
	plt.ylabel('Power [kW]')
	plt.bar(individual_loads, individual_watts)
	plt.savefig('Dynamic.png')
	plt.clf()
	packagePlots('DynamicPlots')


def faultPlot(bus_coord):
	''' Plot fault study. ''' 
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
	plt.savefig('L-L.png')
	plt.clf()
	packagePlots('FaultPlots')

def capacityPlot(coords):
	''' Plot power vs. distance '''
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
	plt.savefig('CurrentLoad.png')
	plt.clf()
	packagePlots('capacityPlots')

if __name__ == "__main__":
	start = time.time()
	parser = ArgumentParser(description='Plotting options for DSS files.')
	parser.add_argument("-f", "--file", required=True, help="DSS file.")
	parser.add_argument("-c", "--coordinates", help="Optional coordinates argument")
	args = vars(parser.parse_args())
	filename = args['file']
	base_coords = None
	if args['coordinates']:
		coordFile = args['coordinates']
		base_coords = pd.read_csv(coordFile, header=None)
	else:
		try:
			dss.run_command('Export BusCoords coords.csv')
			base_coords = pd.read_csv('coords.csv', header=None)
		except OSError as e:
			if e.errno == errno.EEXIST:
				print "Error: coodinate file not created properly. Perhaps you need to set your OpenDSS data path correctly?"
			else:
				raise Exception('Could not read file')
	runDSS(filename)
	full_coords = createRadii(base_coords)
	#voltagePlots(full_coords) 
	#currentPlots(full_coords)
	#networkPlot(full_coords)
	dynamicPlot()
	#faultPlot(full_coords)
	#capacityPlot(full_coords)
	#THD(full_coords)
	print("--- %s seconds ---" % (time.time() - start)) # Check performace.
