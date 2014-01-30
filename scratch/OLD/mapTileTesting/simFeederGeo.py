import json, random, os

d = '../../data/Feeder/'
fileNameList = os.walk(d).next()[2]

with open('feeders.json', 'w+') as fh:
	data = {}
	for i in fileNameList:
		fJson = json.load(open(d+i, 'r'))
		default = None
		data[i] = {'name':i.strip('.json'),'coordinates':[random.uniform(-124,-66), random.uniform(24,49)], 'size':len(fJson['tree']), 
		'layoutVars':fJson.get('layoutVars', default), 'attachments': fJson.get('attachments',default)}
	fh.write(json.dumps(data, indent = 4))
