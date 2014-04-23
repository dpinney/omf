
import re

omf = open("omf.py").read().split("\n")
web = open("web.py").read()

for i in range(len(omf)):
	occ = re.findall("def [A-Za-z0-9_]*", omf[i])	# I seem to remember that [A-z] is different from [A-Za-z]... perhaps I'm wrong, though
	if occ and web.find(occ[0]) == -1:
		print i, occ[0]
		
