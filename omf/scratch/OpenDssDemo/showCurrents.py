import opendssdirect as dss
import pandas as pd

import opendssdirect as dss
import networkx as nx
import matplotlib.pyplot as plt
import pip


def calculateGraph(df, phase=1):
	graph = nx.Graph()
	data = df[['Bus1', 'Bus2']].to_dict(orient="index")
	for key in data:
		voltage_line = data[key]
		graph.add_edge(voltage_line["Bus1"].split(".")[0], voltage_line["Bus2"].split(".")[0])
	positions = {}
	i = 0
	for name in dss.Circuit.AllBusNames():
		dss.Circuit.SetActiveBus(name)
		current = dss.Circuit.YCurrents()[i]
		distance = dss.Bus.Distance()
		positions[dss.Bus.Name()] = (distance, current)
		i += 2
	return graph, positions

def plotGraph():
	lines = dss.utils.lines_to_dataframe()
	graph, position = calculateGraph(lines)
	fig, ax = plt.subplots(1, 1, figsize=(16, 10))
	nx.draw_networkx_nodes(graph, position, labels={x: x for x in graph.nodes()})
	nx.draw_networkx_nodes(graph, position, labels={x: x for x in graph.nodes()})
	nx.draw_networkx_nodes(graph, position, labels={x: x for x in graph.nodes()})
	ax.set_xlabel('Distances [km]')
	ax.set_ylabel('Current [P.u]')
	ax.set_title('Current PROFILE')
	plt.show()

if __name__ == "__main__":
	dss.run_command("Redirect ./short_circuit.dss")
	dss.run_command('Solve')
	plotGraph()
	#dss.run_command('Show curr')
