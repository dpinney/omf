# I think this folder needs to be outside of the omf directory or it will be part of the dependency graph?
# requires graphviz from http://www.graphviz.org/ (not a python module)
python py2depgraph.py path/to/omf | python depgraph2dot.py | dot -T png -o depgraph.png
