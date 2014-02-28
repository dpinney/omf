
from omf import feeder

# Using these switches instead of functions because I want access to pretty much
# all the vars below at the interpreter.
parseNewGuy = True
getLinks = True
getpblinks = True

def gp(obj):
	# gp for get phases
	objStr = obj["phases"].strip('"')
	return objStr[:-1] if objStr[-1] == "N" else objStr

if parseNewGuy:
	print "parsing RectorAlphaPhases.glm"
	p = feeder.parse("RectorAlphaPhases.glm")
	newtree = {}
	print "Parsing done, converting dict"
	for guid, treeObj in p.items():
		if treeObj.get("name") and treeObj.get("phases"):
			treeObj["id"] = guid
			newtree[treeObj["name"]] = treeObj
	print "Done"

if getLinks:
	links = {k:v for k, v in newtree.items() if v.get("from") and v.get("to")}

if getpblinks:
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

	print len(problemlinks), "problemlinks"
	print "found all the problem links!  use printProbLinks if there's not too many!"

def prLnkRng(upper=len(problemlinks), lower=0, probLinks=problemlinks):
	# upper before lower is a little unintuitive...
	for i in range(lower, upper):
		if i < len(probLinks):
			printOneLink(probLinks[i])
		else:
			print "All links have been printed"
			return

def printOneLink(l):
	fromnode, ldata, tonode = l["fromnode"], l["ldata"], l["tonode"]
	print "phase mismatch at", ldata["object"], ldata["name"],":"
	print "linkobj:\n", ldata
	print "tonode:\n", tonode
	print "fromnode:\n",fromnode, "\n\n"

def printProbLinks(probLinks):
	for l in probLinks:
		printOneLink(l)
	print "that's all of em!"

