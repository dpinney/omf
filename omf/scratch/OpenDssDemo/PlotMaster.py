''' Run OpenDSS and plot the results for arbitrary circuits. '''

from time import time
import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import math
import os, shutil

def runDSS(filename):  
	''' Run DSS file and set export path.'''
	homeDir = os.getcwd() # OpenDSS saves plots in a temp file unless you redirect explicitly.
	dss.run_command('Redirect ' + filename)
	dss.run_command('set datapath=' + str(homeDir))
	dss.run_command('Export BusCoords coords.csv') # Get the bus coordinates.
	
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

def voltagePlots(filename):
	''' Voltage plotting routine.'''
	runDSS(filename)
	dss.run_command('Export voltages volts.csv') # Generate voltage plots.
	voltage = pd.read_csv('volts.csv') 
	volt_coord_cols = ['Bus', 'X', 'Y'] # Add defined column names.
	volt_coord = pd.read_csv('coords.csv', names=volt_coord_cols)
	volt_hyp = []
	for index, row in volt_coord.iterrows(): 
		volt_hyp.append(math.sqrt(row['X']**2 + row['Y']**2)) # Get total distance for each entry.
	volt_coord['radius'] = volt_hyp
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

def currentPlots(filename):
	''' Current plotting function.'''
	runDSS(filename) # This routine mirrors the voltage plots.
	dss.run_command('Export current currents.csv')
	current = pd.read_csv('currents.csv')
	curr_coord_cols = ['Index', 'X', 'Y'] # DSS buses don't have current, but are connected to it. 
	curr_coord = pd.read_csv('coords.csv', names=curr_coord_cols)
	curr_hyp = []
	for index, row in curr_coord.iterrows():
		curr_hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
	curr_coord['radius'] = curr_hyp
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

def networkPlot(filename):
	''' Plot the physical topology of the circuit. '''
	runDSS(filename)
	dss.run_command('Export voltages volts.csv')
	volts = pd.read_csv('volts.csv')
	coord = pd.read_csv('coords.csv', names=['Bus', 'X', 'Y'])

	G = nx.Graph() # Declare networkx object.
	pos = {}

	for index, row in coord.iterrows(): # Get the coordinates.
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
	packagePlots('networkPlots')

if __name__ == "__main__":
	start = time()
	filename = 'ieee37.dss'
	voltagePlots(filename)
	currentPlots(filename)
	networkPlot(filename)
	print("--- %s seconds ---" % (time() - start)) # Check performace.