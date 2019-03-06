from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
import networkx as nx
import pandas as pd
import random

def xfrange(start, stop, step):
	i = 0
	while start + i * step < step:
		yield start + i * step
		i += 1

def generateGraphs():
	df = pd.DataFrame({ 'from':['A', 'B', 'C','A'], 'to':['D', 'A', 'E','C']})
	G = nx.from_pandas_dataframe(df, 'from', 'to')
	with PdfPages('plots.pdf') as pdf:
		curGraph = nx.draw(G, node_shape='d', with_labels=True, alpha=.5, edge_color='green', font_color='white', font_weight='bold', style='dotted')
		pdf.savefig(curGraph)
		newGraph = nx.draw(G, node_shape='o', with_labels=True, alpha=.5, edge_color='green', font_color='white', font_weight='bold', style='dotted')
		pdf.savefig(newGraph)

if __name__ == "__main__":
	testGraph = generateGraphs()



