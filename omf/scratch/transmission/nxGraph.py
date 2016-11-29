import datetime, copy, os, re, warnings, networkx as nx, json
from os.path import join as pJoin
from matplotlib import pyplot as plt

G = nx.Graph()
G.add_node(1)
G.add_node(3)
G.add_edge(1,3)
G.add_edge(5,6)
for key in G:
	print key