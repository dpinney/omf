# I think this folder needs to be outside of the omf directory or it will be part of the dependency graph?
python py2depgraph.py path/to/omf | python depgraph2dot.py | dot -T png -o depgraph.png
