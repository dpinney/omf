
from omf import feeder

def gp(obj):
	# gp for get phases
	objStr = obj["phases"].strip('"')
	return objStr[:-1] if objStr[-1] == "N" else objStr

def prLnkRng(lower, upper, probLinks):
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

def phasEq(n1, n2):
	return n1["phases"] == n2["phases"]

def twoOutta3(lnk):
	# We know that at least one object is mismatched.
	# If one object is different from the other two, it returns that
	# But if all three are different, it implicitly returns None
	a, b, c = lnk["fromnode"], lnk["tonode"], lnk["ldata"]
	if phasEq(a, b):
		return c
	elif phasEq(a, c):
		return b
	elif phasEq(b, c):
		return a

# Using these switches instead of functions because I want access to pretty much
# all the vars below at the interpreter, but I want the option not to execute 
# certain if blocks.  feeder.parse takes a long time and I don't need to do it
# each time I make a tiny change to this script.
parseNewGuy = False
getLinks = True
getpblinks = True

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

