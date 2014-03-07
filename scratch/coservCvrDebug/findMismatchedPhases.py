
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

def breakDown(lnk):
	return lnk["fromnode"], lnk["tonode"], lnk["ldata"]

def twoOutta3(lnk):
	# We know that at least one object is mismatched.
	# If one object is different from the other two, it returns that
	# But if all three are different, it implicitly returns None
	a, b, c = breakDown(lnk)
	if phasEq(a, b):
		return c
	elif phasEq(a, c):
		return b
	elif phasEq(b, c):
		return a

def invalidPhaseNum(lnk):
	# returns True if any of the objects have invalid phase numbers, like 26N, 17N, XXX, etc.
	# implicitly returns None otherwise
	# However, this would not catch something like ABABN, but I don't think there are any like that anyway
	for k, gridobj in lnk.items():
		for char in gridobj["phases"].strip('"'):
			if char not in "ABCN":
				return True

def fltr(pred):
	return len(filter(pred, problemlinks))

def dictcopy(d):
	newd = {}
	for k, v in d.items():
		newd[k] = v
	return newd

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

print len(problemlinks), "node-link-node configs with AT LEAST one phase mismatch"
print
print len(filter(twoOutta3, problemlinks)), "node-link-node configs with EXACTLY one phase mismatch"
print
print len(filter(invalidPhaseNum, problemlinks)), "node-link-node configs with AT LEAST one invalid phase number"
print
print len(filter(lambda x: twoOutta3(x) and invalidPhaseNum(x), problemlinks)), "node-link-node configs with EXACTLY one phase mismatch and AT LEAST one invalid phase number"

print
xxx = filter(lambda x: not twoOutta3(x) and not invalidPhaseNum(x), problemlinks)
print len(xxx), "more than one mismatch, no invalid phase numbers"
print
# print len(filter(lambda x: not twoOutta3(x) and not invalidPhaseNum(x), problemlinks))
notInvalid = filter(lambda x: not invalidPhaseNum(x), problemlinks)
print len(notInvalid), "at least one mismatch, no invalid phase numbers"
print
whatevs = filter(lambda x: twoOutta3(x) and not invalidPhaseNum(x), problemlinks)
print len(whatevs), "exactly one mismatch, no invalid phase numbers"
print
lineneut = filter(lambda x: x["ldata"]["phases"] == "N", notInvalid)
print len(lineneut), "at least one mismatch, no invalid phase numbers, line object just has N phase"
print
nodeneut= filter(lambda x: x["fromnode"]["phases"] == "N" or x["tonode"]["phases"] == "N", problemlinks)
print len(nodeneut), "configs where a node just has N"

def is_invalid(phasenum):
	for e in phasenum.strip('"'):
		if e not in "ABCN":
			return 1
	return 0

def exactlyOneInvalid(lnk):
	i = 0
	for e in breakDown(lnk):
		i += is_invalid(e["phases"])
	return i == 1

def oneIsSuperset(lnk):
	a,b,c = breakDown(lnk)
	m = max(a,b,c, key=lambda x: len(x["phases"].strip('"')))["phases"].strip('"')
	for obj in [a,b,c]:
		for c in obj["phases"].strip('"'):
			if c not in m:
				return False
	return True


# One Mismatch One Invalid
omov = filter(lambda x: exactlyOneInvalid(x) and twoOutta3(x), problemlinks)
print len(omov), "exactly one mismatch and exactly one invalid.  Logical deduction: the invalid phase is the mismatch"

# Mismatch but one object's phases are a superset of the other two's
mmbss = filter(oneIsSuperset, problemlinks)
print
print len(mmbss), "mismatched, but one object is a superset of the others"
