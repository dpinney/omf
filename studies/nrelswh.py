#!/usr/bin/env python

with open('./studies/nrelswh.html','r') as configFile: configHtmlTemplate = configFile.read()

def create(analysisName, studyName):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyConfig['studyName']
	# make the study folder:
	os.mkdir(studyPath)
	# copy over tmy2 and replace the dummy climate.tmy2.
	shutil.copyfile('tmy2s/' + studyConfig['tmy2name'], studyPath + '/climate.tmy2')
	# write all the other variables:
	with open(studyPath + '/samInput.json','w') as samInputFile:
		json.dump(studyConfig, samInputFile)
	# add the metadata:
	md = {'climate':str(studyConfig['tmy2name']), 'studyType':str(studyConfig['studyType'])}
	with open(studyPath + '/metadata.json','w') as mdFile:
		json.dump(md, mdFile)
	return

def run(analysisName, studyName):
	pass