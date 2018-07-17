import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import math
import os

def runDSS(filename):  # Initial file run.
	homeDir = os.getcwd() # OpenDSS saves plots in a temp file unless you redirect explicitly.
	dss.run_command('Redirect ' + filename)
	dss.run_command('set datapath=' + str(homeDir))
	dss.run_command('Export BusCoords coords.csv') # Get the bus coordinates.

def voltagePlots(filename):
	runDSS(filename)
	dss.run_command('Export voltages volts.csv') # Generate voltage plots.
	voltage = pd.read_csv('volts.csv') 
	volt_coord_cols = ['Bus', 'X', 'Y'] # Add defined column names.
	volt_coord = pd.read_csv('coords.csv', names=volt_coord_cols)
	volt_hyp = []
	for index, row in volt_coord.iterrows(): 
		volt_hyp.append(math.sqrt(row['X']**2 + row['Y']**2)) # Get total distance for each entry.
	volt_coord['radius'] = volt_hyp
	voltageDF = pd.merge(volt_coord, voltage, on='Bus')
	for i in range(1, 4): 
		volt_ind = ' pu' + str(i)
		plt.scatter(voltageDF['radius'], voltageDF[volt_ind])
		plt.xlabel('RADIUS')
		plt.ylabel('VOLTS')
		plt.title('FOR ' + volt_ind)
		plt.show()

def currentPlots(filename):
	runDSS(filename)
	dss.run_command('Export current currents.csv')
	current = pd.read_csv('currents.csv')
	curr_coord_cols = ['Index', 'X', 'Y']
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
			plt.xlabel('RADIUS')
			plt.ylabel('CURRENT')
			plt.title('FOR ' +  cur_ind)
			plt.show()


def networkPlot(filename):
	runDSS(filename)
	dss.run_command('Export voltages volts.csv')
	volts = pd.read_csv('volts.csv')
	print volts
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
	for index, row in volts.iterrows(): # We'll color the nodes according to voltage. FIX: pu1?
		if row['Bus'] == '799R':
			row['Bus'] = '799r'
		if row['Bus'] == 'SOURCEBUS':
			row['Bus'] = 'SourceBus'
		volt_values[row['Bus']] = row[' pu1']


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
	plt.colorbar(nodes)
	plt.show()

if __name__ == "__main__":
	filename = 'ieee37.dss'
	#voltagePlots(filename)
	#currentPlots(filename)
	networkPlot(filename)