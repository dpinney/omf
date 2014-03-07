from omf import feeder
from helperfuncs import *

if "parsedFeeder" not in globals():
	# Parsing the feeder takes a long time, so I don't want to do it every time I modify and re-run this script
	print "parsing RectorAlphaPhases.glm"
	parsedFeeder = feeder.parse("RectorAlphaPhases.glm")


newtree = {}
print "Parsing done, converting dict"
for guid, t in parsedFeeder.items():
	treeObj = dictcopy(t)
	if treeObj.get("name") and treeObj.get("phases"):
		treeObj["id"] = guid
		newtree[treeObj["name"]] = treeObj
print "Done"

links = {k:v for k, v in newtree.items() if v.get("from") and v.get("to")}

problemlinks = []
print "Finding problem links"
for lname, ldata in links.items():
	fromnode = newtree[ldata["from"]]
	tonode = newtree[ldata["to"]]
	if gp(ldata) != gp(fromnode) or gp(ldata) != gp(tonode):
		problemlinks.append({
			"fromnode":fromnode,
			"ldata":ldata,
			"tonode":tonode
			})
