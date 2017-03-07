import omf

def psuedomizeNames():
	newNameKey = {}
	for key in feeder.tree:
		oldName = feeder.tree[key]['name']
		newName = feeder.tree[key]['object'] + 'randInt'
		newNameKey.update({ oldName : newName })
		feeder.tree[key]['name'] = newName

	pass


def randomizeNames():
	for key in feeder.tree:
		newName = 'randName'
		feeder.tree[key]['name'] = newName

	pass


def translateLocations(translation,rotation):
	for key in feeder.nodes:
		newX = feeder.nodes[key]['x'] + translation
		newY = feeder.nodes[key]['y'] + translation
		feeder.nodes[key]['x'] = newX
		feeder.nodes[key]['px'] = newX
		feeder.nodes[key]['y'] = newY
		feeder.nodes[key]['py'] = newY

	pass


def randomizeLocation():
	for key in feeder.nodes:
		feeder.nodes[key]['x'] = 'randInt'
		feeder.nodes[key]['px'] = 'randInt'
		feeder.nodes[key]['y'] = 'randInt'
		feeder.nodes[key]['py'] = 'randInt'


	pass


def combineLoads():
	pass


def modifyConductorLengths():
	pass


def smoothLoads():
	pass


def shuffleLoads(percent):
	for key in feeder.tree:
		if randint(0,100) <= percent:
			feeder.tree[key]


	pass


def addNoise(percent):	
	for key in feeder.tree:
		if feeder.tree[key].startswith():
			feeder.tree[key][''] = 

	pass