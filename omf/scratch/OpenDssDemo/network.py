import opendssdirect as dss
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


dss.run_command('Redirect ieee37.dss')
volts = pd.read_csv('volts.csv')
bus_coord = pd.read_csv('IEEE37_BusXY.csv', names=['Bus', 'X', 'Y'])
G = nx.Graph()

pos = {}

for index, row in bus_coord.iterrows():
	G.add_node(row['Bus'])
	pos[row['Bus']] = (row['X'], row['Y'])


volt_values = {}
for index, row in volts.iterrows():
	if row['Bus'] == '799R':
		row['Bus'] = '799r'
	if row['Bus'] == 'SOURCEBUS':
		row['Bus'] = 'SourceBus'
	volt_values[row['Bus']] = row[' pu1']


colorCode = [volt_values[node] for node in G.nodes()]

lines = dss.utils.lines_to_dataframe()
edges = []
for index, row in lines.iterrows():
	bus1 = row['Bus1'][:4].replace('.', '')
	bus2 = row['Bus2'][:4].replace('.', '')
	edges.append((bus1, bus2))
G.add_edges_from(edges)


layout = nx.draw_networkx(G, pos, node_color=colorCode)
#plt.colorbar(layout)
plt.show()

