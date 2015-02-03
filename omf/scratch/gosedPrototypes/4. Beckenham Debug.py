import json, sys, os
sys.path.append('../..')
import feeder
from solvers import gridlabd

with open('../../data/Feeder/admin/Olin Beckenham Calibrated.json','r') as inJson:
	myFeeder = json.load(inJson)
	tree = myFeeder['tree']

# Up the power.
for key in tree:
	if 'power_rating' in tree[key]:
		myPow = float(tree[key]['power_rating'])
		# if myPow < 100: myPow = 100
		tree[key]['power_rating'] = myPow*1000
		for x in ['powerA_rating', 'powerB_rating', 'powerC_rating']:
			if x in tree[key]: tree[key][x] = myPow*1000

def runBeckGridlab():
	try:
		os.remove('./beckDebuggery')
	except:
		pass
	os.mkdir('./beckDebuggery')
	rawOut = gridlabd.runInFilesystem(tree,
			attachments=myFeeder.get('attachments',{}), keepFiles=True,
			workDir='./beckDebuggery', glmName=None)

runBeckGridlab()