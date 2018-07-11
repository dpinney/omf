import opendssdirect as dss
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


dss.run_command('Redirect ieee37.dss') # Load files.
volts = pd.read_csv('volts.csv')
bus_coord = pd.read_csv('IEEE37_BusXY.csv', names=['Bus', 'X', 'Y'])

G = nx.Graph() # Declare networkx object.
pos = {}

for index, row in bus_coord.iterrows(): # Get the coordinates.
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

