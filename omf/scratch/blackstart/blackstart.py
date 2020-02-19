import networkx as nx
import matplotlib as mpl
from matplotlib import pyplot as plt
import pandapower as pp
import numpy as np
from random import randint, sample
mpl.rcParams['figure.dpi'] = 300 #FYI, anything over 100 makes this slow.
net = pp.create_empty_network()

# generate the graph from pairs of connected nodes.
incidence = [[0,1],[1,3],[1,4],[2,3],[3,6],[3,4],[4,5],[4,6],[6,7]]
bidir_inc = incidence + [[x[1],x[0]] for x in incidence]
g = nx.DiGraph(bidir_inc)

bus0 = pp.create_bus(net, vn_kv=110.)
bus1 = pp.create_bus(net, vn_kv=110.)
bus2 = pp.create_bus(net, vn_kv=110.)
bus3 = pp.create_bus(net, vn_kv=110.)
bus4 = pp.create_bus(net, vn_kv=110.)
bus5 = pp.create_bus(net, vn_kv=110.)
bus6 = pp.create_bus(net, vn_kv=110.)
bus7 = pp.create_bus(net, vn_kv=110.)

pp.create_line(net, bus0, bus1, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus1, bus3, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus1, bus4, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus2, bus3, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus3, bus6, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus3, bus4, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus4, bus5, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus4, bus6, length_km=70., std_type='149-AL1/24-ST1A 110.0')
pp.create_line(net, bus6, bus7, length_km=70., std_type='149-AL1/24-ST1A 110.0')

# Add load and gen and color by capability to self-support.
def constrained_sum_sample_pos(n, total):
    """
    Return a randomly chosen list of n positive integers sum to total.
    Each such list is equally likely to occur.
    """
    dividers = sorted(sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]
# Generate nicely balanced loads and gens.
nodeCount = len(g.nodes())
load_amounts = constrained_sum_sample_pos(nodeCount, 20)
gen_amounts = [x for x in constrained_sum_sample_pos(nodeCount, 20)]
# Put the loads and gens on the graph.
for n_i in g.nodes():
    g.node[n_i]['load'] = load_amounts[n_i]
    g.node[n_i]['gen'] = gen_amounts[n_i]
    g.node[n_i]['demand'] = load_amounts[n_i] - gen_amounts[n_i]
    if g.node[n_i]['demand'] <= 0:
        g.node[n_i]['color'] = 'lightgreen'
    else:
        g.node[n_i]['color'] = 'lightgray'
demands = [g.node[x]['demand'] for x in g.node]
print(demands, sum(demands))

# Make labels and colors
ugly_labels = {x:'G{gen}\nL{load}'.format(**g.node[x]) for x in g.node}
def get_colors():
    return [g.node[x]['color'] for x in g.node]

# Drawing.
plt.figure(figsize=(10,5))
gpos = nx.layout.spring_layout(g)
nx.draw(g, gpos, node_color=get_colors(), alph=0.7)
nx.draw_networkx_labels(g, gpos, labels=ugly_labels, font_size=7, font_color='black');
plt.show()

# Add a neighbor to an already energized (neighbor)hood.
def energize_hood_neighbor(good_hood, prints=False):
    hood_demand = sum([g.node[x]['demand'] for x in good_hood])
    flatten = lambda x:[item for sublist in x for item in sublist]
    mega_hood = flatten([g.neighbors(n_i) for n_i in good_hood])
    all_hood_nbs = list(set(mega_hood) - set(good_hood))
    first_nb = g.node[all_hood_nbs[0]]
    if first_nb['demand'] < abs(hood_demand):
        if prints:
            print('ENERGIZABLE!')
            print(good_hood, first_nb, hood_demand)
        return good_hood + [all_hood_nbs[0]]
    else:
        return good_hood
h1 = energize_hood_neighbor([4], prints=True)
h2 = energize_hood_neighbor(h1, prints=True)
h3 = energize_hood_neighbor(h2, prints=True)

plt.close()
# Hacking restoration.
plt.figure(figsize=(20,20))
opts={'with_labels':False, 'node_size':20}
def red_coloring(hood):
    c = get_colors()
    for n_i in hood:
        c[n_i] = 'red'
    return c
largest_hdi = 0
best = [0]
for j in range(7):
    hdi = [j]
    generator = [j]
    for i in range(7):
        hdi = energize_hood_neighbor(hdi)
    if largest_hdi < len(hdi):
        largest_hdi = len(hdi)
        best = generator
for i in range(7):
    plt.subplot(331 + i)
    plt.title(i)
    nx.draw(g, gpos, node_color=red_coloring(best), alph=0.7)
    best = energize_hood_neighbor(best)
print(best)
plt.show()

# Calculate a valid network flow.
nx.network_simplex(g)

plt.close()
# Graph with edge width determined by simplex flow
flowCost, flowDict = nx.network_simplex(g)
G = nx.Graph()
widths = []
for u in flowDict:
    for v in flowDict[u]:
        if flowDict[u][v] != 0:
            G.add_edge(u, v)
            widths.append(flowDict[u][v])
plt.figure(figsize=(10,5))
gpos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, gpos, node_size=700)
nx.draw_networkx_edges(G, gpos, width=widths)
plt.show()