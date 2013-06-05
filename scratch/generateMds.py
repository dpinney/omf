#!/usr/bin/env python

import os
import json
import sys
sys.path.append(os.path.abspath('../'))
import feeder

def slurp(fileName):
	with open(fileName,'r') as openFile:
		return openFile.read()

os.chdir('../data/')


# anaNames = [x[0:-5] for x in os.listdir('Analysis') if not x.endswith('.md.json')]

# print 'AnalysisNames', anaNames

# for ana in anaNames:
# 	reports = [x for x in os.listdir('Study'+'/'+ana+'/reports')]
# 	reportData = [json.loads(slurp('Study'+'/'+ana+'/reports/'+x)) for x in reports]
# 	studyNames = [x for x in os.listdir('Study'+'/'+ana+'/studies')]
# 	print ana,reportData,studyNames
# 	with open('Analysis/' + ana + '.json','w') as anaFile:
# 		json.dump({'reports':reports,'studyNames':studyNames},anaFile)

# for ana in anas:
# 	with open(ana[0:-8] + '.json', 'w') as openFile:
# 		openFile.write('{}')

# for ana in anas:
# 	with open(ana + '/metadata.json') as orig:
# 		js = orig.read()
# 	with open(ana + '.md.json', 'w') as mdFile:
# 		mdFile.write(js)

# for ana in anas:
# 	os.remove(ana + '/metadata.json')

# anaStudies = [x for x in os.listdir('Study') if not x.endswith('.json')]

# for ana in anaStudies:
# 	studies = [x for x in os.listdir('Study/' + ana + '/studies')]
# 	outputs = [os.path.isfile('Study/' + ana + '/studies/' + x + '/cleanOutput.json') for x in studies]
# 	inputs = [os.path.isfile('Study/' + ana + '/studies/' + x + '/cleanOutput.json') for x in studies]
# 	print ana, studies, outputs, inputs
# 	if False in outputs or False in inputs: print 'WE ARE MISSING SOME DATA!'
# 	for study in studies:
# 		studyDir = 'Study/' + ana + '/studies/' + study
# 		try:
# 			with open(studyDir + '/main.json','r') as feederFile:
# 				rawInput = json.load(feederFile)
# 		except:
# 			rawInput = {'nodes':[],'hiddenNodes':[],'links':[],'hiddenLinks':[],'layoutVars':{'theta':'0.8','gravity':'0.1','friction':'0.9','linkStrength':'2'}}
# 		with open(studyDir + '/cleanOutput.json','r') as mdFile:
# 			outputJson = json.load(mdFile)
# 		try:
# 			glmTree = feeder.parse(studyDir + '/main.glm')
# 		except:
# 			pass
# 		attachments = {fileName:slurp(studyDir + '/' + fileName) for fileName in os.listdir(studyDir) if fileName != 'main.glm' and not fileName.endswith('json')}
# 		rawInput['attachments'] = attachments
# 		rawInput['tree'] = glmTree
# 		# with open('Study/' + ana + '/studies/' + study + '/metadata.json','r') as mdFile:
# 		# 	mdJson = mdFile.read()
# 		# print os.path.isfile('Study/' + ana + '/studies/' + study + '/cleanOutput.json')
# 		# with open('Study/' + ana + '---' + study + '.md.json','w') as studyMdFile:
# 		# 	studyMdFile.write(mdJson)
# 		# 	os.remove('Study/' + ana + '/studies/' + study + '/metadata.json')
# 		output = {'inputJson':rawInput,'outputJson':outputJson}
# 		with open('Study/' + ana + '---' + study + '.json','w') as studyFile:
# 			json.dump(output, studyFile, indent=4)