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

def tingytang():
	print "tingytangXXXX"