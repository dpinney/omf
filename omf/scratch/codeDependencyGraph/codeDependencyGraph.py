#!/usr/bin/env python
'''
Create a picture of the dependencies in the OMF.
Pre-requisite: snakefood (pip install snakefood), and graphviz (apt-get install graphviz)
'''

import os

# Paths to the directories.
pDir = os.path.dirname
thisDir = pDir(__file__)
omfDir = pDir(pDir(thisDir))

# Filenames.
graphName = thisDir + '/omfDepGraph.dot'
psName = thisDir + '/omfDepGraph.ps'

# Create a graphviz dotfile representation of the dependency graph.
# If you want to see 3rd party dependencies, remove the "--internal" flag.
os.system('sfood --internal {} | sfood-graph > {}'.format(omfDir, graphName))

# Make a postscript drawing of the graph.
os.system('dot -Tps {} -o {}'.format(graphName, psName))